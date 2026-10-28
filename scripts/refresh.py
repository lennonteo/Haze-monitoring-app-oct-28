#!/usr/bin/env python3
"""Fetch fresh data and regenerate index.html.

PSI and PM2.5 come from NEA via data.gov.sg (Singapore only).
Weather for every city comes from Open-Meteo.

Usage:  python3 scripts/refresh.py
No third-party packages are needed. Set DATA_GOV_SG_API_KEY to send an
x-api-key header if you have one (the endpoint also works without it).
"""
import datetime
import json
import os
import pathlib
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PSI_URL = "https://api-open.data.gov.sg/v2/real-time/api/psi"
METEO_URL = "https://api.open-meteo.com/v1/forecast"

# id, name, country, label position on the ASEAN map, latitude, longitude
CITIES = [
    ("singapore", "Singapore", "Singapore", "r", 1.3521, 103.8198),
    ("kl", "Kuala Lumpur", "Malaysia", "l", 3.1390, 101.6869),
    ("jakarta", "Jakarta", "Indonesia", "b", -6.2088, 106.8456),
    ("bangkok", "Bangkok", "Thailand", "l", 13.7563, 100.5018),
    ("hanoi", "Hanoi", "Vietnam", "b", 21.0285, 105.8542),
    ("hcmc", "Ho Chi Minh City", "Vietnam", "r", 10.8231, 106.6297),
    ("manila", "Manila", "Philippines", "b", 14.5995, 120.9842),
    ("phnompenh", "Phnom Penh", "Cambodia", "l", 11.5564, 104.9282),
    ("yangon", "Yangon", "Myanmar", "b", 16.8409, 96.1951),
    ("bsb", "Bandar Seri Begawan", "Brunei", "b", 4.9031, 114.9398),
]
REGIONS = ["north", "south", "east", "west", "central"]
SGT = datetime.timezone(datetime.timedelta(hours=8))


def get_json(url, headers=None, attempts=3):
    last = None
    for i in range(attempts):
        try:
            h = {"User-Agent": "haze-watch-refresh/1.0", "Accept": "application/json"}
            h.update(headers or {})
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # retry on timeouts and transient errors
            last = e
            time.sleep(2 * (i + 1))
    raise SystemExit(f"Could not fetch {url}: {last}")


def fetch_psi():
    headers = {}
    key = os.environ.get("DATA_GOV_SG_API_KEY")
    if key:
        headers["x-api-key"] = key
    item = get_json(PSI_URL, headers)["data"]["items"][0]
    rd = item["readings"]
    regions = {}
    for r in REGIONS:
        regions[r] = {
            "psi": rd["psi_twenty_four_hourly"][r],
            "pm25": rd["pm25_twenty_four_hourly"][r],
            "pm10": rd["pm10_twenty_four_hourly"][r],
            "sub": {k: rd[k + "_sub_index"][r] for k in ["pm25", "pm10", "o3", "so2", "co"]},
        }
    return {"timestamp": item["timestamp"], "updated": item["updatedTimestamp"], "regions": regions}


def fetch_weather():
    q = (
        f"{METEO_URL}?latitude={','.join(str(c[4]) for c in CITIES)}"
        f"&longitude={','.join(str(c[5]) for c in CITIES)}"
        "&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,"
        "wind_speed_10m,wind_direction_10m,precipitation,is_day"
        "&hourly=temperature_2m,precipitation_probability,weather_code,is_day"
        "&daily=uv_index_max&forecast_days=2&timezone=auto&wind_speed_unit=kmh"
    )
    data = get_json(q)
    cities = []
    for (cid, name, country, pos, _, _), w in zip(CITIES, data):
        cur, h = w["current"], w["hourly"]
        i = h["time"].index(cur["time"][:13] + ":00")
        hours = [
            {
                "time": h["time"][j],
                "temp": h["temperature_2m"][j],
                "prob": h["precipitation_probability"][j],
                "code": h["weather_code"][j],
                "day": bool(h["is_day"][j]),
            }
            for j in range(i + 1, i + 9)
        ]
        cities.append(
            {
                "id": cid, "name": name, "country": country, "pos": pos,
                "lat": w["latitude"], "lon": w["longitude"],
                "cur": {
                    "time": cur["time"], "temp": cur["temperature_2m"],
                    "feels": cur["apparent_temperature"], "hum": cur["relative_humidity_2m"],
                    "code": cur["weather_code"], "wind": cur["wind_speed_10m"],
                    "dir": cur["wind_direction_10m"], "precip": cur["precipitation"],
                    "day": bool(cur["is_day"]), "prob": h["precipitation_probability"][i],
                },
                "hours": hours,
                "uv": w["daily"]["uv_index_max"][0],
            }
        )
    return cities


def main():
    geo = json.loads((ROOT / "src" / "geo.json").read_text())
    now = datetime.datetime.now(SGT)
    data = {
        "geo": geo,
        "psi": fetch_psi(),
        "cities": fetch_weather(),
        "captured": now.strftime("%H:%M SGT, ") + str(now.day) + now.strftime(" %b %Y"),
    }
    template = (ROOT / "src" / "template.html").read_text()
    (ROOT / "index.html").write_text(template.replace("__DATA__", json.dumps(data, separators=(",", ":"))))
    print("Wrote index.html, captured", data["captured"])
    print({k: v["psi"] for k, v in data["psi"]["regions"].items()})


if __name__ == "__main__":
    main()
