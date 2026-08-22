"""6G network performance and manufacturing efficiency dashboard."""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(page_title="Unified Mentor | 6G Factory Analytics", page_icon="◈", layout="wide")
st.markdown("""
<style>
  .stApp { background: #f7f9fc; }
  h1 { color: #14213d; letter-spacing: -0.04em; }
  [data-testid="stMetric"] { background: #fff; border: 1px solid #e5eaf2; border-radius: 12px; padding: 14px; }
  [data-testid="stSidebar"] { background: #fff; }
</style>
""", unsafe_allow_html=True)

REQUIRED_COLUMNS = {
    "Date", "Machine_ID", "Operation_Mode", "Temperature_C",
    "Vibration_Hz", "Power_Consumption_kW", "Network_Latency_ms",
    "Packet_Loss_%", "Quality_Control_Defect_Rate_%", "Production_Speed_units_per_hr",
    "Predictive_Maintenance_Score", "Error_Rate_%", "Efficiency_Status",
}
DEFAULT_DATASET = Path(__file__).parent / "data" / "Thales_Group_Manufacturing.csv"


@st.cache_data(show_spinner=False)
def demo_data(rows: int = 10080) -> pd.DataFrame:
    """Create an hourly, 12-week factory telemetry sample."""
    rng = np.random.default_rng(6)
    timestamp = pd.date_range("2026-05-25", periods=rows, freq="h")
    machines = np.array([f"M-{i:02}" for i in range(1, 13)])
    machine = rng.choice(machines, rows)
    mode = rng.choice(["Precision", "Standard", "High Output"], rows, p=[.28, .50, .22])
    hour = timestamp.hour.to_numpy()
    congestion = np.maximum(0, np.sin((hour - 9) * np.pi / 12))
    incident = rng.binomial(1, .035, rows)
    latency = np.clip(9 + 12 * congestion + 34 * incident + rng.normal(0, 3, rows), 2, None)
    loss = np.clip(.08 + .018 * latency + .55 * incident + rng.normal(0, .06, rows), 0, 8)
    vibration = np.clip(34 + rng.normal(0, 7, rows) + 10 * incident, 8, None)
    maintenance = np.clip(86 - .6 * vibration + rng.normal(0, 8, rows), 0, 100)
    defect = np.clip(.55 + .04 * latency + .09 * loss + .012 * vibration + rng.normal(0, .25, rows), .05, 12)
    error = np.clip(.16 + .02 * latency + .19 * loss + rng.normal(0, .13, rows), .01, 15)
    speed_base = np.select([mode == "Precision", mode == "High Output"], [74, 128], default=100)
    speed = np.clip(speed_base - .72 * latency - 4.8 * loss - .42 * defect + rng.normal(0, 5, rows), 20, 160)
    efficiency = np.clip(100 - .45 * latency - 5.2 * loss - 1.9 * defect + .14 * maintenance + rng.normal(0, 4, rows), 0, 100)
    status = np.where(efficiency >= 88, "High", np.where(efficiency >= 72, "Medium", "Low"))
    return pd.DataFrame({
        "Date": timestamp.date.astype(str), "Time": timestamp.time.astype(str), "Machine_ID": machine,
        "Operation_Mode": mode, "Temperature_C": np.round(rng.normal(63, 5, rows), 1),
        "Vibration_Hz": np.round(vibration, 2), "Power_Consumption_kW": np.round(80 + speed * .42 + rng.normal(0, 5, rows), 2),
        "Network_Latency_ms": np.round(latency, 2), "Packet_Loss_%": np.round(loss, 3),
        "Quality_Control_Defect_Rate_%": np.round(defect, 3), "Production_Speed_units_per_hr": np.round(speed, 1),
        "Predictive_Maintenance_Score": np.round(maintenance, 1), "Error_Rate_%": np.round(error, 3),
        "Efficiency_Status": status,
    })


def load_data(file) -> pd.DataFrame:
    if file is None and not DEFAULT_DATASET.exists():
        return demo_data()
    frame = pd.read_csv(file if file is not None else DEFAULT_DATASET)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
    if not ({"Time", "Timestamp"} & set(frame.columns)):
        raise ValueError("Missing a time column: provide either Time or Timestamp.")
    return frame


def enrich(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    time_column = "Timestamp" if "Timestamp" in data.columns else "Time"
    data["Timestamp"] = pd.to_datetime(
        data["Date"].astype(str) + " " + data[time_column].astype(str), errors="coerce", dayfirst=True
    )
    numeric = REQUIRED_COLUMNS - {"Date", "Machine_ID", "Operation_Mode", "Efficiency_Status"}
    for column in numeric:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data["Efficiency_Index"] = (100 - .45 * data["Network_Latency_ms"] - 5.2 * data["Packet_Loss_%"]
                                - 1.9 * data["Quality_Control_Defect_Rate_%"] + .14 * data["Predictive_Maintenance_Score"]).clip(0, 100)
    data["Network_Stability_Index"] = (100 - data["Network_Latency_ms"] - 8 * data["Packet_Loss_%"]).clip(0, 100)
    data["Latency_Band"] = pd.cut(data["Network_Latency_ms"], [-np.inf, 15, 30, np.inf], labels=["Low", "Medium", "High"])
    return data.dropna(subset=["Timestamp"])


def metric(label: str, value: str, delta: str | None = None) -> None:
    st.metric(label, value, delta, border=True)


st.title("6G Factory Intelligence")
st.caption("Network performance, manufacturing efficiency, and quality insight in one operational view.")

with st.sidebar:
    st.header("Data & filters")
    upload = st.file_uploader("Upload factory telemetry CSV", type="csv", help="Use the field names listed in the project brief.")
    try:
        source = enrich(load_data(upload))
    except ValueError as error:
        st.error(str(error))
        st.stop()
    if upload is not None:
        st.caption(f"Loaded upload: {len(source):,} records")
    elif DEFAULT_DATASET.exists():
        st.caption(f"Using Thales manufacturing data: {len(source):,} records")
    else:
        st.caption("Using demo telemetry")
    dates = source["Timestamp"].dt.date
    selected_dates = st.date_input("Date range", value=(dates.min(), dates.max()), min_value=dates.min(), max_value=dates.max())
    machines = st.multiselect("Machines", sorted(source["Machine_ID"].unique()), default=sorted(source["Machine_ID"].unique()))
    modes = st.multiselect("Operation modes", sorted(source["Operation_Mode"].unique()), default=sorted(source["Operation_Mode"].unique()))
    latency_limit = st.slider("Maximum latency (ms)", 10, int(np.ceil(source["Network_Latency_ms"].max())), int(np.ceil(source["Network_Latency_ms"].max())))

if len(selected_dates) != 2:
    st.info("Select a start and end date to view the dashboard.")
    st.stop()
start, end = pd.Timestamp(selected_dates[0]).date(), pd.Timestamp(selected_dates[1]).date()
data = source[(source["Timestamp"].dt.date.between(start, end)) & source["Machine_ID"].isin(machines) & source["Operation_Mode"].isin(modes) & (source["Network_Latency_ms"] <= latency_limit)]
if data.empty:
    st.warning("No records match these filters.")
    st.stop()

overview, efficiency, quality, optimize = st.tabs(["Network overview", "Efficiency analysis", "Quality & errors", "6G optimization"])

with overview:
    a, b, c, d = st.columns(4)
    metric("Network stability", f"{data['Network_Stability_Index'].mean():.1f}/100", "Target ≥ 85")
    metric("Average latency", f"{data['Network_Latency_ms'].mean():.1f} ms", f"P95 {data['Network_Latency_ms'].quantile(.95):.1f} ms")
    metric("Packet loss", f"{data['Packet_Loss_%'].mean():.2f}%", "Target < 0.50%")
    metric("High-efficiency output", f"{(data['Efficiency_Status'] == 'High').mean():.0%}", f"{len(data):,} observations")
    trend = data.set_index("Timestamp").resample("D").agg({"Network_Latency_ms": "mean", "Packet_Loss_%": "mean", "Network_Stability_Index": "mean"}).reset_index()
    left, right = st.columns((2, 1))
    with left:
        fig = px.line(trend, x="Timestamp", y=["Network_Stability_Index", "Network_Latency_ms"], markers=True, labels={"value": "Score / milliseconds", "variable": "Metric"}, title="Daily network health")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        bands = data["Latency_Band"].value_counts().rename_axis("Latency band").reset_index(name="Observations")
        st.plotly_chart(px.pie(bands, names="Latency band", values="Observations", hole=.58, title="Latency distribution", color="Latency band", color_discrete_map={"Low":"#22c55e","Medium":"#f59e0b","High":"#ef4444"}), use_container_width=True)
    st.dataframe(data[["Timestamp", "Machine_ID", "Operation_Mode", "Network_Latency_ms", "Packet_Loss_%", "Efficiency_Status"]].sort_values("Timestamp", ascending=False).head(20), use_container_width=True, hide_index=True)

with efficiency:
    a, b, c = st.columns(3)
    metric("Mean efficiency index", f"{data['Efficiency_Index'].mean():.1f}/100")
    metric("Production speed", f"{data['Production_Speed_units_per_hr'].mean():.1f} units/hr")
    metric("Defect rate", f"{data['Quality_Control_Defect_Rate_%'].mean():.2f}%")
    left, right = st.columns(2)
    with left:
        fig = px.scatter(data, x="Network_Latency_ms", y="Production_Speed_units_per_hr", color="Operation_Mode", size="Efficiency_Index", hover_data=["Machine_ID", "Packet_Loss_%"], title="Production speed declines as latency rises", opacity=.65)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        by_mode = data.groupby("Operation_Mode", as_index=False).agg(Efficiency_Index=("Efficiency_Index", "mean"), Production_Speed_units_per_hr=("Production_Speed_units_per_hr", "mean"))
        st.plotly_chart(px.bar(by_mode, x="Operation_Mode", y="Efficiency_Index", color="Operation_Mode", title="Efficiency by operation mode", range_y=[0, 100]), use_container_width=True)
    matrix = data[["Network_Latency_ms", "Packet_Loss_%", "Quality_Control_Defect_Rate_%", "Production_Speed_units_per_hr", "Efficiency_Index"]].corr().round(2)
    st.subheader("Relationship matrix")
    st.plotly_chart(px.imshow(matrix, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1), use_container_width=True)

with quality:
    a, b, c = st.columns(3)
    metric("Error rate", f"{data['Error_Rate_%'].mean():.2f}%")
    metric("Defect rate", f"{data['Quality_Control_Defect_Rate_%'].mean():.2f}%")
    metric("At-risk machines", str(data.groupby("Machine_ID")["Predictive_Maintenance_Score"].mean().lt(60).sum()))
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.scatter(data, x="Packet_Loss_%", y="Quality_Control_Defect_Rate_%", color="Latency_Band", hover_data=["Machine_ID", "Error_Rate_%"], title="Packet loss impact on quality", color_discrete_map={"Low":"#22c55e","Medium":"#f59e0b","High":"#ef4444"}), use_container_width=True)
    with right:
        ranked = data.groupby("Machine_ID", as_index=False).agg(Error_Rate=("Error_Rate_%", "mean"), Defect_Rate=("Quality_Control_Defect_Rate_%", "mean"), Maintenance_Score=("Predictive_Maintenance_Score", "mean")).sort_values("Error_Rate", ascending=False)
        st.plotly_chart(px.bar(ranked, x="Machine_ID", y=["Error_Rate", "Defect_Rate"], barmode="group", title="Error and defect rates by machine"), use_container_width=True)
    st.dataframe(ranked.style.format({"Error_Rate":"{:.2f}%", "Defect_Rate":"{:.2f}%", "Maintenance_Score":"{:.1f}"}), use_container_width=True, hide_index=True)

with optimize:
    high_latency = data[data["Network_Latency_ms"] > data["Network_Latency_ms"].quantile(.9)]
    impact = data.groupby("Latency_Band", observed=False).agg(Efficiency=("Efficiency_Index", "mean"), Speed=("Production_Speed_units_per_hr", "mean"), Defects=("Quality_Control_Defect_Rate_%", "mean")).round(1)
    avoidable = max(0, data["Efficiency_Index"].mean() - high_latency["Efficiency_Index"].mean()) if not high_latency.empty else 0
    st.subheader("Recommended operating actions")
    cards = st.columns(3)
    cards[0].info(f"**Protect low-latency production**\n\nHigh-latency events cost an estimated **{avoidable:.1f} efficiency points**. Prioritize network slices for precision lines.")
    cards[1].warning(f"**Investigate packet loss zones**\n\n{(data['Packet_Loss_%'] > 0.5).mean():.0%} of selected telemetry exceeds the 0.5% packet-loss guardrail.")
    cards[2].success(f"**Schedule predictive maintenance**\n\n{(data['Predictive_Maintenance_Score'] < 60).sum():,} records show maintenance risk before it becomes an unplanned stop.")
    st.subheader("Expected impact by latency band")
    st.dataframe(impact.style.format("{:.1f}"), use_container_width=True)
    export = io.StringIO()
    data.drop(columns=["Timestamp"]).to_csv(export, index=False)
    st.download_button("Download filtered data", export.getvalue(), "filtered_factory_telemetry.csv", "text/csv")
