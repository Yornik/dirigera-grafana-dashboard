"""Generated test data for the README screenshots: 7 days, 1 sample every 60 s.

Writes data2.om in the OpenMetrics format. Load it into an empty Prometheus:

    PYTHONHASHSEED=0 python3 tools/testdata.py
    promtool tsdb create-blocks-from openmetrics data2.om promdata

No value in it is a real reading.
"""
import time, math, random
random.seed(11)
END = int(time.time()) // 3600 * 3600
STEP = 60
T = list(range(END - 7 * 86400 - 3600, END + 1, STEP))
def hour(t): return ((t % 86400) / 3600 + 1) % 24     # local time, UTC+1
fam = {}
state = {}
PHASE = {"Bedroom": 10.5, "Living room": 9.0, "Office": 8.2, "Bathroom": 9.8}
def add(metric, labels, t, v):
    lab = ",".join('%s="%s"' % kv for kv in labels.items())
    fam.setdefault(metric, []).append("%s{%s} %s %d" % (metric, lab, v, t) if lab else "%s %s %d" % (metric, v, t))
air = {  # room: (sensor, base temp, swing, base rh, has co2/pm25)
    "Bedroom": ("Bedroom sensor", 18.2, 1.0, 58, True), "Living room": ("Living room sensor", 20.6, 1.0, 48, True),
    "Office": ("Office sensor", 19.4, 0.8, 52, False), "Bathroom": ("Bathroom sensor", 21.0, 0.6, 62, False)}
lights = [("Kitchen","Ceiling 1"),("Kitchen","Ceiling 2"),("Kitchen","Worktop strip"),("Living room","Floor lamp"),("Living room","Reading lamp"),
          ("Living room","TV light"),("Bedroom","Bedside"),("Bedroom","Ceiling"),("Entrance","Hall 1"),("Entrance","Hall 2"),("Bathroom","Mirror")]
def light(room, name, t):
    h = hour(t)
    if room == "Kitchen": on = 6.7 < h < 7.6 or 17.5 < h < 20.2; lvl = 100 if name != "Worktop strip" else 60
    elif room == "Living room": on = 17 < h < 23.2 and not (name == "Reading lamp" and h < 20.5); lvl = 100 if h < 21 else (45 if name != "TV light" else 20)
    elif room == "Bedroom": on = 6.4 < h < 7.1 or 22.3 < h < 23.6; lvl = 25 if name == "Bedside" else 70
    elif room == "Entrance": on = (int(t/600) * 2654435761 % 97) < (14 if 7 < h < 23 else 2); lvl = 80
    else: on = 6.5 < h < 7.0 or 22.0 < h < 22.4; lvl = 100
    return on, lvl
remotes = [("Kitchen","Kitchen wheel",85),("Living room","Sofa wheel",27),("Bedroom","Bedroom wheel",12),("Bathroom","Bath wheel",93)]
motions = 0; was = False; last_motion = None; presses = {r[1]: 0 for r in remotes}
for t in T:
    h = hour(t); day = (t - T[0]) // 86400
    add("ikea_dirigera_last_success_timestamp_seconds", {}, t, t)
    add("ikea_dirigera_scrape_success", {}, t, 1)
    for room, (sensor, base, swing, rh, full) in air.items():
        L = {"sensor": sensor, "room": room}
        st = state.setdefault(room, {"n": 0.0, "hn": 0.0, "co2": 480.0, "pm": 2.0, "amp": {}, "peak": {}})
        amp = st["amp"].setdefault(day, random.uniform(0.65, 1.25)); ph = PHASE[room]
        # A heating day: a slow rise after the morning, a plateau, a fall at night. Not a pure sine.
        x = math.sin(2 * math.pi * (h - ph) / 24); shape = math.copysign(abs(x) ** 0.7, x)
        st["n"] += 0.02 * (random.gauss(0, 1) - 0.6 * st["n"])                     # slow, smooth wander
        weather = 0.5 * math.sin(2 * math.pi * (t - T[0]) / (3.3 * 86400) + ph)    # warmer and cooler days
        temp = base + swing * amp * shape + weather + 0.25 * st["n"]
        add("ikea_air_temperature_celsius", L, t, round(temp, 2))
        st["hn"] += 0.03 * (random.gauss(0, 1) - 0.5 * st["hn"])
        hum = rh - 3.2 * amp * shape - 3.0 * weather + 1.6 * st["hn"]
        if room == "Bedroom" and (h > 23 or h < 7): hum += 3.5
        if room == "Bathroom":                                                      # a shower: up fast, down slowly
            since = (h - 7.1) % 24
            if since < 2.5: hum += 14 * amp * math.exp(-since / 0.55) * min(1, since / 0.08)
        add("ikea_air_humidity_percent", L, t, round(hum))
        if full:
            if room == "Bedroom": target = st["peak"].setdefault(("n", day), random.uniform(1020, 1320)) if (h >= 23 or h < 7) else 470
            else: target = st["peak"].setdefault(("e", day), random.uniform(700, 920)) if 19 < h < 23 else 480
            tau = 110 if target > st["co2"] else 45                                # minutes: fills slowly, airs fast
            st["co2"] += (target - st["co2"]) * (STEP / 60) / tau
            add("ikea_air_co2_ppm", L, t, round(st["co2"] + random.uniform(-6, 6)))
            cook = room == "Living room" and day in (1, 3, 4, 6) and abs(h - (18.3 + 0.1 * day)) < STEP / 7200
            candle = room == "Bedroom" and day == 2 and abs(h - 21.0) < STEP / 7200
            if cook: st["pm"] += st["peak"].setdefault(("p", day), random.uniform(45, 150))
            if candle: st["pm"] += 55
            st["pm"] += (1.6 + 0.6 * math.sin(t / 9000.0) - st["pm"]) * (STEP / 60) / 14
            add("ikea_air_pm25_micrograms_per_cubic_meter", L, t, max(0, round(st["pm"])))
        add("ikea_dirigera_device_reachable", L, t, 1)
    P = {"sensor": "Purifier", "room": "Bedroom"}
    boost = state.get("Bedroom", {}).get("pm", 0) > 12
    add("ikea_air_purifier_motor_speed", P, t, 35 if boost else 10)
    add("ikea_air_purifier_running", P, t, 1)
    add("ikea_air_purifier_filter_alarm", P, t, 0)
    add("ikea_air_purifier_pm25", P, t, round(12 + 2.0 * state.get("Bedroom", {}).get("pm", 2)) + random.choice((-1, 0, 1)))
    for mode in ("off", "on", "low", "medium", "high", "auto"):
        add("ikea_air_purifier_fan_mode", {**P, "mode": mode}, t, 1 if mode == "auto" else 0)
    add("ikea_dirigera_device_reachable", P, t, 1)
    for room, name in lights:
        L = {"sensor": name, "room": room}
        reach = not (room == "Bathroom" and END - 15*3600 < t < END - 12*3600)
        add("ikea_dirigera_device_reachable", L, t, int(reach))
        if not reach: continue
        on, lvl = light(room, name, t)
        add("ikea_light_on", L, t, int(on)); add("ikea_light_level_percent", L, t, lvl); add("ikea_light_color_temperature_kelvin", L, t, 2702)
    H = {"sensor": "Hall sensor", "room": "Entrance"}
    moving = (int(t/300) * 2246822519 % 101) < (22 if 7 < h < 23 else 3)
    if moving and not was: motions += 1; last_motion = t
    was = moving
    add("ikea_motion_detected", H, t, int(moving))
    add("ikea_motion_detections_total", H, t, motions)
    if last_motion: add("ikea_motion_last_detected_timestamp_seconds", H, t, last_motion)
    lux = max(0, round(140 * math.sin(math.pi * (h - 7.5) / 9.5))) if 7.5 < h < 17 else 0
    add("ikea_illuminance_lux", H, t, lux + (60 if light("Entrance", "Hall 1", t)[0] else 0))
    add("ikea_dirigera_device_battery_percent", H, t, 97); add("ikea_dirigera_device_reachable", H, t, 1)
    for room, name, b in remotes:
        L = {"sensor": name, "room": room}
        frac = (t - T[0]) / (T[-1] - T[0])
        v = b if name not in ("Sofa wheel", "Bedroom wheel") else (33 - 6 * frac if name == "Sofa wheel" else 18 - 6 * frac)
        add("ikea_dirigera_device_reachable", L, t, 1); add("ikea_dirigera_device_battery_percent", L, t, round(v))
        rate = {"Kitchen wheel": 9, "Sofa wheel": 14, "Bedroom wheel": 6, "Bath wheel": 4}[name]
        if 7 < h < 23.5 and (int(t / STEP) * 40503 + hash(name)) % 997 < rate: presses[name] += 1
        add("ikea_remote_presses_total", {**L, "pattern": "singlePress"}, t, presses[name])
    add("ikea_dirigera_device_reachable", {"sensor": "Old remote", "room": "Living room"}, t, 0)
with open("data2.om", "w") as f:
    for metric, lines in fam.items():
        f.write("# TYPE %s %s\n" % (metric, "counter" if metric.endswith("_total") else "gauge"))
        f.write("\n".join(lines) + "\n")
    f.write("# EOF\n")
print(sum(len(v) for v in fam.values()), "samples, motions", motions, presses)
