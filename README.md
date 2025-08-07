# Radiosonde_Troposphere
Python codes for downloading radiosonde data from the University of Wyoming. The downloaded files will be saved in directories (e.g., RS11035/2024/07) as text files. To perform the download, the save_RS_wyoming.py function should be used.

This also allows for the calculation of tropospheric parameters such as Precipitable Water Vapour (PWV), Wet Refractivity (Nw), Zenith Tropospheric Delay (ZTD), and Zenith Wet Delay (ZWD).
There are two separate output files that will be created using RS_Tropospheric_data.py:

* A text file for Nw for each station and hour.
* A CSV file containing all other parameters for the selected years, months, and hours.

---------------#Requirements-------------

pandas     # pip install pandas  
numpy      # pip install numpy  
requests   # pip install requests  
bs4        # pip install beautifulsoup4  

# Credit
If you use these codes on GitHub, please cite the following reference:
- Adavi Z, Ghassemi B, Weber R, Hanna N. Machine Learning-Based Estimation of Hourly GNSS Precipitable Water Vapour. Remote Sensing. 2023; 15(18):4551. https://doi.org/10.3390/rs15184551
