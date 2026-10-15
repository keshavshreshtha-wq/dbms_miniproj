import sqlite3
import pandas as pd

def initialize_database():
    df = pd.read_csv('navcore_heatwave_synthetic_data.csv')
    
    conn = sqlite3.connect('navcore_heatwave.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Weather_Stations (
        station_id TEXT PRIMARY KEY,
        station_type TEXT,
        region TEXT
    )''')

    # ADDED: stakeholder_target column
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
    
    # ADDED: stakeholder_target to the dataframe selection
    observations = df[['observation_id', 'timestamp', 'station_id', 'recorded_temp_c', 
                       'forecast_temp_c', 'is_heatwave_event', 'heatwave_severity', 
                       'alert_status', 'advisory_category', 'stakeholder_target']]
    observations.to_sql('Observations', conn, if_exists='replace', index=False)

    cursor.execute('DROP VIEW IF EXISTS Region_Summary')
    cursor.execute('''
    CREATE VIEW Region_Summary AS
    SELECT 
        w.region, 
        MAX(o.recorded_temp_c) as max_temp, 
        COUNT(o.observation_id) as total_alerts
    FROM Observations o
    JOIN Weather_Stations w ON o.station_id = w.station_id
    WHERE o.alert_status IN ('Warning', 'Danger')
    GROUP BY w.region
    ''')

    conn.commit()
    conn.close()
    print("✅ Database rebuilt with stakeholder roles included.")

if __name__ == "__main__":
    initialize_database()