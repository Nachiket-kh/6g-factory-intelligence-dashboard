"""6G Factory Intelligence - analytics command center."""
from __future__ import annotations
import io
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

DATA = Path(__file__).parent / "data" / "Thales_Group_Manufacturing.csv"
REPORT = Path(__file__).parent / "output" / "pdf" / "6G_Factory_Intelligence_Technical_Report.pdf"
REQ = {"Date","Machine_ID","Operation_Mode","Temperature_C","Vibration_Hz","Power_Consumption_kW","Network_Latency_ms","Packet_Loss_%","Quality_Control_Defect_Rate_%","Production_Speed_units_per_hr","Predictive_Maintenance_Score","Error_Rate_%","Efficiency_Status"}
NUM = REQ-{ "Date","Machine_ID","Operation_Mode","Efficiency_Status" }
st.set_page_config("6G Factory Intelligence", "◈", "wide")
st.markdown("""<style>
:root{--ink:#10213e;--muted:#60708b;--blue:#2563eb;--navy:#0b1830;--line:#dce5f1}.stApp,[data-testid=stAppViewContainer]{background:#f4f7fb;color:var(--ink)}.block-container{max-width:1450px;padding-top:2rem}h1{font-size:2.45rem;font-weight:760;letter-spacing:-.05em}h1,h2,h3,p,label,[data-testid=stMarkdownContainer]{color:var(--ink)}[data-testid=stSidebar]{background:var(--navy)}[data-testid=stSidebar] *{color:#eff6ff}[data-testid=stSidebar] label{font-weight:650!important}[data-testid=stSidebar] [data-baseweb=input],[data-testid=stSidebar] [data-baseweb=select]>div,[data-testid=stSidebar] [data-testid=stDateInput] [data-baseweb=input]{background:#14294d!important;border-color:#48648e!important}[data-testid=stSidebar] input{background:transparent!important;color:#f8fbff!important;-webkit-text-fill-color:#f8fbff}[data-testid=stSidebar] [data-testid=stFileUploaderDropzone]{background:#14294d;border:1px dashed #5b7ead}[data-testid=stSidebar] [data-testid=stFileUploaderDropzone] *{color:#e7f0ff!important}[data-testid=stMetric]{background:#fff;border:1px solid var(--line);border-radius:14px;padding:15px;box-shadow:0 4px 14px #233e6c12}[data-baseweb=tab-list]{gap:.4rem;border-bottom:1px solid var(--line)}button[data-baseweb=tab]{color:#5f6f88;font-weight:650}.hero{background:linear-gradient(110deg,#0b1830,#173c7a 62%,#2563eb);border-radius:18px;padding:24px 29px;margin:0 0 1.35rem}.hero h2{color:#fff;margin:0}.hero p{color:#dbeafe}.insight{background:#fff;border:1px solid var(--line);border-left:4px solid #2563eb;border-radius:10px;padding:12px 14px;margin:7px 0;color:#223555}</style>""",unsafe_allow_html=True)
px.defaults.template="plotly_white"; px.defaults.color_discrete_sequence=["#2563eb","#0f9f9a","#8b5cf6","#e98c17"]

def validate_data(d:pd.DataFrame)->list[str]:
    out=[]; missing=REQ-set(d.columns)
    if missing: out.append("Missing required columns: "+", ".join(sorted(missing)))
    if not {"Time","Timestamp"}&set(d.columns): out.append("Include Time or Timestamp together with Date.")
    return out
@st.cache_data(show_spinner="Loading factory telemetry...")
def load_data(value:str|bytes)->pd.DataFrame: return pd.read_csv(io.BytesIO(value) if isinstance(value,bytes) else value)
def clean_data(d:pd.DataFrame)->pd.DataFrame:
    x=d.copy(); t="Timestamp" if "Timestamp" in x else "Time"
    x["Event_Time"]=pd.to_datetime(x.Date.astype(str)+" "+x[t].astype(str),dayfirst=True,errors="coerce")
    for c in NUM:x[c]=pd.to_numeric(x[c],errors="coerce")
    x.Machine_ID=x.Machine_ID.astype(str);x.Operation_Mode=x.Operation_Mode.astype(str);x.Efficiency_Status=x.Efficiency_Status.astype(str).str.title()
    return x.dropna(subset=["Event_Time"]).sort_values("Event_Time")
def enrich_data(x:pd.DataFrame)->pd.DataFrame:
    d=x.copy(); pm=d.Predictive_Maintenance_Score; d["Maintenance_Readiness"]=np.where(pm.max()<=1.5,pm*100,pm).clip(0,100)
    d["Network_Stability_Index"]=(100-d.Network_Latency_ms-8*d["Packet_Loss_%"]).clip(0,100)
    d["Efficiency_Index"]=(100-.45*d.Network_Latency_ms-5.2*d["Packet_Loss_%"]-1.9*d["Quality_Control_Defect_Rate_%"]+.14*d.Maintenance_Readiness).clip(0,100)
    d["Quality_Risk"]=pd.cut(d["Quality_Control_Defect_Rate_%"]+d["Error_Rate_%"],[-np.inf,5,12,np.inf],labels=["Low Risk","Medium Risk","High Risk"])
    health=.45*d.Maintenance_Readiness+.25*(100-d.Vibration_Hz.rank(pct=True)*100)+.15*(100-d.Temperature_C.rank(pct=True)*100)+.15*(100-d["Error_Rate_%"].rank(pct=True)*100)
    d["Machine_Health_Score"]=health.clip(0,100);d["Machine_Health"]=pd.cut(health,[-np.inf,35,55,75,np.inf],labels=["Critical","Maintenance Recommended","Watch","Healthy"])
    return d
def kpis(d:pd.DataFrame)->dict[str,float]:
    m=d.mean(numeric_only=True); h=np.mean([m.Network_Stability_Index,m.Efficiency_Index,m.Machine_Health_Score])
    return {"Network stability":m.Network_Stability_Index,"Average latency":m.Network_Latency_ms,"P95 latency":d.Network_Latency_ms.quantile(.95),"Packet loss":m["Packet_Loss_%"],"Production speed":m.Production_Speed_units_per_hr,"Efficiency":m.Efficiency_Index,"Defect rate":m["Quality_Control_Defect_Rate_%"],"Error rate":m["Error_Rate_%"],"Maintenance readiness":m.Maintenance_Readiness,"Factory Health":h}
def machine_metrics(d:pd.DataFrame)->pd.DataFrame:
    cols=["Network_Latency_ms","Packet_Loss_%","Production_Speed_units_per_hr","Efficiency_Index","Quality_Control_Defect_Rate_%","Error_Rate_%","Maintenance_Readiness","Temperature_C","Vibration_Hz","Power_Consumption_kW","Machine_Health_Score"]
    return d.groupby("Machine_ID",as_index=False)[cols].mean()
def line(d:pd.DataFrame,y,title): st.plotly_chart(px.line(d,x="Event_Time",y=y,title=title,labels={"Event_Time":"Date","value":"Value"}).update_layout(margin=dict(l=10,r=10,t=55,b=10),legend_title_text=""),width="stretch")
def insight(d:pd.DataFrame)->list[str]:
    a,b=d[d.Network_Latency_ms<15],d[d.Network_Latency_ms>30];out=[]
    if len(a)>10 and len(b)>10:out.append(f"Records below 15 ms average {a.Production_Speed_units_per_hr.mean()-b.Production_Speed_units_per_hr.mean():.1f} more units/hr than records above 30 ms.")
    out.append(f"Latency-to-efficiency Pearson correlation is {d.Network_Latency_ms.corr(d.Efficiency_Index):.2f}; this is observed association, not causation.")
    out.append(f"{(d.Quality_Risk=='High Risk').mean():.1%} of selected observations meet the stated High Quality Risk threshold.")
    return out
def main():
    st.title("6G Factory Intelligence");st.caption("Impact of 6G Network Performance on Manufacturing Efficiency in Smart Factories")
    st.markdown("<div class='hero'><h2>Smart factory command center</h2><p>Analyze how latency, packet loss and network stability influence production speed, quality, errors and machine health.</p></div>",unsafe_allow_html=True)
    with st.sidebar:
        st.header("Data & global filters"); up=st.file_uploader("Upload compatible telemetry CSV",type="csv")
        try: raw=load_data(up.getvalue()) if up else load_data(str(DATA))
        except FileNotFoundError:st.error("Default dataset is unavailable. Upload a CSV.");return
        errors=validate_data(raw)
        if errors:st.error("CSV cannot be used:\n\n"+"\n".join("- "+e for e in errors));return
        source=enrich_data(clean_data(raw));st.success(f"{'Uploaded' if up else 'Default Thales'} dataset: {len(source):,} valid records")
        dates=source.Event_Time.dt.date;dr=st.date_input("Date range",(dates.min(),dates.max()),min_value=dates.min(),max_value=dates.max())
        machines=st.multiselect("Machines",sorted(source.Machine_ID.unique(),key=lambda s:(len(s),s)),placeholder="All machines")
        modes=st.multiselect("Operation modes",sorted(source.Operation_Mode.unique()),placeholder="All operation modes")
        states=st.multiselect("Efficiency status",sorted(source.Efficiency_Status.unique()),placeholder="All statuses")
        lm=st.slider("Maximum latency (ms)",0.,float(np.ceil(source.Network_Latency_ms.max())),float(np.ceil(source.Network_Latency_ms.max())))
        pm=st.slider("Maximum packet loss (%)",0.,float(np.ceil(source["Packet_Loss_%"].max())),float(np.ceil(source["Packet_Loss_%"].max())))
        if st.button("Reset filters",width="stretch"):st.rerun()
    if len(dr)!=2:st.info("Select a complete date range.");return
    d=source[(source.Event_Time.dt.date.between(*dr))&(source.Network_Latency_ms<=lm)&(source["Packet_Loss_%"]<=pm)]
    if machines:d=d[d.Machine_ID.isin(machines)]
    if modes:d=d[d.Operation_Mode.isin(modes)]
    if states:d=d[d.Efficiency_Status.isin(states)]
    if d.empty:st.warning("No records match the active filters.");return
    st.caption(f"Active filters: {dr[0]} to {dr[1]} · {len(d):,} records")
    K=kpis(d);st.info(f"**Factory Health: {K['Factory Health']:.0f}/100.** Composite of observed network stability, efficiency and machine-health indicators.")
    specs=[("Network stability","/100"),("Average latency"," ms"),("P95 latency"," ms"),("Packet loss","%"),("Production speed"," units/hr"),("Efficiency","/100"),("Defect rate","%"),("Error rate","%"),("Maintenance readiness","/100")]
    for group in (specs[:5],specs[5:]):
        for c,(name,u) in zip(st.columns(len(group)),group):c.metric(name,f"{K[name]:.1f}{u}")
    tabs=st.tabs(["Executive overview","Network performance","Manufacturing efficiency","Quality & errors","Predictive maintenance","6G optimization","Machine explorer","Data explorer","About / methodology"])
    daily=d.set_index("Event_Time").resample("D").mean(numeric_only=True).reset_index();v=d.sample(min(5000,len(d)),random_state=42)
    with tabs[0]:
        st.subheader("Executive overview");c1,c2=st.columns((2,1));
        with c1:line(daily,["Network_Stability_Index","Efficiency_Index"],"Daily network stability and efficiency")
        with c2:st.plotly_chart(px.bar(d.Efficiency_Status.value_counts().rename_axis("Status").reset_index(name="Records"),x="Status",y="Records",color="Status",title="Efficiency status distribution"),width="stretch")
        for x in insight(d):st.markdown(f"<div class='insight'>{x}</div>",unsafe_allow_html=True)
    with tabs[1]:
        st.subheader("Network performance");c1,c2=st.columns(2)
        with c1:line(daily,"Network_Latency_ms","Daily average latency")
        with c2:line(daily,"Packet_Loss_%","Daily packet loss")
        c1,c2=st.columns(2)
        with c1:st.plotly_chart(px.histogram(d,x="Network_Latency_ms",nbins=40,title="Latency distribution"),width="stretch")
        with c2:st.plotly_chart(px.scatter(v,x="Network_Latency_ms",y="Packet_Loss_%",color="Operation_Mode",opacity=.65,title="Latency vs packet loss"),width="stretch")
        st.dataframe(d.Network_Latency_ms.quantile([.5,.75,.9,.95,.99]).rename("Latency (ms)").reset_index(names="Percentile"),hide_index=True,width="stretch");st.metric("High-latency events (>30 ms)",f"{(d.Network_Latency_ms>30).sum():,}")
    with tabs[2]:
        st.subheader("Manufacturing efficiency");c1,c2=st.columns(2)
        with c1:line(daily,["Production_Speed_units_per_hr","Efficiency_Index"],"Production speed and efficiency")
        with c2:st.plotly_chart(px.scatter(v,x="Network_Latency_ms",y="Production_Speed_units_per_hr",color="Operation_Mode",opacity=.65,title="Production speed vs latency"),width="stretch")
        corr=pd.DataFrame({"Relationship":["Latency ↔ Production Speed","Latency ↔ Efficiency","Packet Loss ↔ Production Speed","Packet Loss ↔ Defect Rate","Network Stability ↔ Efficiency"],"Correlation (Pearson r)":[d.Network_Latency_ms.corr(d.Production_Speed_units_per_hr),d.Network_Latency_ms.corr(d.Efficiency_Index),d["Packet_Loss_%"].corr(d.Production_Speed_units_per_hr),d["Packet_Loss_%"].corr(d["Quality_Control_Defect_Rate_%"]),d.Network_Stability_Index.corr(d.Efficiency_Index)]});st.dataframe(corr.style.format({"Correlation (Pearson r)":"{:.3f}"}),hide_index=True,width="stretch")
    with tabs[3]:
        st.subheader("Quality & errors");st.caption("Quality Risk: Low ≤5%, Medium 5-12%, High >12% for defect rate + error rate.");c1,c2=st.columns(2)
        with c1:line(daily,["Quality_Control_Defect_Rate_%","Error_Rate_%"],"Defect and error trend")
        with c2:st.plotly_chart(px.scatter(v,x="Packet_Loss_%",y="Quality_Control_Defect_Rate_%",color="Quality_Risk",opacity=.65,title="Packet loss vs defect rate"),width="stretch")
    with tabs[4]:
        st.subheader("Predictive maintenance");st.caption("Analytical risk indicator only; it is not a trained failure prediction model.");m=machine_metrics(d);c1,c2=st.columns(2)
        with c1:st.plotly_chart(px.bar(m,x="Machine_ID",y="Maintenance_Readiness",color="Maintenance_Readiness",title="Maintenance readiness by machine"),width="stretch")
        with c2:st.plotly_chart(px.scatter(v,x="Vibration_Hz",y="Maintenance_Readiness",color="Machine_Health",opacity=.65,title="Vibration vs maintenance readiness"),width="stretch")
    with tabs[5]:
        st.subheader("6G optimization");st.caption("Scenario Estimate based on simple observed linear associations; not a measured real-world 6G result.");c1,c2=st.columns(2);tl=c1.selectbox("Target latency",[10.,15.,20.],index=1);pl=c2.selectbox("Target packet loss",[.1,.25,.5],index=1)
        bl=d.Production_Speed_units_per_hr.corr(d.Network_Latency_ms)*d.Production_Speed_units_per_hr.std()/max(d.Network_Latency_ms.std(),1e-9);bp=d.Production_Speed_units_per_hr.corr(d["Packet_Loss_%"])*d.Production_Speed_units_per_hr.std()/max(d["Packet_Loss_%"].std(),1e-9);est=d.Production_Speed_units_per_hr.mean()+bl*(tl-d.Network_Latency_ms.mean())+bp*(pl-d["Packet_Loss_%"].mean());st.info(f"Scenario Estimate: target {tl:.0f} ms and {pl:.2f}% gives estimated average production speed of **{est:.1f} units/hr** if observed relationships remain linear and other conditions are constant.")
        m=machine_metrics(d);m["Risk Level"]=np.select([m.Network_Latency_ms>30,m["Packet_Loss_%"]>2],["High","Medium"],default="Low");m["Recommended Network Action"]=np.where(m["Risk Level"].eq("High"),"Prioritize low-latency slice",np.where(m["Risk Level"].eq("Medium"),"Investigate packet loss","Continue monitoring"));st.dataframe(m[["Machine_ID","Network_Latency_ms","Packet_Loss_%","Efficiency_Index","Risk Level","Recommended Network Action"]],hide_index=True,width="stretch")
    with tabs[6]:
        st.subheader("Machine explorer");mid=st.selectbox("Select a machine",sorted(d.Machine_ID.unique(),key=lambda s:(len(s),s)));x=d[d.Machine_ID.eq(mid)];r=machine_metrics(x).iloc[0]
        for c,(n,u) in zip(st.columns(5),[("Machine_Health_Score","/100"),("Network_Latency_ms"," ms"),("Packet_Loss_%","%"),("Production_Speed_units_per_hr"," units/hr"),("Efficiency_Index","/100")]):c.metric(n,f"{r[n]:.1f}{u}")
        line(x.set_index("Event_Time").resample("D").mean(numeric_only=True).reset_index(),["Network_Latency_ms","Efficiency_Index"],f"Machine {mid}: latency and efficiency")
        st.markdown(f"<div class='insight'>{'Prioritize low-latency connectivity.' if r.Network_Latency_ms>30 else 'Continue routine monitoring; selected average latency is within the project warning threshold.'}</div>",unsafe_allow_html=True)
    with tabs[7]:
        st.subheader("Data explorer");st.write(f"**Records:** {len(d):,} | **Missing values:** {int(d.isna().sum().sum()):,}");st.dataframe(d.head(1000),width="stretch",hide_index=True,height=420);c1,c2,c3=st.columns(3);c1.download_button("Download filtered dataset",d.to_csv(index=False),"filtered_factory_telemetry.csv");c2.download_button("Download machine summary",machine_metrics(d).to_csv(index=False),"machine_summary.csv");c3.download_button("Download KPI summary",pd.DataFrame([K]).to_csv(index=False),"kpi_summary.csv")
    with tabs[8]:
        st.subheader("About / methodology");st.markdown("**Network Stability Index:** `100 - latency (ms) - 8 × packet loss (%)`. **Efficiency Index:** `100 - 0.45 × latency - 5.2 × packet loss - 1.9 × defect rate + 0.14 × maintenance readiness`. **Factory Health:** mean of network stability, efficiency, and machine health.\n\nThis is observational data analysis. Correlation does not establish causation. Scenario estimates are explicitly not measured 6G performance.")
        if REPORT.exists():st.download_button("Download technical report",REPORT.read_bytes(),REPORT.name,"application/pdf")
if __name__=="__main__":main()

