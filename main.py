from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import sqlite3

app = FastAPI(title="Navcore Heatwave API")

# Allow all origins for frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    conn = sqlite3.connect('navcore_heatwave.db')
    conn.row_factory = sqlite3.Row
    return conn

# Root route to serve the command center UI
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
