# 6G Factory Intelligence Dashboard

A Streamlit implementation of the **Impact of 6G Network Performance on Manufacturing Efficiency in Smart Factories** brief.

## Run it

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

The supplied **Thales Group Manufacturing** dataset is included as the default source (100,000 records). Upload a CSV to replace it. If the local dataset is removed, the application falls back to a realistic deterministic demo data set. Uploaded data must contain the following fields:

`Date`, `Machine_ID`, `Operation_Mode`, `Temperature_C`, `Vibration_Hz`, `Power_Consumption_kW`, `Network_Latency_ms`, `Packet_Loss_%`, `Quality_Control_Defect_Rate_%`, `Production_Speed_units_per_hr`, `Predictive_Maintenance_Score`, `Error_Rate_%`, and `Efficiency_Status`, plus either `Time` or `Timestamp` for the time component.

## Included analysis

- Network stability, latency, and packet-loss monitoring
- Efficiency and production-speed impact analysis
- Quality/error diagnostics and maintenance risk ranking
- Filterable machine, operation mode, and time-window controls
- Data export and 6G-oriented optimization recommendations
