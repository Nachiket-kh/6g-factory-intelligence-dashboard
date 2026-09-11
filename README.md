# 6G Factory Intelligence

An industrial analytics command center for studying the **Impact of 6G Network Performance on Manufacturing Efficiency in Smart Factories**.

## Features

- Executive KPI dashboard with calculated Factory Health
- Network performance, latency percentile, packet-loss, and machine analysis
- Manufacturing efficiency correlations calculated from the filtered data
- Quality and error-risk analysis with transparent thresholds
- Analytical predictive-maintenance and machine-health indicators
- 6G scenario estimate, machine explorer, data explorer, and CSV downloads
- Global date, machine, operation-mode, status, latency, and packet-loss filters

## Dataset and methodology

The included Thales manufacturing telemetry file contains 100,000 records. The app uses it by default and accepts compatible CSV uploads. Required columns are listed in `app.py`; uploads must also include `Time` or `Timestamp` with `Date`.

Derived indices are transparent: Network Stability combines latency and packet loss; Efficiency combines network, quality, and maintenance readiness; Factory Health is the mean of network stability, efficiency, and machine-health score. These are analytical indicators, not measured 6G outcomes or a trained failure-prediction model.

## Run locally

```powershell
py -m pip install -r requirements.txt
streamlit run app.py
```

## Deployment

The repository is Streamlit Community Cloud compatible. Create an app from this repository, select the `main` branch, and set the entry point to `app.py`. The committed `.streamlit/config.toml` defines the theme and upload limit.

## Project contents

- `app.py` - dashboard, validation, calculations, and visualizations
- `data/` - default manufacturing dataset
- `output/pdf/` - technical report
- `tests/` - processing and validation tests

## Limitations

The analysis identifies associations in the supplied telemetry; it does not establish causality. The 6G Optimization page labels its result as a scenario estimate and explains its linear-association assumption.
