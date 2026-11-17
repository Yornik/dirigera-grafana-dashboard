"""Generated test data for the README screenshots: 7 days, 1 sample every 60 s.

Writes data2.om in the OpenMetrics format. Load it into an empty Prometheus:

    PYTHONHASHSEED=0 python3 tools/testdata.py
    promtool tsdb create-blocks-from openmetrics data2.om promdata

No value in it is a real reading. The data is composed, so that the
screenshots read well. It follows the golden ratio, phi = 1.618:

- The week builds up to a focal point at 0.618 of the time range: the widest
  temperature swing, the highest CO2 night and the highest PM2.5 peak are there.
- The PM2.5 peaks stand at the golden sections of the week (0.382, 0.618 and
  0.854) and their heights fall by phi: 150, 93 and 57.
- The gaps between the temperature lines shrink by phi, from the bottom up.
- On the lights dashboard the motions in each hour follow the Fibonacci numbers
  up to a focal hour at 0.618 of the day and back: 1, 1, 2, 3, 5, 8, 5, 3, 2, 1, 1.
  The presses of the 4 remotes in a day are 8, 5, 3 and 2.
"""
import time, math, random
random.seed(11)
END = int(time.time()) // 3600 * 3600
STEP = 60
PHI = (1 + 5 ** 0.5) / 2
WEEK0 = END - 7 * 86400
def focus(t):
    """1 at the golden section of the week, falling to about 0 at both ends."""
    return math.exp(-(((t - WEEK0) / (7 * 86400) - 1 / PHI) / 0.22) ** 2)
# Motions in each hour of the last 24: Fibonacci numbers up to the focal hour, 0.618 of the day, and back.
FIB_DAY = [0] * 24
for offset, count in zip(range(-5, 6), (1, 1, 2, 3, 5, 8, 5, 3, 2, 1, 1)):
    FIB_DAY[round(24 / PHI) + offset] = count
def motions_in_hour(t): return FIB_DAY[23 - ((END - 1 - t) // 3600) % 24]
def moving_at(t):
    count = motions_in_hour(t)
    return count > 0 and ((t % 3600) // 60) in {int((k + 0.5) * 60 / count) for k in range(count)}
PRESSES_A_DAY = {"Sofa wheel": 8, "Kitchen wheel": 5, "Bedroom wheel": 3, "Bath wheel": 2}
def pressed_at(name, t):
    count = PRESSES_A_DAY[name]; minute = ((t + 3600) % 86400) // 60 - 420       # between 07:00 and 23:00
    return 0 <= minute < 960 and minute in {int((k + 0.5) * 960 / count) for k in range(count)}
T = list(range(END - 7 * 86400 - 3600, END + 1, STEP))
def hour(t): return ((t % 86400) / 3600 + 1) % 24     # local time, UTC+1
fam = {}
state = {}
# The rooms in the order of their oldest device, as dirigera-exporter numbers them.
ROOMS = [("Bedroom", "rooms_bed"), ("Living room", "rooms_sofa"), ("Kitchen", "rooms_kitchen"), ("Office", "rooms_desk"),
         ("Entrance", "rooms_home"), ("Bathroom", "rooms_bathtub")]
PHASE = {"Bedroom": 10.5, "Living room": 9.0, "Office": 8.2, "Bathroom": 9.8}
def add(metric, labels, t, v):
    lab = ",".join('%s="%s"' % kv for kv in labels.items())
    fam.setdefault(metric, []).append("%s{%s} %s %d" % (metric, lab, v, t) if lab else "%s %s %d" % (metric, v, t))
air = {  # room: (sensor, base temp, swing, base rh, has co2/pm25)
    # The gaps between the temperature lines shrink by phi: 1.62, 1.0 and 0.62 degrees.
    "Bedroom": ("Bedroom sensor", 18.0, 1.0, 59, True), "Living room": ("Living room sensor", 20.62, 0.62, 46, True),
    "Office": ("Office sensor", 19.62, 0.62, 51, False), "Bathroom": ("Bathroom sensor", 21.24, 0.38, 62, False)}
lights = [("Kitchen","Ceiling 1"),("Kitchen","Ceiling 2"),("Kitchen","Worktop strip"),("Living room","Floor lamp"),("Living room","Reading lamp"),
          ("Living room","TV light"),("Bedroom","Bedside"),("Bedroom","Ceiling"),("Entrance","Hall 1"),("Entrance","Hall 2"),("Bathroom","Mirror")]
def light(room, name, t):
    h = hour(t)
    if room == "Kitchen": on = 6.7 < h < 7.6 or 17.5 < h < 20.2; lvl = 100 if name != "Worktop strip" else 60
    elif room == "Living room": on = 17 < h < 23.2 and not (name == "Reading lamp" and h < 20.5); lvl = 100 if h < 21 else (45 if name != "TV light" else 20)
    elif room == "Bedroom": on = 6.4 < h < 7.1 or 22.3 < h < 23.6; lvl = 25 if name == "Bedside" else 70
    elif room == "Entrance": on = any(moving_at(t - 60 * k) for k in range(4)); lvl = 80      # the motion sensor switches them
    else: on = 6.5 < h < 7.0 or 22.0 < h < 22.4; lvl = 100
    return on, lvl
remotes = [("Kitchen","Kitchen wheel",85),("Living room","Sofa wheel",27),("Bedroom","Bedroom wheel",12),("Bathroom","Bath wheel",93)]
motions = 0; was = False; last_motion = None; presses = {r[1]: 0 for r in remotes}
for t in T:
    h = hour(t); day = (t - T[0]) // 86400
    add("ikea_dirigera_last_success_timestamp_seconds", {}, t, t)
    add("ikea_dirigera_scrape_success", {}, t, 1)
    for number, (room, icon) in enumerate(ROOMS, start=1):
        add("ikea_dirigera_room_order", {"room": room}, t, number)
        add("ikea_dirigera_room_info", {"room": room, "icon": icon, "color": "ikea_green_no_65"}, t, 1)
    for room, (sensor, base, swing, rh, full) in air.items():
        L = {"sensor": sensor, "room": room}
        st = state.setdefault(room, {"n": 0.0, "hn": 0.0, "co2": 480.0, "pm": 2.0, "amp": {}, "peak": {}})
        amp = st["amp"].setdefault(day, 0.62 + 0.62 * focus(t + 43200) + random.uniform(-0.04, 0.04)); ph = PHASE[room]
        # A heating day: a slow rise after the morning, a plateau, a fall at night. Not a pure sine.
        x = math.sin(2 * math.pi * (h - ph) / 24); shape = math.copysign(abs(x) ** 0.7, x)
        st["n"] += 0.02 * (random.gauss(0, 1) - 0.6 * st["n"])                     # slow, smooth wander
        weather = 0.25 * math.sin(2 * math.pi * (t - T[0]) / (3.3 * 86400) + ph)   # warmer and cooler days
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
            if room == "Bedroom": target = st["peak"].setdefault(("n", day), 1010 + 320 * focus(t)) if (h >= 23 or h < 7) else 470
            else: target = st["peak"].setdefault(("e", day), 690 + 200 * focus(t)) if 19 < h < 23 else 480
            tau = 110 if target > st["co2"] else 45                                # minutes: fills slowly, airs fast
            st["co2"] += (target - st["co2"]) * (STEP / 60) / tau
            add("ikea_air_co2_ppm", L, t, round(st["co2"] + random.uniform(-6, 6)))
            # Cooking peaks at the golden sections of the week. Their heights fall by phi.
            for section, height in ((1 / PHI, 150), (1 - 1 / PHI, 150 / PHI), (1 / PHI + 1 / PHI ** 3, 150 / PHI ** 2)):
                if room == "Living room" and abs(t - (WEEK0 + section * 7 * 86400)) < STEP / 2: st["pm"] += height
            # A candle in the bedroom, 0.618 of an hour after the highest peak: the purifier answers.
            if room == "Bedroom" and abs(t - (WEEK0 + 7 * 86400 / PHI + 3600 / PHI)) < STEP / 2: st["pm"] += 150 / PHI ** 2
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
    moving = moving_at(t)
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
        if pressed_at(name, t): presses[name] += 1
        add("ikea_remote_presses_total", {**L, "pattern": "singlePress"}, t, presses[name])
    add("ikea_dirigera_device_reachable", {"sensor": "Old remote", "room": "Living room"}, t, 0)
with open("data2.om", "w") as f:
    for metric, lines in fam.items():
        f.write("# TYPE %s %s\n" % (metric, "counter" if metric.endswith("_total") else "gauge"))
        f.write("\n".join(lines) + "\n")
    f.write("# EOF\n")
print(sum(len(v) for v in fam.values()), "samples, motions", motions, presses)
