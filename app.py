import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils.gsc_helper import fetch_all_data, get_sites_list, get_performance_data

# Konfigurasi halaman Streamlit
st.set_page_config(page_title="Dashboard GSC - Monitoring Domain Global", layout="wide")

st.title("📈 Dashboard GSC - Monitoring Domain Global")

# 📂 Pengaturan di Sidebar
with st.sidebar:
    st.header("Pengaturan & Filter")

    # 🕒 Pilihan Rentang Tanggal
    date_option = st.selectbox(
        "Pilih Rentang Tanggal:",
        options=["24 hours", "7 days", "28 days", "3 months", "Custom Date"],
        index=2
    )

    # Menghitung rentang tanggal berdasarkan opsi yang dipilih
    if date_option == "24 hours":
        end_date = datetime.today().date()
        start_date = end_date - timedelta(days=1)
    elif date_option == "7 days":
        end_date = datetime.today().date()
        start_date = end_date - timedelta(days=7)
    elif date_option == "28 days":
        end_date = datetime.today().date()
        start_date = end_date - timedelta(days=28)
    elif date_option == "3 months":
        end_date = datetime.today().date()
        start_date = end_date - timedelta(days=90)
    else:  # Custom Date
        start_date = st.date_input("Start Date", value=pd.to_datetime("2025-02-01"))
        end_date = st.date_input("End Date", value=pd.to_datetime("2025-02-23"))

    st.write(f"📅 **Rentang Tanggal:** {start_date} hingga {end_date}")

    # Pilihan untuk Mengambil Data Gabungan atau Per Domain
    data_mode = st.radio(
        "Mode Pengambilan Data:",
        options=["Data Gabungan Semua Domain", "Data Per Domain"],
        help="Pilih untuk melihat data dari semua domain atau memilih satu domain."
    )

    # 🔴 [Perubahan Penting] Mengambil Daftar Domain dari GSC
    # Menggunakan get_sites_list() yang sudah diperbarui dengan autentikasi aman
    all_sites = get_sites_list()
    selected_site = None
    if data_mode == "Data Per Domain" and all_sites:
        selected_site = st.selectbox("Pilih Domain", options=all_sites, help="Pilih domain untuk melihat data spesifik.")

# 🟡 Variabel penyimpanan data yang diambil
data = pd.DataFrame()

# 🔵 Tombol untuk mengambil data dari GSC
if st.button("Fetch Data"):
    if data_mode == "Data Gabungan Semua Domain":
        data = fetch_all_data(start_date=start_date.strftime('%Y-%m-%d'), end_date=end_date.strftime('%Y-%m-%d'))
    elif selected_site:
        data = get_performance_data(selected_site, start_date=start_date.strftime('%Y-%m-%d'), end_date=end_date.strftime('%Y-%m-%d'))
    else:
        st.warning("Pilih domain terlebih dahulu untuk melihat data spesifik.")
    
    if not data.empty:
        st.success("Data berhasil diambil!")
        st.session_state['fetched_data'] = data
    else:
        st.warning("Tidak ada data yang ditemukan untuk rentang tanggal yang dipilih.")
        st.session_state['fetched_data'] = pd.DataFrame()

# Mengambil data dari session state
data = st.session_state.get('fetched_data', pd.DataFrame())

# 🟢 Lanjutkan hanya jika ada data yang tersedia
if not data.empty:
    st.dataframe(data)

    # 📊 Ringkasan Cepat
    st.markdown("## 📈 Ringkasan Data")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Total Klik", value=int(data['Clicks'].sum()))
    col2.metric(label="Total Impresi", value=int(data['Impressions'].sum()))
    col3.metric(label="Rata-rata CTR", value=f"{data['CTR'].mean():.2%}")
    col4.metric(label="Rata-rata Posisi", value=f"{data['Position'].mean():.2f}")

    # 🗃️ Unduh Data sebagai CSV
    csv_data = data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="💾 Download Data sebagai CSV",
        data=csv_data,
        file_name=f"gsc_data_{start_date}_{end_date}.csv",
        mime='text/csv',
    )

    # Input teks untuk memfilter pages berdasarkan pola atau keyword
    page_filter = st.text_input(
        "Filter Pages berdasarkan Keyword atau Pola (contoh: '/?', '%', 'product')",
        value="",
        placeholder="Masukkan pola URL atau kata kunci dan tekan Enter"
    )

    # Input teks untuk memfilter queries berdasarkan kata kunci
    query_filter = st.text_input(
        "Filter Queries berdasarkan Kata Kunci (contoh: 'promo', 'diskon', 'slot')",
        value="",
        placeholder="Masukkan kata kunci query dan tekan Enter"
    )

    # Dropdown untuk memfilter berdasarkan kode negara
    available_countries = data['Country'].unique().tolist() if 'Country' in data.columns else []
    
    selected_country = st.selectbox(
        "Filter berdasarkan Kode Negara:",
        options=["Semua Negara"] + available_countries,
        help="Pilih kode negara (contoh: ID, US, MY) untuk melihat data performa keyword spesifik."
    )

    # Dropdown untuk memilih jumlah query teratas
    top_n = st.selectbox(
        "Pilih jumlah query teratas untuk dianalisis:",
        options=[5, 10, 20, 30, 50],
        index=1,
        help="Pilih berapa banyak query teratas yang ingin Anda analisis berdasarkan klik dan impresi."
    )

    # Tabel Data Queries & Pages
    query_table = data.groupby(['Query', 'Page', 'Site', 'Country']).agg({
        'Clicks': 'sum',
        'Impressions': 'sum',
        'CTR': 'mean',
        'Position': 'mean'
    }).reset_index()
    
    # Terapkan filter query, page, dan negara
    if page_filter:
        query_table = query_table[query_table['Page'].str.contains(page_filter, na=False, case=False)]
    if query_filter:
        query_table = query_table[query_table['Query'].str.contains(query_filter, na=False, case=False)]
    if selected_country and selected_country != "Semua Negara":
        query_table = query_table[query_table['Country'] == selected_country]

    # Mendapatkan Top N Queries
    top_queries = query_table.sort_values(by=['Clicks', 'Impressions'], ascending=[False, False]).head(top_n)
    st.dataframe(top_queries)

    # Visualisasi Data
    st.markdown("### 📈 Visualisasi Data: Queries dengan Klik Tertinggi")
    fig_clicks = px.bar(top_queries, x='Clicks', y='Query', color='Country', orientation='h', 
                        title='Top Queries berdasarkan Klik (per Kode Negara)', height=600)
    st.plotly_chart(fig_clicks, use_container_width=True)

    st.markdown("### 📊 Visualisasi Data: Queries dengan Impresi Tertinggi")
    fig_impressions = px.bar(top_queries, x='Impressions', y='Query', color='Country', orientation='h', 
                             title='Top Queries berdasarkan Impresi (per Kode Negara)', height=600)
    st.plotly_chart(fig_impressions, use_container_width=True)
