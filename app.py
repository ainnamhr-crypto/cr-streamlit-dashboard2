import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="CR Dashboard peace",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main {
    background-color: #f7f9fc;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.kpi-card {
    background: white;
    padding: 1.2rem;
    border-radius: 16px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    border: 1px solid #eef1f5;
}

.kpi-label {
    font-size: 0.85rem;
    color: #6b7280;
    margin-bottom: 0.3rem;
}

.kpi-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #111827;
}
</style>
""", unsafe_allow_html=True)

DEFAULT_DATA = Path(__file__).parent / "data.csv"

MONTH_MAP = {
    "jan": "Jan", "feb": "Feb", "mac": "Mar", "mar": "Mar", "apr": "Apr", "mei": "May", "may": "May",
    "jun": "Jun", "jul": "Jul", "ogos": "Aug", "aug": "Aug", "sep": "Sep", "sept": "Sep", "okt": "Oct",
    "oct": "Oct", "nov": "Nov", "dis": "Dec", "dec": "Dec",
}

STATUS_ORDER = [
    "BAHARU", "TPA", "SRS", "SDD", "SIT", "UAT", "PEMBANGUNAN", "DITANGGUHKAN", "GUGUR", "SELESAI"
]


def normalize_date(value):
    if pd.isna(value):
        return pd.NaT
    text = str(value).strip()
    if text in {"", "-", "nan", "NaN"}:
        return pd.NaT
    # Normalize Malay month abbreviations if any appear later.
    for src, dst in MONTH_MAP.items():
        text = re.sub(src, dst, text, flags=re.IGNORECASE)
    return pd.to_datetime(text, errors="coerce", dayfirst=True)


def money_to_float(value):
    if pd.isna(value):
        return 0.0
    text = str(value).strip()
    if text in {"", "-", "nan", "NaN"}:
        return 0.0
    text = text.replace("RM", "").replace(",", "").strip()
    text = re.sub(r"[^0-9.\-]", "", text)
    try:
        return float(text) if text else 0.0
    except ValueError:
        return 0.0


@st.cache_data(show_spinner=False)
def load_data(source):
    df = pd.read_csv(source, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]

    expected_cols = ["Bil", "Bahagian", "Tarikh Permohonan", "CCB", "No. CCB", "Tajuk CR", "Status", "Nota", "On-Site", "Off-Site", "Kos (RM)"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = pd.NA

    df = df.dropna(how="all").copy()
    df["Bil"] = pd.to_numeric(df["Bil"], errors="coerce")
    df["Bahagian"] = df["Bahagian"].fillna("Tidak dinyatakan").astype(str).str.strip().replace({"": "Tidak dinyatakan", "nan": "Tidak dinyatakan"})
    df["CCB"] = df["CCB"].fillna("Tidak dinyatakan").astype(str).str.strip().replace({"": "Tidak dinyatakan", "nan": "Tidak dinyatakan"})
    df["Status"] = df["Status"].fillna("Tidak dinyatakan").astype(str).str.strip().str.upper().replace({"": "TIDAK DINYATAKAN", "NAN": "TIDAK DINYATAKAN"})
    df["No. CCB"] = df["No. CCB"].fillna("").astype(str).str.strip()
    df["Tajuk CR"] = df["Tajuk CR"].fillna("").astype(str).str.strip()
    df["Nota"] = df["Nota"].fillna("").astype(str).str.strip()
    df["Tarikh"] = df["Tarikh Permohonan"].apply(normalize_date)
    df["Tahun"] = df["Tarikh"].dt.year
    df["Bulan"] = df["Tarikh"].dt.to_period("M").astype(str).replace("NaT", "Tidak dinyatakan")
    df["On-Site"] = pd.to_numeric(df["On-Site"], errors="coerce").fillna(0)
    df["Off-Site"] = pd.to_numeric(df["Off-Site"], errors="coerce").fillna(0)
    df["Total Mandays"] = df["On-Site"] + df["Off-Site"]
    df["Kos Numeric"] = df["Kos (RM)"].apply(money_to_float)
    return df


def rm(value):
    return f"RM {value:,.2f}"


def number(value):
    if abs(value - round(value)) < 0.001:
        return f"{int(round(value)):,}"
    return f"{value:,.1f}"


st.title("📊 CR Dashboard Prototype")
st.caption("Prototype visualization untuk data Change Request. Upload CSV baru di sidebar untuk test versi data lain.")

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
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()
        date_range = st.date_input("Tarikh Permohonan", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    else:
        date_range = None

filtered = df[
    df["Bahagian"].isin(selected_bahagian)
    & df["Status"].isin(selected_status)
    & df["CCB"].isin(selected_ccb)
].copy()

if date_range and isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered = filtered[(filtered["Tarikh"].isna()) | ((filtered["Tarikh"] >= start_date) & (filtered["Tarikh"] <= end_date))]

total_cr = len(filtered)
selesai = int((filtered["Status"] == "SELESAI").sum())
completion_rate = (selesai / total_cr * 100) if total_cr else 0
jumlah_kos = rm(filtered["Kos Numeric"].sum())
total_mandays = number(filtered["Total Mandays"].sum())

def kpi_card(label, value):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    kpi_card("Jumlah CR", f"{total_cr:,}")

with kpi2:
    kpi_card("Selesai", f"{selesai:,}")

with kpi3:
    kpi_card("Completion", f"{completion_rate:.1f}%")

with kpi4:
    kpi_card("Jumlah Kos", jumlah_kos)

with kpi5:
    kpi_card("Total Mandays", total_mandays)

st.divider()

left, right = st.columns((1.1, 1))

with left:
    status_counts = filtered["Status"].value_counts().rename_axis("Status").reset_index(name="Bilangan")
    status_counts["Status"] = pd.Categorical(status_counts["Status"], categories=STATUS_ORDER + [s for s in status_counts["Status"] if s not in STATUS_ORDER], ordered=True)
    status_counts = status_counts.sort_values("Status")
    fig_status = px.bar(status_counts, x="Status", y="Bilangan", title="Bilangan CR mengikut Status", text_auto=True)
    fig_status.update_layout(xaxis_title="Status", yaxis_title="Bilangan", height=420)
    st.plotly_chart(fig_status, use_container_width=True)

with right:
    bahagian_counts = filtered["Bahagian"].value_counts().rename_axis("Bahagian").reset_index(name="Bilangan")
    fig_bahagian = px.bar(bahagian_counts, x="Bilangan", y="Bahagian", orientation="h", title="CR mengikut Bahagian", text_auto=True)
    fig_bahagian.update_layout(xaxis_title="Bilangan", yaxis_title="Bahagian", height=420, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_bahagian, use_container_width=True)

left2, right2 = st.columns((1, 1))

with left2:
    trend = filtered.dropna(subset=["Tarikh"]).groupby(pd.Grouper(key="Tarikh", freq="MS")).size().reset_index(name="Bilangan")
    if not trend.empty:
        fig_trend = px.line(trend, x="Tarikh", y="Bilangan", markers=True, title="Trend Permohonan CR mengikut Bulan")
        fig_trend.update_layout(xaxis_title="Bulan", yaxis_title="Bilangan", height=420)
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Tiada tarikh valid untuk paparan trend.")

with right2:
    cost_by_bahagian = filtered.groupby("Bahagian", as_index=False)["Kos Numeric"].sum().sort_values("Kos Numeric", ascending=False)
    fig_cost = px.bar(cost_by_bahagian, x="Kos Numeric", y="Bahagian", orientation="h", title="Jumlah Kos mengikut Bahagian", text_auto=".2s")
    fig_cost.update_layout(xaxis_title="Kos (RM)", yaxis_title="Bahagian", height=420, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_cost, use_container_width=True)

left3, right3 = st.columns((1, 1))

with left3:
    ccb_counts = filtered["CCB"].value_counts().head(15).rename_axis("CCB").reset_index(name="Bilangan")
    fig_ccb = px.bar(ccb_counts, x="Bilangan", y="CCB", orientation="h", title="Top CCB mengikut Bilangan CR", text_auto=True)
    fig_ccb.update_layout(xaxis_title="Bilangan", yaxis_title="CCB", height=450, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_ccb, use_container_width=True)

with right3:
    mandays = filtered.groupby("Bahagian", as_index=False)[["On-Site", "Off-Site"]].sum().sort_values(["On-Site", "Off-Site"], ascending=False)
    fig_mandays = px.bar(mandays, x="Bahagian", y=["On-Site", "Off-Site"], title="On-Site vs Off-Site Mandays", barmode="group")
    fig_mandays.update_layout(xaxis_title="Bahagian", yaxis_title="Mandays", height=450, xaxis_tickangle=-30)
    st.plotly_chart(fig_mandays, use_container_width=True)

st.divider()

st.subheader("Senarai CR")
search = st.text_input("Search Tajuk CR / No. CCB / Nota")
table = filtered.copy()
if search:
    s = search.lower()
    table = table[
        table["Tajuk CR"].str.lower().str.contains(s, na=False)
        | table["No. CCB"].str.lower().str.contains(s, na=False)
        | table["Nota"].str.lower().str.contains(s, na=False)
    ]

show_cols = ["Bil", "Bahagian", "Tarikh Permohonan", "CCB", "No. CCB", "Tajuk CR", "Status", "Nota", "On-Site", "Off-Site", "Kos (RM)"]
st.dataframe(table[show_cols], use_container_width=True, hide_index=True)

csv = table[show_cols].to_csv(index=False).encode("utf-8-sig")
st.download_button("Download filtered data", data=csv, file_name="filtered_cr_dashboard.csv", mime="text/csv")
