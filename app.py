from flask import Flask, request, redirect, url_for, render_template
import requests
import pandas as pd
import matplotlib.pyplot as plt
import datetime

app = Flask(__name__)
app.secret_key = "alsndbgiujdjfk[qekf;dsk]"
app.config["DEBUG"] = True

api_key = "72bf6eb2246493bb869d99a07ad80220"

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        location = request.form["location"]
        data = get_weather_data(location)
        log_data(data)
        current, hourly, daily = process_data(data)
        visualize_data(current, "Current")
        visualize_data(hourly, "Hourly")
        visualize_data(daily, "Daily")
        return render_template("result.html")
    return render_template("home.html")


def get_lat_lon(location):
    lat_lon_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=5&appid={api_key}"
    response = requests.get(lat_lon_url)
    data = response.json()
    return data[0]["lat"], data[0]["lon"]


def get_weather_data(location):
    lat, lon = get_lat_lon(location)
    weather_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&units=metric&appid={api_key}"
    response = requests.get(weather_url)
    data = response.json()
    return data


def process_data(data):
    current = data["current"]
    hourly = data["hourly"]
    daily = data["daily"]

    current_weather = {
        "temp": current["temp"],
        "feels_like": current["feels_like"],
        "humidity": current["humidity"],
        "wind_speed": current["wind_speed"],
        "weather": current["weather"][0]["description"],
    }

    hourly_weather = []
    for hour in hourly:
        hourly_weather.append({
            "time": hour["dt"],
            "temp": hour["temp"],
            "weather": hour["weather"][0]["description"],
        })

    daily_weather = []
    for day in daily:
        daily_weather.append({
            "time": day["dt"],
            "temp": day["temp"],
            "weather": day["weather"][0]["description"],
        })

    return current_weather, hourly_weather, daily_weather


def log_data(data):
    df = pd.DataFrame([data])
    df.to_csv("weather_data.csv", mode="a", header=False)


def visualize_data(data, title):
    times = [datetime.datetime.fromtimestamp(d["time"], tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S") for d in data]
    temps = [d["temp"] for d in data]

    plt.plot(times, temps)
    plt.xlabel("Time")
    plt.ylabel("Temp (Celsius)")
    plt.title(title + " Temperature Trends")
    plt.show()


if __name__ == "__main__":
    data = get_weather_data("Jerusalem")
    log_data(data)
    current, hourly, daily = process_data(data)
    # visualize_data(current, "Current")
    visualize_data(hourly, "Hourly")
    # visualize_data(daily, "Daily")