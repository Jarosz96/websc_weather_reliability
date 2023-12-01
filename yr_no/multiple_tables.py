from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

# Your directory where .xlsx file is stored
file_directory = os.getenv("FILE_DIRECTORY")

# List of URLs for scraping from different destinations
base_urls = ["https://www.yr.no/en/forecast/daily-table/2-2673730/Sweden/Stockholm/Stockholm%20Municipality/Stockholm",
             "https://www.yr.no/en/forecast/daily-table/2-9114206/Sweden/Jämtland/Åre%20Municipality/Åre"]


# Loop through each destination in base_urls
for base_url in base_urls:

    # Try to read existing excel files data, if not found initialize as an empty dictionary
    try:
        existing_data = pd.read_excel(f"{file_directory}scraped_weather_{base_url.split('/')[-1]}.xlsx", sheet_name=None)
    except FileNotFoundError:
        existing_data = {}

    # Iterating through days (days forecasted), extracting data
    for i in range(1, 10):
        url = f"{base_url}{i}"
        page_to_scrape = requests.get(url)
        soup = BeautifulSoup(page_to_scrape.content, "html.parser")

        specific_item = soup.find("li", {"class": "daily-weather-list-item", "id": f"dailyWeatherListItem{i}"})

        max_temperature_warm = specific_item.findAll("span", {"class": "temperature min-max-temperature__max temperature--warm"})
        max_temperature_cold = specific_item.findAll("span", {"class": "temperature min-max-temperature__max temperature--cold"})
        min_temperature_warm = specific_item.findAll("span", {"class": "temperature min-max-temperature__min temperature--warm"})
        min_temperature_cold = specific_item.findAll("span", {"class": "temperature min-max-temperature__min temperature--cold"})
        precipitation = specific_item.find("span", {"class": "Precipitation-module__main-sU6qN"}).text
        date = specific_item.find("a", {"class": "daily-weather-list-item__item-date"}).text

        # Function to extract numbers from text
        def extract_numbers(text):
            numbers = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", text)
            return float(numbers[0]) if numbers else None

        max_temperature = extract_numbers(max_temperature_warm[0].text) if max_temperature_warm else extract_numbers(max_temperature_cold[0].text)
        min_temperature = extract_numbers(min_temperature_warm[0].text) if min_temperature_warm else extract_numbers(min_temperature_cold[0].text)
        precipitation = extract_numbers(precipitation)
        
        # Parsing and formatting the date to get the right year
        parsed_date = datetime.strptime(date, "%A %d %b.")
        current_date = datetime.now()
        date_iso = parsed_date.replace(year=current_date.year if parsed_date.month >= current_date.month else current_date.year + 1).strftime("%Y-%m-%d")

        # Creating a dictionary for each columns in the file
        data = {
            "DATE": date_iso,
            "MAX_TEMP [°C]": max_temperature,
            "MIN_TEMP [°C]": min_temperature,
            "PRECIP [mm]": precipitation
        }

        # Appending or creating dataframe for each day's forecast
        if f"{i}_Day_Forecast" in existing_data:
            if date_iso not in existing_data[f"{i}_Day_Forecast"]['DATE'].values:
                existing_data[f"{i}_Day_Forecast"] = existing_data[f"{i}_Day_Forecast"]._append(data, ignore_index=True)
        else:
            existing_data[f"{i}_Day_Forecast"] = pd.DataFrame([data])

    # Writing the scraped data to the excel file for each destination
    with pd.ExcelWriter(f"{file_directory}scraped_weather_{base_url.split('/')[-1]}.xlsx") as writer:
        for name, sheet in existing_data.items():
            sheet.to_excel(writer, sheet_name=name, index=False)
