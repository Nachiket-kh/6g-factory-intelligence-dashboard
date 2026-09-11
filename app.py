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
  :root { --ink: #10213e; --muted: #5d6d86; --blue: #2563eb; --navy: #0b1830; --line: #dce5f1; }
  .stApp, [data-testid="stAppViewContainer"] { background: #f4f7fb; color: var(--ink); }
  .block-container { max-width: 1440px; padding-top: 2.15rem; padding-bottom: 3rem; }
  h1, h2, h3, p, label, [data-testid="stMarkdownContainer"] { color: var(--ink); }
  h1 { font-size: 2.35rem; font-weight: 760; letter-spacing: -.045em; margin-bottom: .1rem; }
  h2, h3 { letter-spacing: -.02em; }
  [data-testid="stCaptionContainer"] { color: var(--muted); }
  [data-testid="stSidebar"] { background: var(--navy); border-right: 1px solid #203a63; }
  [data-testid="stSidebar"] * { color: #f2f7ff; }
  [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #bfd0ed; }
  [data-testid="stSidebar"] label { color: #f2f7ff !important; font-weight: 650; }
  [data-testid="stSidebar"] input, [data-testid="stSidebar"] input::placeholder,
  [data-testid="stSidebar"] [data-baseweb="input"] input,
  [data-testid="stSidebar"] [data-baseweb="select"] > div { background: #14294d; color: #f8fbff !important; border-color: #48648e; }
  [data-testid="stSidebar"] [data-baseweb="input"],
  [data-testid="stSidebar"] [data-baseweb="select"] > div { background: #14294d !important; border-color: #48648e !important; }
  [data-testid="stSidebar"] [data-testid="stDateInput"] [data-baseweb="input"] { background: #14294d !important; border-color: #48648e !important; }
  [data-testid="stSidebar"] [data-testid="stDateInput"] input { background: transparent !important; color: #f8fbff !important; -webkit-text-fill-color: #f8fbff; }
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] { background: #14294d; border: 1px dashed #5b7ead; }
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] *,
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] * { color: #e7f0ff !important; }
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button { background: #2563eb; color: #fff !important; border: 0; }
  [data-testid="stSidebar"] [data-baseweb="slider"] [role="slider"] { background: #60a5fa; }
  [data-testid="stSidebar"] svg { fill: #dbeafe; }
  [data-testid="stSidebar"] [data-baseweb="tag"] { background: #2563eb; }
  [data-testid="stMetric"] { background: white; border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px; box-shadow: 0 4px 15px rgba(35, 62, 108, .06); }
  [data-testid="stMetricLabel"] { color: var(--muted); font-size: .84rem; font-weight: 650; }
  [data-testid="stMetricValue"] { color: var(--ink); font-weight: 750; }
  [data-testid="stMetricDelta"] { font-weight: 650; }
  [data-baseweb="tab-list"] { gap: .55rem; border-bottom: 1px solid var(--line); }
  button[data-baseweb="tab"] { color: #5f6f88; font-weight: 650; padding: .7rem 1rem; }
  button[data-baseweb="tab"][aria-selected="true"] { color: #1d4ed8; border-bottom-color: #2563eb; }
  [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
  [data-testid="stDownloadButton"] button { background: #2563eb; color: white; border: 0; border-radius: 8px; font-weight: 650; }
  .hero { background: linear-gradient(115deg, #0b1830 0%, #173c7a 58%, #2563eb 100%); border-radius: 18px; padding: 25px 30px; margin: 0 0 1.5rem; box-shadow: 0 13px 30px rgba(24, 55, 108, .16); }
  .hero h2 { color: white; margin: 0; font-size: 1.35rem; }
  .hero p { color: #dbeafe; margin: .45rem 0 0; font-size: .98rem; }
</style>
""", unsafe_allow_html=True)

px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = ["#2563eb", "#0f9f9a", "#8b5cf6", "#e98c17", "#db3f87"]

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
st.caption("Operational analytics for network performance, manufacturing efficiency, and product quality.")
st.markdown("""
<div class="hero">
  <h2>Connected factory command center</h2>
  <p>Spot network conditions that reduce output, increase defects, or create maintenance risk - before they become downtime.</p>
</div>
""", unsafe_allow_html=True)

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
    machines = st.multiselect("Machines", sorted(source["Machine_ID"].unique()), placeholder="All machines")
    modes = st.multiselect("Operation modes", sorted(source["Operation_Mode"].unique()), placeholder="All operation modes")
    st.caption("Leave machine and mode filters blank to include all data.")
    latency_limit = st.slider("Maximum latency (ms)", 10, int(np.ceil(source["Network_Latency_ms"].max())), int(np.ceil(source["Network_Latency_ms"].max())))

if len(selected_dates) != 2:
    st.info("Select a start and end date to view the dashboard.")
    st.stop()
start, end = pd.Timestamp(selected_dates[0]).date(), pd.Timestamp(selected_dates[1]).date()
machine_filter = machines or source["Machine_ID"].unique()
mode_filter = modes or source["Operation_Mode"].unique()
data = source[(source["Timestamp"].dt.date.between(start, end)) & source["Machine_ID"].isin(machine_filter) & source["Operation_Mode"].isin(mode_filter) & (source["Network_Latency_ms"] <= latency_limit)]
if data.empty:
    st.warning("No records match these filters.")
    st.stop()

# Use all selected data for calculations, and a fixed representative sample only
# for point charts so the page remains quick with the 100,000-row data set.
chart_data = data.sample(n=min(5_000, len(data)), random_state=42)

overview, efficiency, quality, optimize = st.tabs(["Network overview", "Efficiency analysis", "Quality & errors", "6G optimization"])

with overview:
    a, b, c, d = st.columns(4)
    with a: metric("Network stability", f"{data['Network_Stability_Index'].mean():.1f}/100", "Target >= 85")
    with b: metric("Average latency", f"{data['Network_Latency_ms'].mean():.1f} ms", f"P95 {data['Network_Latency_ms'].quantile(.95):.1f} ms")
    with c: metric("Packet loss", f"{data['Packet_Loss_%'].mean():.2f}%", "Target < 0.50%")
    with d: metric("High-efficiency output", f"{(data['Efficiency_Status'] == 'High').mean():.0%}", f"{len(data):,} observations")
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
    with a: metric("Mean efficiency index", f"{data['Efficiency_Index'].mean():.1f}/100")
    with b: metric("Production speed", f"{data['Production_Speed_units_per_hr'].mean():.1f} units/hr")
    with c: metric("Defect rate", f"{data['Quality_Control_Defect_Rate_%'].mean():.2f}%")
    left, right = st.columns(2)
    with left:
        fig = px.scatter(chart_data, x="Network_Latency_ms", y="Production_Speed_units_per_hr", color="Operation_Mode", size="Efficiency_Index", hover_data=["Machine_ID", "Packet_Loss_%"], title="Production speed declines as latency rises", opacity=.72)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        by_mode = data.groupby("Operation_Mode", as_index=False).agg(Efficiency_Index=("Efficiency_Index", "mean"), Production_Speed_units_per_hr=("Production_Speed_units_per_hr", "mean"))
        st.plotly_chart(px.bar(by_mode, x="Operation_Mode", y="Efficiency_Index", color="Operation_Mode", title="Efficiency by operation mode", range_y=[0, 100]), use_container_width=True)
    matrix = data[["Network_Latency_ms", "Packet_Loss_%", "Quality_Control_Defect_Rate_%", "Production_Speed_units_per_hr", "Efficiency_Index"]].corr().round(2)
    st.subheader("Relationship matrix")
    st.plotly_chart(px.imshow(matrix, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1), use_container_width=True)

with quality:
    a, b, c = st.columns(3)
    with a: metric("Error rate", f"{data['Error_Rate_%'].mean():.2f}%")
    with b: metric("Defect rate", f"{data['Quality_Control_Defect_Rate_%'].mean():.2f}%")
    with c: metric("At-risk machines", str(data.groupby("Machine_ID")["Predictive_Maintenance_Score"].mean().lt(60).sum()))
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.scatter(chart_data, x="Packet_Loss_%", y="Quality_Control_Defect_Rate_%", color="Latency_Band", hover_data=["Machine_ID", "Error_Rate_%"], title="Packet loss impact on quality", opacity=.72, color_discrete_map={"Low":"#16a34a","Medium":"#d97706","High":"#dc2626"}), use_container_width=True)
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
