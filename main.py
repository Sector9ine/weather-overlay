import os
import time
import threading
import requests
from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Set your WeatherAPI key and location here
WEATHER_API_KEY = '89ff8cf55d8e44f39c390702252907'
LOCATION = 'Bangkok'

last_weather = None

def fetch_weather():
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={LOCATION}&aqi=yes"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'error': str(e)}

def weather_monitor_thread():
    global last_weather
    while True:
        data = fetch_weather()
        print(data)
        if 'error' not in data:
            current = data.get('current', {})
            location = data.get('location', {})
            aqi = current.get('air_quality', {})
            pm25 = aqi.get('pm2_5', '')
            pm10 = aqi.get('pm10', '')
            o3 = aqi.get('o3', '')
            no2 = aqi.get('no2', '')
            so2 = aqi.get('so2', '')
            co = aqi.get('co', '')
            city = location.get('name', '')
            country = location.get('country', '')
            condition = current.get('condition', {}).get('text', '')
            temp_f = current.get('temp_f', '')
            humidity = current.get('humidity', '')
            percipitation = current.get('precip_mm', '')
            wind_mph = current.get('wind_mph', '')
            weather_str = f"{city}, {country}: {condition}, {temp_f}°F, Wind: {wind_mph} mph, Humidity: {humidity}%, Precip: {percipitation} mm, PM2.5: {pm25}, PM10: {pm10}, O3: {o3}, NO2: {no2}, SO2: {so2}, CO: {co}"
            if weather_str != last_weather:
                last_weather = weather_str
                socketio.emit('weather_update', weather_str)
        else:
            socketio.emit('weather_update', f"Error: {data['error']}")
        time.sleep(300)  # Check every 60 seconds

@app.route('/')
def index():
    return render_template('weather.html')

@socketio.on('connect')
def on_connect():
    # Send the last known weather immediately
    if last_weather:
        socketio.emit('weather_update', last_weather)

if __name__ == '__main__':
    threading.Thread(target=weather_monitor_thread, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000 , allow_unsafe_werkzeug=True)
