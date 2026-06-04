import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Dashboard CR mySIKAP",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp { background: #f7f8fb; }
.block-container { padding-top: 1.1rem; padding-bottom: 2rem; max-width: 1500px; }
.dashboard-title { font-size: 1.35rem; font-weight: 800; color: #3f4a5f; margin-bottom: 1rem; }
.card { background: #ffffff; border: 1px solid #edf0f5; border-radius: 8px; padding: 1.1rem; box-shadow: 0 1px 4px rgba(20,24,40,.04); }
.kpi-big { min-height: 230px; display: flex; align-items: center; justify-content: center; text-align: center; }
.kpi-number { font-size: 3.1rem; line-height: 1; font-weight: 800; color: #4b556d; }
.kpi-label { font-size: .9rem; color: #3f4a5f; margin-top: .65rem; }
.rm-card { background: white; border: 1px solid #edf0f5; border-radius: 8px; padding: 1.05rem; text-align: center; box-shadow: 0 1px 4px rgba(20,24,40,.04); }
.rm-value { font-size: 2.15rem; line-height: 1; font-weight: 800; color: #657084; }
.rm-label { font-size: .82rem; color: #4b5563; margin-top: .45rem; font-weight: 600; }
.small-note { font-size: .78rem; color: #6b7280; text-align: center; margin-top: .35rem; margin-bottom: .35rem; }
[data-testid="stSidebar"] { background: #ffffff; }
div[data-testid="stPlotlyChart"] { background: white; border: 1px solid #edf0f5; border-radius: 8px; padding: .7rem; box-shadow: 0 1px 4px rgba(20,24,40,.04); }
</style>
""", unsafe_allow_html=True)

DEFAULT_DATA = Path(__file__).parent / "data.csv"
MONTH_MAP = {"jan":"Jan","feb":"Feb","mac":"Mar","mar":"Mar","apr":"Apr","mei":"May","may":"May","jun":"Jun","jul":"Jul","ogos":"Aug","aug":"Aug","sep":"Sep","sept":"Sep","okt":"Oct","oct":"Oct","nov":"Nov","dis":"Dec","dec":"Dec"}
STATUS_ORDER = ["BAHARU", "GUGUR", "PEMBANGUNAN", "SELESAI", "SIT", "SRS", "TPA", "UAT", "SDD", "DITANGGUHKAN"]

def normalize_date(value):
    if pd.isna(value): return pd.NaT
    text = str(value).strip()
    if text in {"", "-", "nan", "NaN"}: return pd.NaT
    for src, dst in MONTH_MAP.items():
        text = re.sub(src, dst, text, flags=re.IGNORECASE)
    return pd.to_datetime(text, errors="coerce", dayfirst=True)

def money_to_float(value):
    if pd.isna(value): return 0.0
    text = str(value).strip()
    if text in {"", "-", "nan", "NaN"}: return 0.0
    text = text.replace("RM", "").replace(",", "").strip()
    text = re.sub(r"[^0-9.\-]", "", text)
    try: return float(text) if text else 0.0
    except ValueError: return 0.0

@st.cache_data(show_spinner=False)
def load_data(source):
    df = pd.read_csv(source, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]
    expected_cols = ["Bil", "Bahagian", "Tarikh Permohonan", "CCB", "No. CCB", "Tajuk CR", "Status", "Nota", "On-Site", "Off-Site", "Kos (RM)"]
    for col in expected_cols:
        if col not in df.columns: df[col] = pd.NA
    df = df.dropna(how="all").copy()
    df["Bil"] = pd.to_numeric(df["Bil"], errors="coerce")
    df["Bahagian"] = df["Bahagian"].fillna("Tidak dinyatakan").astype(str).str.strip().replace({"":"Tidak dinyatakan", "nan":"Tidak dinyatakan"})
    df["CCB"] = df["CCB"].fillna("Tidak dinyatakan").astype(str).str.strip().replace({"":"Tidak dinyatakan", "nan":"Tidak dinyatakan"})
    df["Status"] = df["Status"].fillna("Tidak dinyatakan").astype(str).str.strip().str.upper().replace({"":"TIDAK DINYATAKAN", "NAN":"TIDAK DINYATAKAN"})
    df["No. CCB"] = df["No. CCB"].fillna("").astype(str).str.strip()
    df["Tajuk CR"] = df["Tajuk CR"].fillna("").astype(str).str.strip()
    df["Nota"] = df["Nota"].fillna("").astype(str).str.strip()
    df["Tarikh"] = df["Tarikh Permohonan"].apply(normalize_date)
    df["On-Site"] = pd.to_numeric(df["On-Site"], errors="coerce").fillna(0)
    df["Off-Site"] = pd.to_numeric(df["Off-Site"], errors="coerce").fillna(0)
    df["Total Mandays"] = df["On-Site"] + df["Off-Site"]
    df["Kos Numeric"] = df["Kos (RM)"].apply(money_to_float)
    return df

def rm(value): return f"RM{value:,.0f}"
def number(value): return f"{int(round(value)):,}" if abs(value - round(value)) < .001 else f"{value:,.1f}"

def clean_chart(fig, height=360):
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=15,r=15,t=55,b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(size=11,color="#4b5563"), title=dict(font=dict(size=13,color="#4b5563"), x=.5, xanchor="center"))
    fig.update_xaxes(showgrid=True, gridcolor="#eef2f7", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eef2f7", zeroline=False)
    return fig

def kpi_card(value, label, min_height=230):
    st.markdown(f"""<div class="card kpi-big" style="min-height:{min_height}px;"><div><div class="kpi-number">{value}</div><div class="kpi-label">{label}</div></div></div>""", unsafe_allow_html=True)

def rm_card(value, label):
    st.markdown(f"""<div class="rm-card"><div class="rm-value">{value}</div><div class="rm-label">Bahagian {label}</div></div>""", unsafe_allow_html=True)

st.markdown('<div class="dashboard-title">Dashboard CR mySIKAP</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Data & Filter")
    uploaded = st.file_uploader("Upload CSV lain", type=["csv"])
    data_source = uploaded if uploaded is not None else DEFAULT_DATA
    df = load_data(data_source)
    bahagian_options = sorted(df["Bahagian"].dropna().unique())
    status_options = sorted(df["Status"].dropna().unique())
    ccb_options = sorted(df["CCB"].dropna().unique())
    selected_bahagian = st.multiselect("Bahagian", bahagian_options, default=bahagian_options)
    selected_status = st.multiselect("Status", status_options, default=status_options)
    selected_ccb = st.multiselect("CCB", ccb_options, default=ccb_options)
    valid_dates = df["Tarikh"].dropna()
    if not valid_dates.empty:
        min_date = valid_dates.min().date(); max_date = valid_dates.max().date()
        date_range = st.date_input("Tarikh Permohonan", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    else:
        date_range = None

filtered = df[df["Bahagian"].isin(selected_bahagian) & df["Status"].isin(selected_status) & df["CCB"].isin(selected_ccb)].copy()
if date_range and isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered = filtered[(filtered["Tarikh"].isna()) | ((filtered["Tarikh"] >= start_date) & (filtered["Tarikh"] <= end_date))]

total_cr = len(filtered)
selesai = int((filtered["Status"] == "SELESAI").sum())
ongoing = max(total_cr - selesai, 0)

top_left, top_right = st.columns((1, 2.75), gap="small")
with top_left:
    kpi_card(f"{total_cr:,}", "Jumlah Permohonan CR Diluluskan", 240)
with top_right:
    bahagian_counts = filtered["Bahagian"].value_counts().rename_axis("Bahagian").reset_index(name="Bil Permohonan")
    fig_top = px.bar(bahagian_counts, x="Bahagian", y="Bil Permohonan", text_auto=True, title="Bilangan Permohonan CR Mengikut Bahagian")
    fig_top.update_traces(marker_color="#ffe59a", textposition="outside")
    fig_top.update_layout(xaxis_title="Bahagian", yaxis_title="Bil Permohonan")
    fig_top.update_xaxes(tickangle=-38)
    st.plotly_chart(clean_chart(fig_top, 240), use_container_width=True)

mid_left, mid_center, mid_right = st.columns((1.8, .9, 1), gap="small")
with mid_left:
    completion_data = pd.DataFrame({"Kategori":["Complete", "On-going"], "Bilangan":[selesai, ongoing]})
    fig_completion = px.pie(completion_data, names="Kategori", values="Bilangan", title="Completion Status", hole=.55)
    fig_completion.update_traces(textposition="inside", textinfo="percent+label+value")
    st.plotly_chart(clean_chart(fig_completion, 285), use_container_width=True)
with mid_center:
    st.markdown("##### Status CR")
    status_table = filtered["Status"].value_counts().rename_axis("Status CR").reset_index(name="Bilangan")
    status_table["Status CR"] = pd.Categorical(status_table["Status CR"], categories=STATUS_ORDER + [s for s in status_table["Status CR"] if s not in STATUS_ORDER], ordered=True)
    st.dataframe(status_table.sort_values("Status CR").astype({"Status CR": str}), use_container_width=True, hide_index=True, height=250)
with mid_right:
    kpi_card(f"{selesai:,}", "Jumlah CR Selesai", 285)

done_by_bahagian = filtered[filtered["Status"] == "SELESAI"].groupby("Bahagian", as_index=False).size().rename(columns={"size":"Bil CR Selesai"}).sort_values("Bil CR Selesai", ascending=True)
fig_done = px.bar(done_by_bahagian, x="Bil CR Selesai", y="Bahagian", orientation="h", text_auto=True, title="Bilangan CR Selesai Mengikut Bahagian")
fig_done.update_traces(marker_color="#bfe8e6", textposition="outside")
fig_done.update_layout(xaxis_title="Bil. CR Selesai", yaxis_title="Bahagian")
st.plotly_chart(clean_chart(fig_done, 300), use_container_width=True)

st.markdown('<div class="small-note">Jumlah Mandays On-Site dan Off-Site Mengikut Bahagian</div>', unsafe_allow_html=True)
st.markdown('<div class="small-note">Kos CR yang dilaksanakan secara on-site adalah termasuk dalam kontrak mySIKAP &nbsp;&nbsp;&nbsp;&nbsp; Kos bagi CR dilaksanakan secara off-site adalah sebanyak RM1,700.00 bagi 1 manday.</div>', unsafe_allow_html=True)

line_left, line_right = st.columns(2, gap="small")
mandays_by_bahagian = filtered.groupby("Bahagian", as_index=False)[["On-Site", "Off-Site"]].sum().sort_values("Bahagian")
with line_left:
    fig_on = px.line(mandays_by_bahagian, x="Bahagian", y="On-Site", markers=True, text="On-Site", title="Jumlah Mandays (On-Site) Mengikut Bahagian")
    fig_on.update_traces(line_color="#7586b7", marker_color="#7586b7", textposition="top center")
    fig_on.update_layout(xaxis_title="Bahagian", yaxis_title="Jumlah Days Onsite")
    fig_on.update_xaxes(tickangle=-38)
    st.plotly_chart(clean_chart(fig_on, 300), use_container_width=True)
with line_right:
    fig_off = px.line(mandays_by_bahagian, x="Bahagian", y="Off-Site", markers=True, text="Off-Site", title="Jumlah Mandays (Off-Site) Mengikut Bahagian")
    fig_off.update_traces(line_color="#f1919b", marker_color="#f1919b", textposition="top center")
    fig_off.update_layout(xaxis_title="Bahagian", yaxis_title="Jumlah Days Offsite")
    fig_off.update_xaxes(tickangle=-38)
    st.plotly_chart(clean_chart(fig_off, 300), use_container_width=True)

cost_by_bahagian = filtered.groupby("Bahagian", as_index=False)["Kos Numeric"].sum().sort_values("Kos Numeric", ascending=True)
fig_cost = px.bar(cost_by_bahagian, x="Kos Numeric", y="Bahagian", orientation="h", text_auto=".3s", title="Jumlah Kos (Off-Site) Mengikut Bahagian")
fig_cost.update_traces(marker_color="#cdb3df", textposition="outside")
fig_cost.update_layout(xaxis_title="Jumlah Kos (RM)", yaxis_title="Bahagian")
st.plotly_chart(clean_chart(fig_cost, 300), use_container_width=True)

top_cost = cost_by_bahagian.sort_values("Kos Numeric", ascending=False).head(6)
cols = st.columns(3, gap="small")
for i, row in enumerate(top_cost.itertuples(index=False)):
    with cols[i % 3]:
        rm_card(rm(row._1), row.Bahagian)

st.divider()
with st.expander("Senarai CR / data table", expanded=False):
    search = st.text_input("Search Tajuk CR / No. CCB / Nota")
    table = filtered.copy()
    if search:
        s = search.lower()
        table = table[table["Tajuk CR"].str.lower().str.contains(s, na=False) | table["No. CCB"].str.lower().str.contains(s, na=False) | table["Nota"].str.lower().str.contains(s, na=False)]
    show_cols = ["Bil", "Bahagian", "Tarikh Permohonan", "CCB", "No. CCB", "Tajuk CR", "Status", "Nota", "On-Site", "Off-Site", "Kos (RM)"]
    st.dataframe(table[show_cols], use_container_width=True, hide_index=True)
    csv = table[show_cols].to_csv(index=False).encode("utf-8-sig")
    st.download_button("Download filtered data", data=csv, file_name="filtered_cr_dashboard.csv", mime="text/csv")
