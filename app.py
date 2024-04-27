from flask import Flask, request, redirect, url_for, render_template
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import datetime

matplotlib.use('Agg')
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
        current, hourly_df, daily_df, daily_days, weekday_dict = process_data(data)
        save_trends_images(current, hourly_df, daily_df, daily_days, weekday_dict)
        cur_weather = f"current weather\ntime: {datetime.datetime.now().time().strftime("%H:%M")} temperature: {current["temp"]}"
        hourly_image = "hourly-weather.png"
        daily_image = "daily-weather.png"
        return render_template("result.html", cur_weather=cur_weather, hourly_image=hourly_image, daily_image=daily_image)
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


def log_data(data):
    df = pd.DataFrame([data])
    df.to_csv("weather_data.csv", mode="a", header=False)


def process_data(data):
    current = data["current"]
    hourly_df = pd.DataFrame(list(data["hourly"]))
    daily_df = pd.DataFrame(list(data["daily"]))

    hourly_df['time'] = pd.to_datetime(hourly_df['dt'], unit='s')
    daily_df['time'] = pd.to_datetime(daily_df['dt'], unit='s')
    
    weekday_dict = {1: "Sunday", 2: "Monday", 3: "Tuesday", 4: "Wednesday", 5: "Thursday", 6: "Friday", 0: "Saturday"}

    hourly_df['hour'] = hourly_df['time'].dt.strftime("%H\n%m-%d")
    daily_df['weekday_num'] = (daily_df["time"].dt.weekday + 2) % 7
    daily_df['weekday'] = daily_df['weekday_num'].map(weekday_dict)
    daily_df['day'] = daily_df['time'].dt.strftime('%m-%d\n')

    daily_df["temp_day"] = daily_df["temp"].apply(lambda x: x["day"])
    daily_df["temp_night"] = daily_df["temp"].apply(lambda x: x["night"])
    daily_df["temp_min"] = daily_df["temp"].apply(lambda x: x["min"])
    daily_df["temp_max"] = daily_df["temp"].apply(lambda x: x["max"])
    daily_df["temp_morn"] = daily_df["temp"].apply(lambda x: x["morn"])
    daily_df["temp_eve"] = daily_df["temp"].apply(lambda x: x["eve"])

    daily_days = daily_df["day"].to_list()
    for i in range(len(daily_days)):
        daily_days[i] += str(daily_df["weekday"][i])

    return current, hourly_df, daily_df, daily_days, weekday_dict


def save_trends_images(current, hourly_df, daily_df, daily_days, weekday_dict):

    # show current weather
    # print(f"current weather\ntime: {datetime.datetime.now().time().strftime("%H:%M")} temperature: {current["temp"]}")

    # show hourly weather for the next 24 hours
    temp_hourly = hourly_df["hour"].to_list()
    first = temp_hourly[0]
    ending = first[-5:]
    # keeping the date just when we jump from day to another
    for i in range(1, len(temp_hourly)):
        if temp_hourly[i].endswith(ending):
            temp_hourly[i] = temp_hourly[i][:-6]
        else:
            first = temp_hourly[i]
            ending = first[-5:]

    plt.figure(figsize=(10, 6))
    plt.plot(temp_hourly[:len(hourly_df["hour"]) // 2], hourly_df['temp'][:len(hourly_df["temp"]) // 2])
    plt.xlabel("Time")
    plt.ylabel("Temp (Celsius)")
    cur_date = datetime.datetime.now().date()
    plt.title(f"Hourly Temperature Trends - Today {cur_date} {weekday_dict[(cur_date.weekday() + 2) % 7]}")
    plt.savefig('static/hourly-weather.png')
    plt.close()

    # show daily weather for the next 7 days

    plt.figure(figsize=(10, 6))
    plt.plot(daily_days, daily_df['temp_min'], label="Min Temp")
    plt.plot(daily_days, daily_df['temp_max'], label="Max Temp")
    plt.xlabel("Date")
    plt.ylabel("Temp (Celsius)")
    plt.title("Daily Temperature Trends")
    plt.legend()
    plt.savefig('static/daily-weather.png')


if __name__ == "__main__":
    # data = get_weather_data("Sakhnin")
    # log_data(data)
    # process_data(data)
    # visualize_data(current, hourly, daily)
    app.run()
