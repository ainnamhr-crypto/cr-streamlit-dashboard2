# CR Dashboard Prototype - Streamlit

Prototype dashboard interaktif untuk visualize data Change Request (CR).

## Cara run locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run dashboard:

```bash
streamlit run app.py
```

3. Browser akan buka dashboard secara automatik. Kalau tidak, buka link yang Streamlit paparkan di terminal.

## Fungsi dashboard

- KPI ringkas: jumlah CR, selesai, completion %, jumlah kos, total mandays
- Filter ikut Bahagian, Status, CCB dan Tarikh Permohonan
- Chart status CR
- Chart CR mengikut bahagian
- Trend permohonan CR bulanan
- Jumlah kos mengikut bahagian
- Top CCB mengikut bilangan CR
- On-Site vs Off-Site mandays
- Search table dan download filtered data

## Tukar data

Dashboard ini sudah include `data.csv` daripada file test. Untuk test data lain, guna upload box di sidebar atau replace `data.csv`.
