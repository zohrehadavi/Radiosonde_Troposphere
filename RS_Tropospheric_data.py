# -*- coding: utf-8 -*-
"""
Created on Fri Jan 20 10:03:30 2023

@author: zadavi
"""
from datetime import date
from calendar import monthrange
import os
import pandas as pd
import numpy as np
import math

def RS_Tropospheric_Parameters(start_year: int, end_year: int, start_month: int, end_month: int, station_id: str = "11035", hours: list = [0, 12], file_out: str = "RS_TRP.csv") -> None:
    # Calculating the Tropospheric Parameters from RS data
    # Result in a CSV file.

    #  Input parameters:
    # -----------------------------------------
    #  start_year: Starting year (e.g., 2024).
    #  end_year: Ending year (inclusive).
    #  start_month: Starting month (1-12).
    #  end_month: Ending month (1-12).
    #  station_id: Weather station ID (default: "11035" for Wien/Hohe Warte).
    #  hours: Hours to fetch (default: [0, 12]).
    #  file_out : Path for TRP file (default: RS_TRP.csv).
 
    #  Example:
    # -----------------------------------------
    # RS_Tropospheric_Parameters(2024, 2024, 7, 8)
    
    # -------------------------Constants-------------------------------
    Md  = 28.9644;       # [kg/kmol]
    Mw  = 18.01528;      # [kg/kmol]
    g0  = 9.80665;       # Gravity acceleration [m/s²]
    # -----------------Refractivity coefficients------------------------
    k1  = 77.689;        # [K/hPa]
    k2  = 71.295;        # [K/hPa]
    k3  = 375463;        # [K^2/hPa]
    data_list = []


    CRD_csv = f"RS{station_id}.csv"
    CRD = pd.read_csv(CRD_csv)
    lat = CRD['Latitude'].iloc[0] 
    lon = CRD['Longitude'].iloc[0]

    for year in range(start_year, end_year + 1):

        for month in range(start_month, end_month):
            daym = monthrange(year, month)[1]
            directory = f"RS{station_id}/{year}/{month:02d}"

            if not os.path.exists(directory):
                print(f"No data directory {directory}")
                continue

            for day in range(1, daym):
                doy = date(year, month, day).timetuple().tm_yday

                for hour in hours:
                    filename = f"RS{station_id}{str(year)[2:4]}{doy:03d}{hour:02d}.txt"
                    filepath = os.path.join(directory, filename)
                    
                    filenw = f"NW{str(year)[2:4]}{doy:03d}{hour:02d}.txt"
                    file_NW= os.path.join(directory, filenw)
                    
                    file_out_trp=os.path.join(directory, file_out)

                    if not os.path.exists(filepath):
                        continue

                    try:
                        
                        with open(filepath, 'r', encoding='utf-8') as f:
                            lines = f.readlines()

                        data_lines = []
                        data_start = False
                        for line in lines:
                            if "PRES" in line and "HGHT" in line:
                                data_start = True
                                continue
                            if data_start:
                                parts = line.strip().split()
                                if len(parts) == 11:
                                    try:
                                        data_lines.append([float(val) if val != 'NaN' else np.nan for val in parts])
                                    except ValueError:
                                        continue  

                        if not data_lines:
                            print(f"No valid data in {filename}")
                            continue

                        df = pd.DataFrame(data_lines, columns=['PRES', 'HGHT', 'TEMP', 'DWPT', 'RELH', 'MIXR', 'DRCT', 'SPED', 'THTA', 'THTE', 'THTV'])

                        df = df.dropna(subset=['PRES', 'TEMP', 'DWPT', 'HGHT'])

                        if df.empty:
                            print(f"No usable data in {filename}")
                            continue

                        


                        nan_c = df[['HGHT','PRES','TEMP','RELH']].isnull().sum(axis=1)
                        remove_ind = df[nan_c >= 2].index

                        # 
                        df_new = df.drop(remove_ind)
                        

                        H = df_new['HGHT'].values
                        temp = df_new['TEMP'].values #[°^C]
                        tdw = df_new['DWPT'].values  #[°^C]
                        RH = df_new['RELH'].values   #[%]
                        P = df_new['PRES'].values    #[hPa]
                        T_k = temp + 273.15
                        rh=RH/100
                        h=H[0]
                        
                        ew = np.zeros_like(temp)
                        
                        
                        # water (T >= 0°C)
                        mask_water = temp >= 0
                        ew[mask_water] = 6.112 * np.exp((17.67 * temp[mask_water]) / (temp[mask_water] + 243.5))

                        # ice (T < 0°C)
                        mask_ice = temp < 0
                        ew[mask_ice] = 6.112 * np.exp((21.85 * temp[mask_ice]) / (temp[mask_ice] + 265.5))
                        

                        ###PWV
                        pw=rh*ew
                        
                        q=(0.622*pw)/(P-(0.378*pw))
                        mean_q = (q[:-1] + q[1:]) / 2
                        
                        delta_p=  np.abs(np.diff(P))*100
                            
                        gs=g0*(1-0.00266*np.cos(2*(math.radians(lat)))-(2.8e-7)*H[0])
                        
                        PWV=np.sum((mean_q * delta_p) / (gs))
                        
                        
                        ### Refractivity
                        
                        P_d = P - pw
                        Nh = k1 * P_d / T_k
                        Nw = k2*pw/(T_k)+k3*(pw/(T_k)**2);
                        N=Nh+Nw
                        
                        ### ZTD
                        dh = np.abs(np.diff(H))
                        mean_Nh=(Nh[:-1] + Nh[1:]) / 2
                        mean_Nw=(Nw[:-1] + Nw[1:]) / 2
                        
                        ZHD=np.sum(mean_Nh * dh)* 1e-6
                        ZWD=np.sum(mean_Nw * dh)* 1e-6
                        
                        ZHD_top=0.002277*(P[-1]+((1255/T_k[-1])+0.05)*pw[-1]) #Topmot Layer value
                        ZTD=ZHD+ZWD+ZHD_top
                        
                        

                        data_list.append({
                            'Year': year,
                            'DoY': doy,
                            'Time': hour,
                            'Lat': lat,
                            'Lon': lon,
                            'H': h,
                            'PWV': PWV,
                            'ZWD': ZWD,
                            'ZTD': ZTD,
                        })
                        
                        pd.DataFrame(Nw).to_csv(file_NW,header=False,index=False)
                        
                        del df_new,df,Nh,Nw,N
                    except Exception as e:
                        print(f"Error processing {filename}: {e}")
                        continue


    if data_list:
        file_final= pd.DataFrame(data_list)
        with open(file_out_trp, 'a') as f:
                df_string = file_final.to_string( index=False)
                f.write(df_string)
        print(f"Results saved to {file_out_trp}")
    else:
        print("No data processed.")
    
    return file_final

############################### EXAMPLE########################################
if __name__ == "__main__":
    # Example: July 2024
    RS_Tropospheric_Parameters(2024, 2024, 7, 8)
    
