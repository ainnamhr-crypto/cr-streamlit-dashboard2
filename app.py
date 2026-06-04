import re
from pathlib import Path
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# PAGE SETUP
# =========================================================
st.set_page_config(
    page_title="Dashboard CR mySIKAP",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CSS STYLE
# =========================================================
st.markdown("""
<style>
:root {
    --bg: #f6f8fb;
    --card: #ffffff;
    --border: #e8edf5;
    --text: #334155;
    --muted: #64748b;
    --blue: #64748b;
    --yellow: #fde68a;
    --teal: #99f6e4;
    --green: #86efac;
    --orange: #fdba74;
    --red: #fca5a5;
    --purple: #c4b5fd;
}

.stApp {
    background: var(--bg);
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1550px;
}

[data-testid="stSidebar"] {
    background: #ffffff;
}

.dashboard-title {
    font-size: 1.55rem;
    font-weight: 850;
    color: var(--text);
    margin-bottom: 0.2rem;
}

.dashboard-subtitle {
    font-size: 0.86rem;
    color: var(--muted);
    margin-bottom: 1rem;
}

.card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1rem;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.035);
}

.kpi-card {
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1rem 1.05rem;
    min-height: 112px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.035);
}

.kpi-label {
    font-size: 0.78rem;
    color: var(--muted);
    font-weight: 650;
    margin-bottom: 0.4rem;
}

.kpi-value {
    font-size: 1.85rem;
    line-height: 1.1;
    color: #475569;
    font-weight: 850;
}

.kpi-note {
    font-size: 0.72rem;
    color: var(--muted);
    margin-top: 0.45rem;
}

.insight-card {
    background: #ffffff;
    border: 1px solid var(--border);
    border-left: 5px solid #f59e0b;
    border-radius: 14px;
    padding: 0.95rem 1rem;
    min-height: 96px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.035);
}

.insight-title {
    font-size: 0.76rem;
    color: #92400e;
    font-weight: 800;
    margin-bottom: 0.28rem;
}

.insight-main {
    font-size: 1.05rem;
    color: #334155;
    font-weight: 800;
}

.insight-sub {
    font-size: 0.75rem;
    color: #64748b;
    margin-top: 0.25rem;
}

.click-helper {
    background: #f8fafc;
    border: 1px dashed #cbd5e1;
    border-radius: 12px;
    padding: 0.8rem 1rem;
    color: #475569;
    font-size: 0.84rem;
    margin-top: 0.5rem;
}

.rm-card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.05rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.035);
}

.rm-value {
    font-size: 1.9rem;
    line-height: 1.1;
    font-weight: 850;
    color: #64748b;
}

.rm-label {
    font-size: 0.76rem;
    color: #475569;
    margin-top: 0.35rem;
    font-weight: 650;
}

.section-label {
    font-size: 0.95rem;
    font-weight: 800;
    color: #334155;
    margin: 0.8rem 0 0.35rem 0;
}

.small-note {
    font-size: 0.78rem;
    color: #64748b;
    text-align: center;
    margin-top: 0.25rem;
    margin-bottom: 0.25rem;
}

div[data-testid="stPlotlyChart"] {
    background: white;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.72rem;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.035);
}

div[data-testid="stDataFrame"] {
    background: white;
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# CONSTANTS
# =========================================================
DEFAULT_DATA = Path(__file__).parent / "data.csv"

MONTH_MAP = {
    "jan": "Jan", "feb": "Feb", "mac": "Mar", "mar": "Mar", "apr": "Apr",
    "mei": "May", "may": "May", "jun": "Jun", "jul": "Jul", "ogos": "Aug",
    "aug": "Aug", "sep": "Sep", "sept": "Sep", "okt": "Oct", "oct": "Oct",
    "nov": "Nov", "dis": "Dec", "dec": "Dec",
}

STATUS_ORDER = [
    "BAHARU", "TPA", "SRS", "SDD", "SIT", "UAT",
    "PEMBANGUNAN", "DITANGGUHKAN", "GUGUR", "SELESAI"
]

ONGOING_BUCKET_ORDER = ["0–30 hari", "31–60 hari", "61–90 hari", ">90 hari", "Tiada tarikh"]


# =========================================================
# HELPER FUNCTIONS
# =========================================================
def normalize_date(value):
    if pd.isna(value):
        return pd.NaT

    text = str(value).strip()
    if text in {"", "-", "nan", "NaN", "None"}:
        return pd.NaT

    for src, dst in MONTH_MAP.items():
        text = re.sub(src, dst, text, flags=re.IGNORECASE)

    return pd.to_datetime(text, errors="coerce", dayfirst=True)


def money_to_float(value):
    if pd.isna(value):
        return 0.0

    text = str(value).strip()
    if text in {"", "-", "nan", "NaN", "None"}:
        return 0.0

    text = text.replace("RM", "").replace(",", "").strip()
    text = re.sub(r"[^0-9.\-]", "", text)

    try:
        return float(text) if text else 0.0
    except ValueError:
        return 0.0


def rm(value):
    return f"RM{value:,.0f}"


def number(value):
    try:
        value = float(value)
    except Exception:
        return "0"

    if abs(value - round(value)) < 0.001:
        return f"{int(round(value)):,}"

    return f"{value:,.1f}"


def clean_chart(fig, height=360, legend=True):
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=12, r=12, t=56, b=25),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11, color="#475569"),
        title=dict(font=dict(size=13, color="#334155"), x=0.5, xanchor="center"),
        showlegend=legend,
    )
    fig.update_xaxes(showgrid=True, gridcolor="#eef2f7", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eef2f7", zeroline=False)
    return fig


def kpi_card(label, value, note=""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(title, main, sub=""):
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">{title}</div>
            <div class="insight-main">{main}</div>
            <div class="insight-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def rm_card(value, label):
    st.markdown(
        f"""
        <div class="rm-card">
            <div class="rm-value">{value}</div>
            <div class="rm-label">Bahagian {label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_first_existing_col(df, candidates):
    for col in candidates:
        if col in df.columns:
            return col
    return None


def aging_bucket(days):
    if pd.isna(days):
        return "Tiada tarikh"
    if days <= 30:
        return "0–30 hari"
    if days <= 60:
        return "31–60 hari"
    if days <= 90:
        return "61–90 hari"
    return ">90 hari"


# =========================================================
# DATA LOADING
# =========================================================
@st.cache_data(show_spinner=False)
def load_data(source):
    df = pd.read_csv(source, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]

    expected_cols = [
        "Bil", "Bahagian", "Tarikh Permohonan", "CCB", "No. CCB", "Tajuk CR",
        "Status", "Nota", "On-Site", "Off-Site", "Kos (RM)"
    ]

    for col in expected_cols:
        if col not in df.columns:
            df[col] = pd.NA

    df = df.dropna(how="all").copy()

    df["Bil"] = pd.to_numeric(df["Bil"], errors="coerce")
    df["Bahagian"] = (
        df["Bahagian"]
        .fillna("Tidak dinyatakan")
        .astype(str)
        .str.strip()
        .replace({"": "Tidak dinyatakan", "nan": "Tidak dinyatakan", "None": "Tidak dinyatakan"})
    )
    df["CCB"] = (
        df["CCB"]
        .fillna("Tidak dinyatakan")
        .astype(str)
        .str.strip()
        .replace({"": "Tidak dinyatakan", "nan": "Tidak dinyatakan", "None": "Tidak dinyatakan"})
    )
    df["Status"] = (
        df["Status"]
        .fillna("Tidak dinyatakan")
        .astype(str)
        .str.strip()
        .str.upper()
        .replace({"": "TIDAK DINYATAKAN", "NAN": "TIDAK DINYATAKAN", "NONE": "TIDAK DINYATAKAN"})
    )
    df["No. CCB"] = df["No. CCB"].fillna("").astype(str).str.strip()
    df["Tajuk CR"] = df["Tajuk CR"].fillna("").astype(str).str.strip()
    df["Nota"] = df["Nota"].fillna("").astype(str).str.strip()

    df["Tarikh"] = df["Tarikh Permohonan"].apply(normalize_date)
    df["Tahun"] = df["Tarikh"].dt.year
    df["Bulan"] = df["Tarikh"].dt.to_period("M").astype(str).replace("NaT", "Tidak dinyatakan")

    # Optional completed date support.
    completed_col = get_first_existing_col(
        df,
        ["Tarikh Selesai", "Tarikh Siap", "Tarikh Completion", "Completion Date", "Date Completed"]
    )
    if completed_col:
        df["Tarikh Selesai Parsed"] = df[completed_col].apply(normalize_date)
    else:
        df["Tarikh Selesai Parsed"] = pd.NaT

    df["On-Site"] = pd.to_numeric(df["On-Site"], errors="coerce").fillna(0)
    df["Off-Site"] = pd.to_numeric(df["Off-Site"], errors="coerce").fillna(0)
    df["Total Mandays"] = df["On-Site"] + df["Off-Site"]
    df["Kos Numeric"] = df["Kos (RM)"].apply(money_to_float)

    today = pd.Timestamp(date.today())
    df["Aging Days"] = (today - df["Tarikh"]).dt.days
    df.loc[df["Tarikh"].isna(), "Aging Days"] = pd.NA

    df["Completion Duration Days"] = (df["Tarikh Selesai Parsed"] - df["Tarikh"]).dt.days
    df.loc[df["Tarikh Selesai Parsed"].isna() | df["Tarikh"].isna(), "Completion Duration Days"] = pd.NA

    return df


# =========================================================
# HEADER
# =========================================================
st.markdown('<div class="dashboard-title">Dashboard CR mySIKAP</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="dashboard-subtitle">Executive view untuk status CR, completion, bahagian, mandays, kos dan aging analysis.</div>',
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR: DATA + FILTER
# =========================================================
with st.sidebar:
    st.header("Data")
    uploaded = st.file_uploader("Upload CSV lain", type=["csv"])
    data_source = uploaded if uploaded is not None else DEFAULT_DATA
    df = load_data(data_source)

    st.divider()
    st.header("Filter")

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
        date_range = st.date_input(
            "Tarikh Permohonan",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
    else:
        date_range = None


# =========================================================
# APPLY FILTER
# =========================================================
filtered = df[
    df["Bahagian"].isin(selected_bahagian)
    & df["Status"].isin(selected_status)
    & df["CCB"].isin(selected_ccb)
].copy()

if date_range and isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered = filtered[
        (filtered["Tarikh"].isna())
        | ((filtered["Tarikh"] >= start_date) & (filtered["Tarikh"] <= end_date))
    ].copy()


# =========================================================
# SUMMARY METRICS
# =========================================================
total_cr = len(filtered)
complete_cr = int((filtered["Status"] == "SELESAI").sum())
ongoing_cr = int((filtered["Status"] != "SELESAI").sum())
completion_rate = (complete_cr / total_cr * 100) if total_cr else 0
total_cost = filtered["Kos Numeric"].sum()
total_mandays = filtered["Total Mandays"].sum()

ongoing_df = filtered[filtered["Status"] != "SELESAI"].copy()
valid_ongoing_age = ongoing_df["Aging Days"].dropna()
avg_aging = valid_ongoing_age.mean() if not valid_ongoing_age.empty else 0
over_90 = int((valid_ongoing_age > 90).sum()) if not valid_ongoing_age.empty else 0

k1, k2, k3, k4, k5 = st.columns(5, gap="small")
with k1:
    kpi_card("Jumlah CR", f"{total_cr:,}", "Semua rekod selepas filter")
with k2:
    kpi_card("Complete", f"{complete_cr:,}", "Status SELESAI")
with k3:
    kpi_card("On-going", f"{ongoing_cr:,}", "Selain status SELESAI")
with k4:
    kpi_card("Completion", f"{completion_rate:.1f}%", "Complete / jumlah CR")
with k5:
    kpi_card("Jumlah Kos", rm(total_cost), "Kos keseluruhan")


# =========================================================
# INSIGHT / ALERT SECTION
# =========================================================
st.markdown('<div class="section-label">Key Insight</div>', unsafe_allow_html=True)

status_counts_all = filtered["Status"].value_counts()
non_complete_status_counts = status_counts_all.drop(labels=["SELESAI"], errors="ignore")
highest_pending_status = non_complete_status_counts.idxmax() if not non_complete_status_counts.empty else "-"
highest_pending_count = int(non_complete_status_counts.max()) if not non_complete_status_counts.empty else 0

bahagian_counts_all = filtered["Bahagian"].value_counts()
highest_bahagian = bahagian_counts_all.idxmax() if not bahagian_counts_all.empty else "-"
highest_bahagian_count = int(bahagian_counts_all.max()) if not bahagian_counts_all.empty else 0

cost_by_bahagian_tmp = filtered.groupby("Bahagian", as_index=False)["Kos Numeric"].sum()
if not cost_by_bahagian_tmp.empty:
    highest_cost_row = cost_by_bahagian_tmp.sort_values("Kos Numeric", ascending=False).iloc[0]
    highest_cost_bahagian = highest_cost_row["Bahagian"]
    highest_cost_value = highest_cost_row["Kos Numeric"]
else:
    highest_cost_bahagian = "-"
    highest_cost_value = 0

i1, i2, i3 = st.columns(3, gap="small")
with i1:
    insight_card(
        "STATUS PALING BANYAK BELUM SELESAI",
        f"{highest_pending_status} — {highest_pending_count:,} CR",
        "Fokus untuk kenal pasti bottleneck proses."
    )
with i2:
    insight_card(
        "BAHAGIAN PALING BANYAK CR",
        f"{highest_bahagian} — {highest_bahagian_count:,} CR",
        "Bahagian dengan volume permohonan tertinggi."
    )
with i3:
    insight_card(
        "KOS TERTINGGI",
        f"{highest_cost_bahagian} — {rm(highest_cost_value)}",
        "Bahagian dengan jumlah kos paling tinggi."
    )

st.markdown(
    '<div class="click-helper">Klik/pilih status di bawah untuk terus keluar senarai CR berkaitan. Ini lebih stabil daripada click pada card HTML.</div>',
    unsafe_allow_html=True,
)

status_detail_options = ["Pilih status untuk lihat senarai"] + list(non_complete_status_counts.index)
selected_status_detail = st.selectbox(
    "Drill down: Status paling banyak belum selesai",
    status_detail_options,
    key="status_drilldown_select",
)

if selected_status_detail != "Pilih status untuk lihat senarai":
    status_detail = filtered[filtered["Status"] == selected_status_detail].copy()
    detail_cols = [
        "Bil", "Bahagian", "Tarikh Permohonan", "CCB", "No. CCB",
        "Tajuk CR", "Status", "Nota", "On-Site", "Off-Site", "Kos (RM)", "Aging Days"
    ]
    detail_cols = [col for col in detail_cols if col in status_detail.columns]

    with st.expander(
        f"Senarai CR untuk status {selected_status_detail} ({len(status_detail):,} rekod)",
        expanded=True,
    ):
        st.dataframe(
            status_detail[detail_cols].sort_values("Aging Days", ascending=False, na_position="last"),
            use_container_width=True,
            hide_index=True,
            height=340,
        )


# =========================================================
# ROW 1: COMPLETION + STATUS
# =========================================================
st.markdown('<div class="section-label">Completion & Status Overview</div>', unsafe_allow_html=True)

row1_left, row1_mid, row1_right = st.columns((1.05, 1.45, 0.9), gap="small")

with row1_left:
    completion_data = pd.DataFrame({
        "Kategori": ["Complete", "On-going"],
        "Bilangan": [complete_cr, ongoing_cr],
    })
    fig_completion = px.pie(
        completion_data,
        names="Kategori",
        values="Bilangan",
        title="Completion Status",
        hole=0.55,
    )
    fig_completion.update_traces(textposition="inside", textinfo="percent+label+value")
    st.plotly_chart(clean_chart(fig_completion, 335), use_container_width=True)

with row1_mid:
    status_counts = filtered["Status"].value_counts().rename_axis("Status").reset_index(name="Bilangan")
    status_counts["Status"] = pd.Categorical(
        status_counts["Status"],
        categories=STATUS_ORDER + [s for s in status_counts["Status"] if s not in STATUS_ORDER],
        ordered=True,
    )
    status_counts = status_counts.sort_values("Bilangan", ascending=True)

    fig_status = px.bar(
        status_counts,
        x="Bilangan",
        y="Status",
        orientation="h",
        text_auto=True,
        title="Status CR",
    )
    fig_status.update_traces(marker_color="#fbbf24", textposition="outside")
    fig_status.update_layout(xaxis_title="Bilangan", yaxis_title="")
    st.plotly_chart(clean_chart(fig_status, 335, legend=False), use_container_width=True)

with row1_right:
    st.markdown("##### Status Table")
    status_table = filtered["Status"].value_counts().rename_axis("Status CR").reset_index(name="Bilangan")
    status_table["Status CR"] = pd.Categorical(
        status_table["Status CR"],
        categories=STATUS_ORDER + [s for s in status_table["Status CR"] if s not in STATUS_ORDER],
        ordered=True,
    )
    status_table = status_table.sort_values("Status CR")
    st.dataframe(
        status_table.astype({"Status CR": str}),
        use_container_width=True,
        hide_index=True,
        height=285,
    )


# =========================================================
# ROW 2: BAHAGIAN
# =========================================================
st.markdown('<div class="section-label">CR Mengikut Bahagian</div>', unsafe_allow_html=True)

row2_left, row2_right = st.columns(2, gap="small")

with row2_left:
    bahagian_counts = filtered["Bahagian"].value_counts().rename_axis("Bahagian").reset_index(name="Bil Permohonan")
    bahagian_counts = bahagian_counts.sort_values("Bil Permohonan", ascending=True)

    fig_bahagian = px.bar(
        bahagian_counts,
        x="Bil Permohonan",
        y="Bahagian",
        orientation="h",
        text_auto=True,
        title="Jumlah CR Mengikut Bahagian",
    )
    fig_bahagian.update_traces(marker_color="#fde68a", textposition="outside")
    fig_bahagian.update_layout(xaxis_title="Bil. CR", yaxis_title="")
    st.plotly_chart(clean_chart(fig_bahagian, 360, legend=False), use_container_width=True)

with row2_right:
    done_by_bahagian = (
        filtered[filtered["Status"] == "SELESAI"]
        .groupby("Bahagian", as_index=False)
        .size()
        .rename(columns={"size": "Bil CR Selesai"})
        .sort_values("Bil CR Selesai", ascending=True)
    )

    if done_by_bahagian.empty:
        st.info("Tiada CR selesai untuk filter semasa.")
    else:
        fig_done = px.bar(
            done_by_bahagian,
            x="Bil CR Selesai",
            y="Bahagian",
            orientation="h",
            text_auto=True,
            title="CR Selesai Mengikut Bahagian",
        )
        fig_done.update_traces(marker_color="#99f6e4", textposition="outside")
        fig_done.update_layout(xaxis_title="Bil. CR Selesai", yaxis_title="")
        st.plotly_chart(clean_chart(fig_done, 360, legend=False), use_container_width=True)


# =========================================================
# ROW 3: AGING ANALYSIS
# =========================================================
st.markdown('<div class="section-label">Aging Analysis</div>', unsafe_allow_html=True)

age_left, age_right = st.columns((1.1, 1.4), gap="small")

with age_left:
    kpi_age1, kpi_age2 = st.columns(2, gap="small")
    with kpi_age1:
        kpi_card("Avg Aging On-going", f"{avg_aging:.0f} hari", "Asas: hari ini - Tarikh Permohonan")
    with kpi_age2:
        kpi_card("On-going >90 Hari", f"{over_90:,}", "Perlu perhatian")

    st.info(
        "Nota: Aging ini guna Tarikh Permohonan sebagai asas. Bila data final ada Tarikh Selesai / Tarikh Status Terkini / SLA Days, chart ini boleh jadi lebih tepat."
    )

with age_right:
    if ongoing_df.empty:
        st.info("Tiada on-going CR untuk aging analysis.")
    else:
        ongoing_df["Aging Bucket"] = ongoing_df["Aging Days"].apply(aging_bucket)
        aging_counts = ongoing_df["Aging Bucket"].value_counts().rename_axis("Aging Bucket").reset_index(name="Bilangan")
        aging_counts["Aging Bucket"] = pd.Categorical(
            aging_counts["Aging Bucket"],
            categories=ONGOING_BUCKET_ORDER,
            ordered=True,
        )
        aging_counts = aging_counts.sort_values("Aging Bucket")

        fig_aging = px.bar(
            aging_counts,
            x="Aging Bucket",
            y="Bilangan",
            text_auto=True,
            title="Aging Bucket untuk On-going CR",
        )
        fig_aging.update_traces(marker_color="#fdba74", textposition="outside")
        fig_aging.update_layout(xaxis_title="Aging Bucket", yaxis_title="Bilangan CR")
        st.plotly_chart(clean_chart(fig_aging, 300, legend=False), use_container_width=True)

        available_buckets = [
            bucket for bucket in ONGOING_BUCKET_ORDER
            if bucket in ongoing_df["Aging Bucket"].dropna().unique()
        ]

        selected_bucket = st.radio(
            "Klik/pilih Aging Bucket untuk lihat senarai CR",
            available_buckets,
            horizontal=True,
            key="aging_bucket_drilldown",
        )

        bucket_detail = ongoing_df[ongoing_df["Aging Bucket"] == selected_bucket].copy()
        bucket_cols = [
            "Bil", "Bahagian", "Tarikh Permohonan", "CCB", "No. CCB",
            "Tajuk CR", "Status", "Nota", "Aging Days", "On-Site", "Off-Site", "Kos (RM)"
        ]
        bucket_cols = [col for col in bucket_cols if col in bucket_detail.columns]

        with st.expander(
            f"Senarai On-going CR untuk Aging Bucket {selected_bucket} ({len(bucket_detail):,} rekod)",
            expanded=True,
        ):
            st.dataframe(
                bucket_detail[bucket_cols].sort_values("Aging Days", ascending=False, na_position="last"),
                use_container_width=True,
                hide_index=True,
                height=340,
            )


# =========================================================
# ROW 4: MANDAYS + COST
# =========================================================
st.markdown('<div class="section-label">Mandays & Kos</div>', unsafe_allow_html=True)

manday_left, manday_right = st.columns(2, gap="small")

mandays_by_bahagian = (
    filtered.groupby("Bahagian", as_index=False)[["On-Site", "Off-Site"]]
    .sum()
    .sort_values("Bahagian")
)

with manday_left:
    if mandays_by_bahagian.empty:
        st.info("Tiada data mandays.")
    else:
        fig_mandays = px.bar(
            mandays_by_bahagian,
            x="Bahagian",
            y=["On-Site", "Off-Site"],
            title="Mandays On-Site vs Off-Site",
            barmode="group",
            text_auto=True,
        )
        fig_mandays.update_layout(xaxis_title="Bahagian", yaxis_title="Mandays")
        fig_mandays.update_xaxes(tickangle=-35)
        st.plotly_chart(clean_chart(fig_mandays, 360), use_container_width=True)

with manday_right:
    cost_by_bahagian = (
        filtered.groupby("Bahagian", as_index=False)["Kos Numeric"]
        .sum()
        .sort_values("Kos Numeric", ascending=True)
    )

    if cost_by_bahagian.empty:
        st.info("Tiada data kos.")
    else:
        fig_cost = px.bar(
            cost_by_bahagian,
            x="Kos Numeric",
            y="Bahagian",
            orientation="h",
            text_auto=".3s",
            title="Kos Mengikut Bahagian",
        )
        fig_cost.update_traces(marker_color="#c4b5fd", textposition="outside")
        fig_cost.update_layout(xaxis_title="Jumlah Kos (RM)", yaxis_title="")
        st.plotly_chart(clean_chart(fig_cost, 360, legend=False), use_container_width=True)


# =========================================================
# ROW 5: TOP ACTIONABLE TABLES
# =========================================================
st.markdown('<div class="section-label">Actionable Lists</div>', unsafe_allow_html=True)

top_left, top_right = st.columns(2, gap="small")

with top_left:
    st.markdown("##### Top 10 On-going CR Paling Lama")
    oldest_cols = ["Bil", "Bahagian", "Tarikh Permohonan", "CCB", "No. CCB", "Tajuk CR", "Status", "Aging Days"]
    oldest = (
        ongoing_df.dropna(subset=["Aging Days"])
        .sort_values("Aging Days", ascending=False)
        .head(10)
    )
    if oldest.empty:
        st.info("Tiada data aging valid.")
    else:
        st.dataframe(oldest[oldest_cols], use_container_width=True, hide_index=True, height=300)

with top_right:
    st.markdown("##### Top 10 CR Kos Tertinggi")
    cost_cols = ["Bil", "Bahagian", "CCB", "No. CCB", "Tajuk CR", "Status", "Kos (RM)"]
    top_cost_cr = filtered.sort_values("Kos Numeric", ascending=False).head(10)
    if top_cost_cr.empty:
        st.info("Tiada data kos.")
    else:
        st.dataframe(top_cost_cr[cost_cols], use_container_width=True, hide_index=True, height=300)


# =========================================================
# ROW 6: COST CARDS
# =========================================================
st.markdown('<div class="section-label">Ringkasan Kos Tertinggi Mengikut Bahagian</div>', unsafe_allow_html=True)

top_cost_bahagian = (
    filtered.groupby("Bahagian", as_index=False)["Kos Numeric"]
    .sum()
    .sort_values("Kos Numeric", ascending=False)
    .head(6)
)

if not top_cost_bahagian.empty:
    card_cols = st.columns(3, gap="small")
    for i, (_, row) in enumerate(top_cost_bahagian.iterrows()):
        with card_cols[i % 3]:
            rm_card(rm(row["Kos Numeric"]), row["Bahagian"])


# =========================================================
# FULL DATA TABLE
# =========================================================
st.divider()

with st.expander("Senarai CR / Full Data Table", expanded=False):
    search = st.text_input("Search Tajuk CR / No. CCB / Nota / Bahagian")
    table = filtered.copy()

    if search:
        s = search.lower()
        table = table[
            table["Tajuk CR"].str.lower().str.contains(s, na=False)
            | table["No. CCB"].str.lower().str.contains(s, na=False)
            | table["Nota"].str.lower().str.contains(s, na=False)
            | table["Bahagian"].str.lower().str.contains(s, na=False)
        ]

    show_cols = [
        "Bil", "Bahagian", "Tarikh Permohonan", "CCB", "No. CCB", "Tajuk CR",
        "Status", "Nota", "On-Site", "Off-Site", "Kos (RM)", "Aging Days"
    ]

    existing_show_cols = [col for col in show_cols if col in table.columns]
    st.dataframe(table[existing_show_cols], use_container_width=True, hide_index=True)

    csv = table[existing_show_cols].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Download filtered data",
        data=csv,
        file_name="filtered_cr_dashboard.csv",
        mime="text/csv",
    )


# =========================================================
# FOOTNOTE
# =========================================================
st.caption(
    "Nota: Complete merujuk kepada status SELESAI. On-going merujuk kepada semua status selain SELESAI. "
    "Aging dikira secara asas menggunakan Tarikh Permohonan sehingga tarikh semasa."
)
