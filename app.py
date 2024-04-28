from flask import Flask, request, redirect, url_for, render_template
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import datetime
import mpld3
import plotly.graph_objects as go
import numpy as np

matplotlib.use('Agg')
app = Flask(__name__)
app.secret_key = "alsndbgiujdjfk[qekf;dsk]"
app.config["DEBUG"] = True

weather_api_key = "72bf6eb2246493bb869d99a07ad80220"


@app.route("/")
def index():
    return redirect(url_for("home"))

fig_html = ""

@app.route("/check_weather", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        location = request.form["location"]
        data = get_weather_data(location)
        log_data(data)
        current, hourly_df, daily_df, daily_days, weekday, cur_date = process_data(data)
        global fig_html
        fig_html = save_trends_images(hourly_df, daily_df, daily_days, weekday, cur_date)
        cur_time = f"time: {datetime.datetime.now().strftime("[%d-%m-%Y] %H:%M")} {weekday}"
        cur_temp = f"temperature: {current["temp"]} \u00b0C"
        hourly_image = "hourly-weather.png"
        daily_image = "daily-weather.png"
        return redirect(url_for("result", cur_time=cur_time, cur_temp=cur_temp, hourly_image=hourly_image, daily_image=daily_image, location=location))
    return render_template("home.html")


@app.route("/weather_forecast_results")
def result():
    cur_time = request.args.get("cur_time")
    cur_temp = request.args.get("cur_temp")
    hourly_image = request.args.get("hourly_image")
    daily_image = request.args.get("daily_image")
    location = request.args.get("location")
    # fig_html = request.args.get("fig_html")
    return render_template("result.html", cur_time=cur_time, cur_temp=cur_temp, hourly_image=hourly_image, daily_image=daily_image, location=location)


def get_lat_lon(location):
    lat_lon_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=5&appid={weather_api_key}"
    response = requests.get(lat_lon_url)
    data = response.json()
    return data[0]["lat"], data[0]["lon"]


def get_weather_data(location):
    lat, lon = get_lat_lon(location)
    weather_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&units=metric&appid={weather_api_key}"
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

    cur_date = datetime.datetime.now().date()

    return current, hourly_df, daily_df, daily_days, weekday_dict[(cur_date.weekday() + 2) % 7], cur_date


def save_trends_images(hourly_df, daily_df, daily_days, weekday, cur_date):
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

    half_hours = temp_hourly[:len(hourly_df["hour"]) // 2]
    half_temps = hourly_df['temp'][:len(hourly_df["temp"]) // 2]

    # fig = go.Figure(data=go.Scatter(x=half_hours, y=half_temps, mode='markers+lines', 
    #                             text=[f'({x}, {y})' for x, y in zip(half_hours, half_temps)], 
    #                             hoverinfo='text'))

    # fig.update_layout(title=f"Hourly Temperature Trends - Today {cur_date} {weekday}",
    #                 xaxis_title="Time",
    #                 yaxis_title="Temp (Celsius)")

    # fig_html = fig.to_html(full_html=False)

    plt.figure(figsize=(15, 7))
    fig, ax = plt.subplots()
    
    # ax.plot([3,1,4,1,5], 'ks-', mec='w', mew=5, ms=20)
    plt.plot(half_hours, half_temps)
    plt.scatter(half_hours, half_temps, color='red')
    for i, txt in enumerate(half_temps):
        plt.text(half_hours[i], half_temps[i], f'({half_hours[i]}, {txt})', fontsize=7)
    plt.xlabel("Time")
    plt.ylabel("Temp (Celsius)")
    plt.title(f"Hourly Temperature Trends - Today {cur_date} {weekday}")
    new_arr = []
    for i in range(0, len(half_hours), 2):
        new_arr += [half_hours[i]]

    print(new_arr)
    plt.xticks(new_arr)
    plt.tight_layout()
    plt.savefig('static/hourly-weather.png')
    # fig_html = mpld3.fig_to_html(fig)
    plt.close()

    # show daily weather for the next 7 days

    plt.figure(figsize=(15, 7))
    plt.plot(daily_days, daily_df['temp_min'], label="Min Temp")
    plt.scatter(daily_days, daily_df['temp_min'], color='blue')
    for i, txt in enumerate(daily_df['temp_min']):
        plt.text(daily_days[i], daily_df['temp_min'][i], f'({txt})', fontsize=7)
    
    plt.plot(daily_days, daily_df['temp_max'], label="Max Temp")
    plt.scatter(daily_days, daily_df['temp_max'], color='red')
    for i, txt in enumerate(daily_df['temp_max']):
        plt.text(daily_days[i], daily_df['temp_max'][i], f'({txt})', fontsize=7)
    
    plt.xlabel("Date")
    plt.ylabel("Temp (Celsius)")
    plt.title("Daily Temperature Trends")
    plt.legend()
    plt.savefig('static/daily-weather.png')

    # return fig_html


if __name__ == "__main__":
    # data = get_weather_data("Sakhnin")
    # log_data(data)
    # process_data(data)
    # visualize_data(current, hourly, daily)
    app.run()
