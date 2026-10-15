import pandas as pd
import requests
import numpy as np
import time

def fetch_real_climate_data():
    print("Connecting to Open-Meteo Historical API...")
    
    # Coordinates for real Maharashtra cities
    cities = [
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "station": "STN-MUM"},
        {"name": "Pune", "lat": 18.5204, "lon": 73.8567, "station": "STN-PUN"},
        {"name": "Nagpur", "lat": 21.1458, "lon": 79.0882, "station": "STN-NAG"},
        {"name": "Nashik", "lat": 20.0059, "lon": 73.7629, "station": "STN-NSK"},
        {"name": "Aurangabad", "lat": 19.8762, "lon": 75.3433, "station": "STN-AUR"}
    ]
    
    all_data = []
    
    # Fetch historical data for May 2024 (Peak Indian Summer)
    for city in cities:
        print(f"Fetching real historical data for {city['name']}...")
        url = (
            f"https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={city['lat']}&longitude={city['lon']}&"
            f"start_date=2024-05-01&end_date=2024-05-31&"
            f"hourly=temperature_2m&timezone=Asia%2FCalcutta"
        )
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            # Format the incoming data into a Pandas DataFrame
            df = pd.DataFrame({
                "timestamp": data["hourly"]["time"],
                "recorded_temp_c": data["hourly"]["temperature_2m"]
            })
            
            # Add metadata
            df["region"] = city["name"]
            df["latitude"] = city["lat"]
            df["longitude"] = city["lon"]
            df["station_id"] = city["station"]
            df["station_type"] = np.random.choice(["IMD", "AWS"], len(df))
            
            all_data.append(df)
        time.sleep(1) # Be polite to the free API
        
    # Combine all city datasets
    final_df = pd.concat(all_data, ignore_index=True)
    
    # Drop any null values from the API
    final_df = final_df.dropna(subset=["recorded_temp_c"])
    
    # Generate schema columns based on real temperature readings
    num_rows = len(final_df)
    final_df['observation_id'] = [f"OBS-{10000 + i}" for i in range(num_rows)]
    
    # Simulate forecast by adding a small margin of error (-1 to +1 degrees) to actuals
    final_df['forecast_temp_c'] = (final_df['recorded_temp_c'] + np.random.uniform(-1, 1, num_rows)).round(1)
    
    # Define IMD Heatwave logic dynamically based on real temperatures
    final_df['is_heatwave_event'] = final_df['recorded_temp_c'] >= 40.0
    
    conditions = [
        (final_df['recorded_temp_c'] >= 42.0),
        (final_df['recorded_temp_c'] >= 40.0),
        (final_df['recorded_temp_c'] >= 37.0)
    ]
    
    final_df['heatwave_severity'] = np.select(conditions, ['Extreme', 'Severe', 'Moderate'], default='Normal')
    final_df['alert_status'] = np.select(conditions, ['Danger', 'Warning', 'Watch'], default='Clear')
    final_df['advisory_category'] = np.select(conditions, ['Medical Emergency', 'Stay Indoors', 'Hydration'], default='None')
    
    # Distribute Stakeholders
    final_df['stakeholder_target'] = np.random.choice(
        ['Public Dashboard User', 'Disaster Management Officer', 'Meteorologist', 'AI Analyst'], 
        num_rows
    )

    # Export to the EXACT filename your setup_db.py script uses
    output_filename = "navcore_heatwave_synthetic_data.csv"
    final_df.to_csv(output_filename, index=False)
    print(f"✅ Downloaded {num_rows} real weather records and saved to {output_filename}")

if __name__ == "__main__":
    fetch_real_climate_data()