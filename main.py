from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import sqlite3
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

app = FastAPI(title="Navcore Heatwave API")

# Enable CORS for external access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_db():
    """Auto-generates dataset and builds SQLite database on server startup"""
    csv_file = 'navcore_heatwave_synthetic_data.csv'
    
    # 1. Generate fallback dataset if CSV is missing on server
    if not os.path.exists(csv_file):
        start_date = datetime(2026, 5, 1)
        rows = []
        regions = ['Mumbai', 'Pune', 'Nagpur', 'Nashik', 'Aurangabad']
        for i in range(500):
            temp = round(float(np.random.normal(38, 4)), 1)
            rows.append({
                'observation_id': f"OBS-{10000 + i}",
                'timestamp': (start_date + timedelta(hours=i)).isoformat(),
                'station_id': f"STN-{np.random.randint(100, 150)}",
                'station_type': np.random.choice(['IMD', 'AWS']),
                'region': np.random.choice(regions),
                'recorded_temp_c': temp,
                'forecast_temp_c': round(temp + float(np.random.uniform(-1, 1)), 1),
                'is_heatwave_event': temp >= 40.0,
                'heatwave_severity': 'Severe' if temp >= 40 else 'Normal',
                'alert_status': 'Danger' if temp >= 40 else 'Clear',
                'advisory_category': 'Medical Emergency' if temp >= 40 else 'None',
                'stakeholder_target': np.random.choice(['Public Dashboard User', 'Disaster Management Officer', 'Meteorologist', 'Admin'])
            })
        df = pd.DataFrame(rows)
        df.to_csv(csv_file, index=False)
    else:
        df = pd.read_csv(csv_file)

    # 2. Build database and views
    conn = sqlite3.connect('navcore_heatwave.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Weather_Stations (
        station_id TEXT PRIMARY KEY,
        station_type TEXT,
        region TEXT
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Observations (
        observation_id TEXT PRIMARY KEY,
        timestamp TEXT,
        station_id TEXT,
        recorded_temp_c REAL,
        forecast_temp_c REAL,
        is_heatwave_event BOOLEAN,
        heatwave_severity TEXT,
        alert_status TEXT,
        advisory_category TEXT,
        stakeholder_target TEXT,
        FOREIGN KEY (station_id) REFERENCES Weather_Stations(station_id)
    )''')

    stations = df[['station_id', 'station_type', 'region']].drop_duplicates()
    stations.to_sql('Weather_Stations', conn, if_exists='replace', index=False)

    obs_cols = ['observation_id', 'timestamp', 'station_id', 'recorded_temp_c', 
                'forecast_temp_c', 'is_heatwave_event', 'heatwave_severity', 
                'alert_status', 'advisory_category', 'stakeholder_target']
    
    available_cols = [c for c in obs_cols if c in df.columns]
    df[available_cols].to_sql('Observations', conn, if_exists='replace', index=False)

    cursor.execute('DROP VIEW IF EXISTS Region_Summary')
    cursor.execute('''
    CREATE VIEW Region_Summary AS
    SELECT 
        w.region, 
        MAX(o.recorded_temp_c) as max_temp, 
        COUNT(o.observation_id) as total_alerts
    FROM Observations o
    JOIN Weather_Stations w ON o.station_id = w.station_id
    WHERE o.recorded_temp_c >= 37.0
    GROUP BY w.region
    ''')

    conn.commit()
    conn.close()

# Lifecycle Event: Automatically setup DB before serving API requests
@app.on_event("startup")
def startup_event():
    init_db()

def get_db_connection():
    conn = sqlite3.connect('navcore_heatwave.db')
    conn.row_factory = sqlite3.Row
    return conn

# API Endpoints
@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

@app.get("/api/summary")
def get_region_summary():
    conn = get_db_connection()
    data = conn.execute('SELECT * FROM Region_Summary').fetchall()
    conn.close()
    return [dict(row) for row in data]

@app.get("/api/hotspots")
def get_hotspots():
    conn = get_db_connection()
    data = conn.execute('''
        SELECT o.timestamp, w.region, w.station_type, o.recorded_temp_c, o.alert_status, o.advisory_category
        FROM Observations o
        JOIN Weather_Stations w ON o.station_id = w.station_id
        WHERE o.recorded_temp_c >= 40.0
        ORDER BY o.timestamp DESC
        LIMIT 10
    ''').fetchall()
    conn.close()
    return [dict(row) for row in data]

@app.get("/api/alerts/{stakeholder}")
def get_stakeholder_alerts(stakeholder: str):
    conn = get_db_connection()
    target = stakeholder.replace("_", " ")
    data = conn.execute('''
        SELECT o.timestamp, w.region, o.recorded_temp_c, o.forecast_temp_c, o.alert_status, o.advisory_category, o.stakeholder_target
        FROM Observations o
        JOIN Weather_Stations w ON o.station_id = w.station_id
        WHERE o.stakeholder_target = ? OR ? = 'Admin'
        ORDER BY o.timestamp DESC
        LIMIT 15
    ''', (target, target)).fetchall()
    conn.close()
    return [dict(row) for row in data]
