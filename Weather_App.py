import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from geopy.geocoders import Nominatim
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib import dates as mdates
from PIL import ImageTk, Image

class MeteoDataProcessor:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude
        self.setup_openmeteo_client()
        self.current_data = {}
    def setup_openmeteo_client(self):
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.openmeteo = openmeteo_requests.Client(session=retry_session)
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_columns", None)

    def process_location_data(self, response):
        result = f"Coordonatele sunt: {response.Latitude()}°N {response.Longitude()}°E\n"
        result += f"Altitudinea fata de nivelul marii {response.Elevation()} m asl\n"
        result += f"Fusul orar {response.Timezone()} {response.TimezoneAbbreviation()}\n"
        result += f"Ora locală este cu {response.UtcOffsetSeconds()} de secunde înaintea timpului mediu Greenwich (GMT)\n"
        return result

    def process_current_data(self, current):
        variables = [
            "temperatura actuala", "umiditatea", "temeperatura resimtita", "is_day",
            "precipitatii", "ploi", "averse", "caderi de zapada",  "acoperirea norilor",
            "presiunea la nivelul marii", "presiunea la suprafata", "viteza vantului",
        ]

        current_data = {variable: current.Variables(i).Value() for i, variable in enumerate(variables)}
        current_data["temperatura actuala"] = round(current_data["temperatura actuala"], 2)
        current_data["Current time"] = current.Time()
        current_data["is_day"] = "este zi" if current_data["is_day"] else "este noapte"
        current_data["temeperatura resimtita"] = round(current_data["temeperatura resimtita"], 2)
        current_data["viteza vantului"]= round(current_data["viteza vantului"],2)
        result = ""
        current_data.pop("Current time", None)

        for variable, value in current_data.items():
            result += f" {variable}: {value}\n"
        return result

    def process_hourly_data(self, hourly):
        variables = [
            "temperature_2m", "relative_humidity_2m", "dew_point_2m", "apparent_temperature",
            "precipitation_probability", "precipitation", "rain", "showers", "snowfall",
            "snow_depth", "cloud_cover",
            "visibility",
            "wind_speed_10m",
            "wind_direction_10m", "soil_temperature_0cm"
        ]

        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s"),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s"),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left"
            )
        }

        for i, variable in enumerate(variables):
            hourly_data[variable] = hourly.Variables(i).ValuesAsNumpy()

        hourly_dataframe = pd.DataFrame(data=hourly_data)
        result = str(hourly_dataframe)
        return result

    def process_daily_data(self, daily):
        variables = [
            "weather_code", "temperature_2m_max", "temperature_2m_min",
            "apparent_temperature_max", "apparent_temperature_min", "sunrise", "sunset",
            "daylight_duration", "sunshine_duration", "uv_index_max", "uv_index_clear_sky_max",
            "precipitation_sum", "rain_sum", "showers_sum", "snowfall_sum",
            "precipitation_hours", "precipitation_probability_max", "wind_speed_10m_max",
            "wind_gusts_10m_max", "wind_direction_10m_dominant", "shortwave_radiation_sum",
            "et0_fao_evapotranspiration"
        ]

        daily_data = {
            "date": pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s"),
                end=pd.to_datetime(daily.TimeEnd(), unit="s"),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left"
            )
        }

        for i, variable in enumerate(variables):
            daily_data[variable] = daily.Variables(i).ValuesAsNumpy()

        daily_dataframe = pd.DataFrame(data=daily_data)
        result = str(daily_dataframe)
        return result

    def get_weather_data(self):
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "is_day",
                        "precipitation", "rain", "showers", "snowfall", "weather_code", "cloud_cover",
                        "pressure_msl", "surface_pressure", "wind_speed_10m", "wind_direction_10m",
                        "wind_gusts_10m"],
            "hourly": ["temperature_2m", "relative_humidity_2m", "dew_point_2m", "apparent_temperature",
                       "precipitation_probability", "precipitation", "rain", "showers", "snowfall",
                       "snow_depth", "cloud_cover", "visibility", "wind_speed_10m", "wind_direction_10m",
                       "soil_temperature_0cm"],

            "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min",
                      "apparent_temperature_max", "apparent_temperature_min", "sunrise", "sunset",
                      "daylight_duration", "sunshine_duration", "uv_index_max", "uv_index_clear_sky_max",
                      "precipitation_sum", "rain_sum", "showers_sum", "snowfall_sum",
                      "precipitation_hours", "precipitation_probability_max", "wind_speed_10m_max",
                      "wind_gusts_10m_max", "wind_direction_10m_dominant", "shortwave_radiation_sum",
                      "et0_fao_evapotranspiration"],
            "timezone": ["auto"]
        }

        responses = self.openmeteo.weather_api(url, params=params)

        current_result = ""
        hourly_result = ""
        daily_result = ""

        for response in responses:
            current_result += self.process_location_data(response) + "\n"
            current_result += self.process_current_data(response.Current()) + "\n"

            hourly_result += self.process_hourly_data(response.Hourly()) + "\n"
            daily_result += self.process_daily_data(response.Daily()) + "\n"

        return current_result, hourly_result, daily_result

    def process_hourly_data_for_graph(self, response):
        variables = ["temperature_2m"]
        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(response.Hourly().Time(), unit="s"),
                end=pd.to_datetime(response.Hourly().TimeEnd(), unit="s"),
                freq=pd.Timedelta(seconds=response.Hourly().Interval()),
                inclusive="left"
            )
        }

        for i, variable in enumerate(variables):
            hourly_data[variable] = response.Hourly().Variables(i).ValuesAsNumpy()

        hourly_dataframe = pd.DataFrame(data=hourly_data)
        return hourly_dataframe

    # def get_weather_image_file(self, current_data):
    #     is_day = current_data.get("is_day", "este zi")
    #
    #     if is_day == "este zi":
    #         return "soare-128.png"
    #     else:
    #         return "luna-128.png"


class App:
    def __init__(self, master):
        self.master = master
        self.master.title("Weather Data Processor")

        self.geolocator = Nominatim(user_agent="weather_app")
        self.coordinates = {}
        self.current_data = {}

        self.city_label = ttk.Label(master, text="Introduceti orasul:")
        self.city_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.city_entry = ttk.Entry(master)
        self.city_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.show_details_button = ttk.Button(master, text="Show Details", command=self.show_details)
        self.show_details_button.grid(row=1, column=1, pady=10)
        self.process_button = ttk.Button(master, text="Search", command=self.get_coordinates)
        self.process_button.grid(row=1, column=0, columnspan=1, pady=10)
        self.show_graph_button = ttk.Button(master, text="Grafic", command=self.show_graph)
        self.show_graph_button.grid(row=1, column=1, columnspan=2, pady=10)
        self.weather_image_label = ttk.Label(master)
        self.weather_image_label.grid(row=3, column=0, columnspan=2, pady=10)

        self.result_text = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=80, height=20)
        self.result_text.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
    def get_coordinates(self):
        city_name = self.city_entry.get()
        geolocator = Nominatim(user_agent="weather_app")
        location = geolocator.geocode(city_name)

        if location:
            latitude = location.latitude
            longitude = location.longitude
            meteo_processor = MeteoDataProcessor(latitude=latitude, longitude=longitude)
            current_result, _, _ = meteo_processor.get_weather_data()
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, current_result)


            # image_file = meteo_processor.get_weather_image_file(meteo_processor.current_data)
            # self.display_weather_image(image_file)
        else:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"Acest oraș nu există: {city_name}")

    # def display_weather_image(self, image_filename):
    #     try:
    #
    #         image_path = f"C:\\Users\\ASUS\OneDrive\\Desktop\\TEMA IA\\proiect/{image_filename}"
    #         img = Image.open(image_path)
    #         img = img.resize((50, 50))
    #
    #         photo = ImageTk.PhotoImage(img)
    #         self.weather_image_label.config(image=photo)
    #         self.weather_image_label.image = photo
    #
    #     except Exception as e:
    #         print(f"Error displaying image: {e}")

    def show_details(self):
        city_name = self.city_entry.get()
        geolocator = Nominatim(user_agent="weather_app")
        location = geolocator.geocode(city_name)

        if location:
            meteo_processor = MeteoDataProcessor(latitude=location.latitude, longitude=location.longitude)
            details = meteo_processor.process_location_data(location.raw)
            details_window = DetailsWindow(self.master, details)
        else:
            messagebox.showerror("Eroare", f"Acest oraș nu există: {city_name}")

    def show_graph(self):
        city_name = self.city_entry.get()
        geolocator = Nominatim(user_agent="weather_app")
        location = geolocator.geocode(city_name)

        if location:
            latitude = location.latitude
            longitude = location.longitude
            meteo_processor = MeteoDataProcessor(latitude=latitude, longitude=longitude)
            response = meteo_processor.openmeteo.weather_api("https://api.open-meteo.com/v1/forecast", params={
                "latitude": latitude,
                "longitude": longitude,
                "hourly": ["temperature_2m"],
            })[0]

            hourly_data = meteo_processor.process_hourly_data_for_graph(response)

            # Selectați prima zi din setul de date
            selected_day = hourly_data['date'].dt.date.unique()[0]
            selected_day_data = hourly_data[hourly_data['date'].dt.date == selected_day]

            # Crearea și afișarea graficului
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.stem(selected_day_data['date'], selected_day_data['temperature_2m'], label='Temperatura')
            ax.set_title(f'Temperatura la data de {selected_day}')
            ax.set_xlabel('Timp')
            ax.set_ylabel('Temperatura(°C)')
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_minor_locator(mdates.HourLocator())


            ax.set_xlim([pd.to_datetime(selected_day), pd.to_datetime(selected_day) + pd.Timedelta(days=1)])
            ax.legend()


            second_window = tk.Toplevel(self.master)
            second_window.title("Graph")
            canvas = FigureCanvasTkAgg(fig, master=second_window)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)


            toolbar = NavigationToolbar2Tk(canvas, second_window)
            toolbar.update()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        else:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"Acest oraș nu există: {city_name}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
