import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Airlines On Time U.S", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_parquet("Data_Dashboard_Preparation_Final.parquet")
    return df

df = load_data()

st.sidebar.title("📊 Menu Dashboard")
menu = st.sidebar.radio(
    "Pilih Analisis:",
    ["Ringkasan Delay", "Penyebab Dominan Delay", "Bandara & Bulan Tersibuk", "Cek Rute (A ke B)"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filter")
tahun_pilihan = st.sidebar.multiselect(
    "Tahun:", options=sorted(df['YEAR'].unique()), default=sorted(df['YEAR'].unique())
)

df_filtered = df[df['YEAR'].isin(tahun_pilihan)]

def weighted_avg(data, value_col, weight_col):
    return (data[value_col] * data[weight_col]).sum() / data[weight_col].sum()

if menu == "Ringkasan Delay":
    st.title("Ringkasan Ketepatan Waktu Penerbangan")

    col1, col2, col3 = st.columns(3)
    avg_delay = weighted_avg(df_filtered, 'avg_arr_delay', 'total_flights')
    delay_rate = df_filtered['delayed_flights'].sum() / df_filtered['total_flights'].sum() * 100
    total_flights = df_filtered['total_flights'].sum()

    col1.metric("Rata-rata Delay", f"{avg_delay:.1f} menit")
    col2.metric("Persentase Delay (>15 menit)", f"{delay_rate:.1f}%")
    col3.metric("Total Penerbangan", f"{total_flights:,.0f}")

    st.subheader("Delay per Maskapai")
    maskapai = df_filtered.groupby('OP_UNIQUE_CARRIER').apply(
        lambda g: weighted_avg(g, 'avg_arr_delay', 'total_flights')
    ).reset_index(name='avg_delay').sort_values('avg_delay', ascending=False)

    fig1 = px.bar(maskapai, x='avg_delay', y='OP_UNIQUE_CARRIER', orientation='h',
                  labels={'avg_delay': 'Rata-rata Delay (menit)', 'OP_UNIQUE_CARRIER': 'Maskapai'},
                  color='avg_delay', color_continuous_scale='Reds')
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Tren Delay per Bulan")
    bulanan = df_filtered.groupby('MONTH').apply(
        lambda g: weighted_avg(g, 'avg_arr_delay', 'total_flights')
    ).reset_index(name='avg_delay')

    fig2 = px.line(bulanan, x='MONTH', y='avg_delay', markers=True,
                   labels={'avg_delay': 'Rata-rata Delay (menit)', 'MONTH': 'Bulan'})
    st.plotly_chart(fig2, use_container_width=True)

elif menu == "Penyebab Dominan Delay":
    st.title("Faktor Penyebab Delay Dominan")

    penyebab_cols = ['total_carrier_delay', 'total_weather_delay', 'total_nas_delay',
                      'total_security_delay', 'total_late_aircraft_delay']
    label_penyebab = ['Maskapai', 'Cuaca', 'Sistem Navigasi Udara (NAS)', 'Keamanan', 'Pesawat Telat Datang']

    total_penyebab = df_filtered[penyebab_cols].sum()
    total_penyebab.index = label_penyebab
    total_penyebab = total_penyebab.sort_values(ascending=False)

    fig = px.pie(values=total_penyebab.values, names=total_penyebab.index,
                 title="Proporsi Total Menit Delay Berdasarkan Penyebab")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Rincian (menit)")
    st.dataframe(total_penyebab.reset_index().rename(columns={'index': 'Penyebab', 0: 'Total Menit'}))

elif menu == "Bandara & Bulan Tersibuk":
    st.title("Bandara & Bulan Tersibuk")

    st.subheader("Top 10 Bandara Tersibuk")
    bandara = df_filtered.groupby(['ORIGIN', 'origin_city']).agg(
        total_flights=('total_flights', 'sum')
    ).reset_index().sort_values('total_flights', ascending=False).head(10)

    fig1 = px.bar(bandara, x='total_flights', y='origin_city', orientation='h',
                  labels={'total_flights': 'Total Penerbangan', 'origin_city': 'Kota'})
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Volume Penerbangan per Bulan")
    bulanan_traffic = df_filtered.groupby('MONTH')['total_flights'].sum().reset_index()
    fig2 = px.bar(bulanan_traffic, x='MONTH', y='total_flights',
                  labels={'total_flights': 'Total Penerbangan', 'MONTH': 'Bulan'})
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Bandara Tersibuk per Bulan Tertentu")
    bulan_pilih = st.selectbox("Pilih Bulan:", sorted(df_filtered['MONTH'].unique()))
    top_per_bulan = df_filtered[df_filtered['MONTH'] == bulan_pilih].groupby('origin_city')['total_flights'].sum()
    top_per_bulan = top_per_bulan.sort_values(ascending=False).head(10).reset_index()

    fig3 = px.bar(top_per_bulan, x='total_flights', y='origin_city', orientation='h')
    st.plotly_chart(fig3, use_container_width=True)

elif menu == "Cek Rute (A ke B)":
    st.title("Cek Pola Rute Penerbangan")

    col1, col2 = st.columns(2)
    kota_asal = col1.selectbox("Dari Kota:", sorted(df['origin_city'].unique()))
    
    # Tujuan otomatis mengikuti pilihan kota asal (hanya tampilkan rute yang benar-benar ada)
    pilihan_tujuan = df[df['origin_city'] == kota_asal]['dest_city'].unique()
    kota_tujuan = col2.selectbox("Ke Kota:", sorted(pilihan_tujuan))

    rute = df_filtered[(df_filtered['origin_city'] == kota_asal) & (df_filtered['dest_city'] == kota_tujuan)]

    if rute.empty:
        st.warning("Tidak ada data penerbangan untuk rute ini pada tahun yang difilter.")
    else:
        col1, col2 = st.columns(2)
        total_rute = rute['total_flights'].sum()
        avg_delay_rute = weighted_avg(rute, 'avg_arr_delay', 'total_flights')
        col1.metric("Total Penerbangan", f"{total_rute:,.0f}")
        col2.metric("Rata-rata Delay", f"{avg_delay_rute:.1f} menit")

        st.subheader(f"Volume Penerbangan {kota_asal} → {kota_tujuan} per Bulan")
        bulanan_rute = rute.groupby('MONTH')['total_flights'].sum().reset_index()
        bulan_tersibuk = bulanan_rute.loc[bulanan_rute['total_flights'].idxmax(), 'MONTH']

        fig = px.bar(bulanan_rute, x='MONTH', y='total_flights',
                     labels={'total_flights': 'Total Penerbangan', 'MONTH': 'Bulan'})
        st.plotly_chart(fig, use_container_width=True)
        st.info(f"Bulan tersibuk untuk rute ini: **Bulan {bulan_tersibuk}**")
