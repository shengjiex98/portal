# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
import displayio
import terminalio
from adafruit_matrixportal.matrixportal import MatrixPortal

def init():
    matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=True)

    # Get wifi details and more from a credentials.py file
    try:
        from credentials import credentials
    except ImportError:
        print("WiFi secrets are kept in credentials.py, please add them there!")
        raise

    matrixportal.network.connect(credentials)

    matrixportal.add_text(
        text_font=terminalio.FONT,
        text_position=(2, (matrixportal.graphics.display.height // 2) - 1),
        scrolling=False
    )

    return matrixportal

def display(matrixportal, text, delay):
    matrixportal.set_text(text)
    matrixportal.set_text_color('#808080')
    matrixportal.scroll_text(delay)

def fetch_text(matrixportal, url):
    r = matrixportal.network.requests.get(url)
    text = r.text
    r.close()
    return text

def fetch_json(matrixportal, url):
    r = matrixportal.network.requests.get(url)
    json = r.json()
    r.close()
    return json

def parse_api(xml_string):
    minutes_list = []
    start_index = 0

    while True:
        minutes_start = xml_string.find('minutes="', start_index)
        if minutes_start == -1:
            break
        minutes_end = xml_string.find('"', minutes_start + 9)
        minutes = xml_string[minutes_start + 9 : minutes_end]
        minutes_list.append(int(minutes))
        start_index = minutes_end

    # Get first two predictions (if exists) and convert to string
    minutes_list = ",".join(map(str, minutes_list[:2]))
    return minutes_list

def parse_time(time_string):
    hours = int(time_string[0:2])
    minutes = int(time_string[3:5])
    if hours == 12:
        hours = 0
    if time_string[-2:] == 'PM':
        hours += 12
    return hours * 60 + minutes

def predict_jfx(current_time):
    time_values = [
        '05:30AM', '06:00AM', '06:30AM', '06:45AM', '07:00AM', '07:15AM', '07:30AM', '07:45PM', 
        '08:00AM', '08:15AM', '08:30AM', '08:45AM', '09:00AM', '09:15AM', '09:30AM', '10:00AM', 
        '10:30AM', '11:00AM', '11:30AM', '12:00PM', '12:30PM', '01:00PM', '01:30PM', '02:00PM',
        '02:30PM', '03:00PM', '03:30PM', '04:00PM', '04:15PM', '04:30PM', '04:45PM', '05:00PM',
        '05:15PM', '05:30PM', '05:45PM', '06:00PM', '06:15PM', '06:30PM', '06:45PM', '07:00PM', 
        '07:30PM', '08:00PM'
    ]
    
    next_time = map(lambda x: parse_time(x) - current_time, time_values)
    next_time = map(lambda x: x if x > 0 else x + 60 * 24, next_time)
    next_time = sorted(next_time)
    
    next_time = f"{next_time[0]}" + f",{next_time[1]}" if next_time[1] < 60 else ''
    return next_time

def main():
    DELAY = 0.1
    API_CM = "https://retro.umoiq.com/service/publicXMLFeed?command=predictions&a=chapel-hill&r=CM&s=autoldf_n"
    API_TIME = "http://worldtimeapi.org/api/timezone/America/New_York"

    mp = init()

    while True:
        current_time = fetch_json(mp, API_TIME)['datetime']
        current_time = parse_time(current_time[11:16])

        # Nightmode
        if current_time < 6 * 60 + 30 or current_time > 22 * 60:
            display(mp, '', DELAY)
        else:
            xml_string = fetch_text(mp, API_CM)
            predictions_cm = parse_api(xml_string)
            predictions_jfx = predict_jfx(current_time)

            text_to_display = f"CM  {predictions_cm}\nJFX {predictions_jfx}"
            display(mp, text_to_display, DELAY)

        time.sleep(30)

main()
