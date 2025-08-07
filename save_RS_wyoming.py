# -*- coding: utf-8 -*-
"""
Created on Mon Dec 5 18:12:20 2022

@author: zadavi
"""
from datetime import date
from calendar import monthrange
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def save_RS_wyoming(start_year: int, end_year: int, start_month: int, end_month: int, station_id: str = "11035", hours: list = [0, 12]):
    # Downloading radiosonde data from the University of Wyoming and saves as text files
    # RS*.txt & latitude and longitude in a CSV file.

    #  Input parameters:
    # -----------------------------------------
    #  start_year: Starting year (e.g., 2024).
    #  end_year: Ending year (inclusive).
    #  start_month: Starting month (1-12).
    #  end_month: Ending month (1-12).
    #  station_id: Weather station ID (default: "11035" for Wien/Hohe Warte).
    #  hours: Hours to fetch (default: [0, 12]).
    #  CRD_csv: Path for station cordinate CSV (default: RS{station_id}.csv).
 
    #  Example:
    # -----------------------------------------
    # save_RS_wyoming(2024, 2024, 7, 8)

    CRD_csv = f"RS{station_id}.csv"
    
    CRD = []

    for year in range(start_year, end_year + 1):
        for month in range(start_month, end_month):
            daym = monthrange(year, month)[1]
            directory = f"RS{station_id}/{year}/{month:02d}"
            os.makedirs(directory, exist_ok=True)

            for day in range(1, daym + 1):
                doy = date(year, month, day).timetuple().tm_yday

                for hour in hours:
                    try:
                        url = (
                            f"http://weather.uwyo.edu/wsgi/sounding?datetime={year}-{month:02d}-{day:02d}%20{hour:02d}:00:00"
                            f"&id={station_id}&src=UNKNOWN&type=TEXT:LIST"
                        )
                        response = requests.get(url, timeout=10)
                        if response.status_code != 200:
                            print(f"No data for {year}-{month:02d}-{day:02d} {hour:02d}:00")
                            continue

                        soup = BeautifulSoup(response.text, "html.parser")
                        pre_tag = soup.find("pre")
                        if not pre_tag:
                            print(f"No data for {year}-{month:02d}-{day:02d} {hour:02d}:00")
                            continue

                       
                        if not CRD:
                            text_lines = soup.get_text().split('\n')
                            lat = lon = None
                            for line in text_lines:
                                
                                match = re.search(r'Latitude:\s*([-]?\d+\.?\d*)\s*Longitude:\s*([-]?\d+\.?\d*)', line)
                                if match:
                                    try:
                                        lat = float(match.group(1))
                                        lon = float(match.group(2))
                                    except ValueError:
                                        print("Couldn’t read coordinates")
                                        continue
                                    break
                            if lat is not None and lon is not None:
                                CRD.append({'Station_ID': station_id, 'Latitude': lat, 'Longitude': lon})

                        # Extract data table
                        lines = pre_tag.get_text().split('\n')
                        table_data = []
                        data_start = False
                        for line in lines:
                            if "PRES   HGHT   TEMP   DWPT   RELH" in line:
                                data_start = True
                                table_data.append(line)
                                continue
                            if data_start and line.strip() and not line.startswith('---'):
                                table_data.append(line)

                        if len(table_data) < 2:
                            print(f"No usable  data for {year}-{month:02d}-{day:02d} {hour:02d}:00")
                            continue

                       
                        filename = f"RS{station_id}{str(year)[2:4]}{doy:03d}{hour:02d}.txt"
                        with open(os.path.join(directory, filename), 'w', encoding='utf-8') as f:
                            f.write('\n'.join(table_data))

                    except Exception as e:
                        print(f"Error for {year}-{month:02d}-{day:02d} {hour:02d}:00: {e}")
                        continue

    
    if CRD:
        pd.DataFrame(CRD).to_csv(CRD_csv, index=False)
        print(f"Lat & Lon saved to {CRD_csv}")
    else:
        print("Couldn’t find any coordinates")
        
############################### EXAMPLE########################################
if __name__ == "__main__":
    # Example: July 2024
    save_RS_wyoming(2024, 2024, 7, 8)