import json
import pandas as pd
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 📂 Membuat service untuk Google Search Console API menggunakan Streamlit Secrets
def get_service():
    try:
        # Mengambil kredensial dari Streamlit Secrets
        keyfile_json = st.secrets["gcp"]["keyfile"]
        credentials_info = json.loads(keyfile_json)

        # Membuat kredensial menggunakan informasi dari secrets
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info, 
            scopes=['https://www.googleapis.com/auth/webmasters.readonly']
        )

        # Refresh token jika kredensial telah kedaluwarsa
        if credentials.expired:
            credentials.refresh(Request())

        # Membuat service untuk Google API
        service = build('searchconsole', 'v1', credentials=credentials)
        return service

    except Exception as e:
        st.error(f"❌ Gagal membuat service GSC: {e}")
        return None

# Mendapatkan daftar situs dari Google Search Console
def get_sites_list():
    service = get_service()
    if not service:
        return []

    try:
        sites = service.sites().list().execute()
        site_list = [site['siteUrl'] for site in sites.get('siteEntry', [])]
        return site_list

    except Exception as e:
        st.error(f"❌ Terjadi kesalahan saat mengakses GSC: {e}")
        return []

# Mendapatkan data performa dari situs tertentu
def get_performance_data(site_url, start_date, end_date):
    service = get_service()
    if not service:
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

        return pd.DataFrame(data, columns=[
            'Query', 'Page', 'Country', 
            'Clicks', 'Impressions', 'CTR', 'Position', 'Site'
        ])

    except Exception as e:
        st.error(f"❌ Error fetching performance data: {e}")
        return pd.DataFrame()

# 🔥 Mengambil data performa untuk semua situs di GSC
def fetch_all_data(start_date, end_date):
    service = get_service()
    if not service:
        return pd.DataFrame()

    try:
        all_sites = get_sites_list()
        combined_data = pd.DataFrame()

        for site_url in all_sites:
            site_data = get_performance_data(site_url, start_date, end_date)
            combined_data = pd.concat([combined_data, site_data], ignore_index=True)

        if combined_data.empty:
            st.warning("⚠️ Tidak ada data performa yang ditemukan untuk semua situs pada rentang tanggal yang dipilih.")

        return combined_data

    except Exception as e:
        st.error(f"❌ Error fetching all performance data: {e}")
        return pd.DataFrame()
