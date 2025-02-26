import json
import pandas as pd
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 📂 Membuat service untuk Google Search Console API
@st.cache_resource(show_spinner=False)
def get_service():
    try:
        # Mengambil file kunci JSON dari Streamlit Secrets
        keyfile_json = st.secrets["gcp"]["keyfile"]
        
        # Memuat file kunci JSON
        credentials_info = json.loads(keyfile_json)

        # Membuat kredensial menggunakan informasi dari secrets
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info, 
            scopes=['https://www.googleapis.com/auth/webmasters.readonly']
        )

        # Refresh token jika kredensial telah kedaluwarsa
        if credentials.expired:
            st.info("⏳ Token telah kedaluwarsa, mencoba untuk refresh...")
            credentials.refresh(Request())

        # Membuat service untuk Google API
        service = build('searchconsole', 'v1', credentials=credentials)
        st.success("✅ Berhasil terhubung ke Google Search Console API!")
        return service

    except Exception as e:
        st.error(f"❌ Gagal membuat service GSC: {e}")
        return None

# 🌐 Mendapatkan daftar situs dari Google Search Console
def get_sites_list():
    service = get_service()
    if not service:
        st.error("❌ Tidak dapat terhubung ke Google Search Console.")
        return []

    try:
        sites = service.sites().list().execute()
        site_list = [site['siteUrl'] for site in sites.get('siteEntry', [])]
        
        if not site_list:
            st.warning("⚠️ Tidak ada situs yang ditemukan di Google Search Console.")
        
        return site_list

    except Exception as e:
        st.error(f"❌ Terjadi kesalahan saat mengakses GSC: {e}")
        return []

# 📊 Mendapatkan data performa dari Google Search Console
def get_performance_data(site_url, start_date, end_date):
    service = get_service()
    if not service:
        st.error("❌ Tidak dapat terhubung ke Google Search Console.")
        return pd.DataFrame()

    try:
        request = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['query', 'page', 'country'],
            'rowLimit': 5000
        }

        response = service.searchanalytics().query(siteUrl=site_url, body=request).execute()

        data = []
        if 'rows' in response:
            for row in response['rows']:
                keys = row.get('keys', ['', '', ''])
                data.append([
                    keys[0],  # query
                    keys[1],  # page
                    keys[2],  # country
                    row.get('clicks', 0),
                    row.get('impressions', 0),
                    row.get('ctr', 0.0),
                    row.get('position', 0.0),
                    site_url
                ])

        # Mengembalikan DataFrame dengan kolom yang terdefinisi dengan baik
        df = pd.DataFrame(data, columns=[
            'Query', 'Page', 'Country', 
            'Clicks', 'Impressions', 'CTR', 'Position', 'Site'
        ])

        if df.empty:
            st.warning(f"⚠️ Tidak ada data performa yang ditemukan untuk situs {site_url} pada rentang tanggal {start_date} hingga {end_date}.")
        else:
            st.success(f"✅ Data performa berhasil diambil untuk situs {site_url}!")

        return df

    except Exception as e:
        st.error(f"❌ Error fetching performance data: {e}")
        return pd.DataFrame()
