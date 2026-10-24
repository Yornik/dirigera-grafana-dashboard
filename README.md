# DIRIGERA Air Quality — Grafana dashboard

A Grafana dashboard for [`dirigera-exporter`](https://github.com/Yornik/dirigera-exporter),
visualising air quality from IKEA DIRIGERA environment sensors (VINDSTYRKA /
ALPSTUGA) and STARKVIND air purifiers, scraped by Prometheus.

<picture>
  <source media="(prefers-color-scheme: light)" srcset="docs/dashboard-light.png">
  <img alt="The DIRIGERA air quality dashboard, rendered with test data" src="docs/dashboard-dark.png" width="800">
</picture>

## Panels

- **Needs attention:** a full-width strip at the top. It lists only what needs
  you, in plain words with a ⚠ sign: a stuffy room (CO₂ 1000 ppm or more), a
  damp room (70 % or more for an hour), smoke or cooking (PM2.5 35 µg/m³ or
  more), a purifier filter to replace, a purifier that stopped, a sensor with no
  reading, or a hub that stopped answering. Otherwise it says "Nothing right
  now".
- **Now:** one tile each for temperature, humidity, CO₂ and PM2.5, per room,
  with a status word (for example "Bedroom: fresh").
- **History:** temperature, humidity, CO₂ and PM2.5 over time, one color per
  room, with gray reference marks:
  - Temperature: the comfortable band of the selected room (16-19 °C in a
    bedroom, 19-22 °C elsewhere).
  - Humidity: 40-60 %.
  - CO₂: a dashed line at 1000 ppm, "open a window".
  - PM2.5: a dashed line at 15 µg/m³, the WHO 24-hour guideline, on a
    logarithmic scale so cooking peaks do not flatten the everyday level.
- **Air purifier (STARKVIND):** fan mode and speed, the filter state, the fan
  speed over time, and the particles the purifier itself senses, aligned so a
  particle peak sits above the fan boost it causes.
- A `room` template variable to show one room or all.

Readings of exactly 0 °C, 0 % or 0 ppm are treated as "no reading" and show as
a gap: the hub reports 0 when a sensor drops out. When the hub stops answering,
the charts show a gap instead of the last value.

The air purifier section. The fan speed sits right above the particles the
purifier senses, so a particle peak lines up with the fan boost it causes:

<picture>
  <source media="(prefers-color-scheme: light)" srcset="docs/purifier-light.png">
  <img alt="Air purifier panels: fan mode and speed, filter state, fan speed over time and the particles the purifier senses" src="docs/purifier-dark.png" width="800">
</picture>

The screenshots use generated test data, not real sensor readings.

## Required metrics

Exported by [`dirigera-exporter`](https://github.com/Yornik/dirigera-exporter):
`ikea_air_temperature_celsius`, `ikea_air_humidity_percent`, `ikea_air_co2_ppm`,
`ikea_air_pm25_micrograms_per_cubic_meter`, and the `ikea_air_purifier_*` series.

## Import

1. Grafana → Dashboards → New → **Import**.
2. Upload `dashboard.json` (or paste its contents).
3. Select your Prometheus data source.

To provision it through the kube-prometheus-stack Grafana sidecar, wrap
`dashboard.json` in a `ConfigMap` labelled `grafana_dashboard: "1"`.

## Disclaimer & trademarks

Independent, unofficial project — **not** affiliated with, authorized, sponsored,
or endorsed by Inter IKEA Systems B.V. **IKEA®**, **DIRIGERA**, **STARKVIND**,
**VINDSTYRKA** and **ALPSTUGA** are trademarks of Inter IKEA Systems B.V., used
here solely for identification and descriptive purposes (nominative fair use).

## License

[MIT](LICENSE)
