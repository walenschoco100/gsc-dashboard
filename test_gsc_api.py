from google.oauth2 import service_account
from googleapiclient.discovery import build

# Konfigurasi Google Search Console API
SERVICE_ACCOUNT_FILE = 'credentials/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('searchconsole', 'v1', credentials=credentials)

# Mengatur parameter permintaan API
site_url = "https://amutatbh.com"  # Ganti dengan situs Anda
request = {
    'startDate': '2024-01-01',
    'endDate': '2025-01-01',
    'dimensions': ['date'],  # Hanya mengambil data berdasarkan tanggal
    'rowLimit': 1000
}

# Menjalankan permintaan API dan menampilkan hasilnya
try:
    response = service.searchanalytics().query(siteUrl=site_url, body=request).execute()
    print(f"API Response for {site_url}: {response}")
    
    # Menampilkan data secara terstruktur jika ada
    if 'rows' in response:
        for row in response['rows']:
            date = row['keys'][0]
            clicks = row.get('clicks', 0)
            impressions = row.get('impressions', 0)
            ctr = row.get('ctr', 0.0)
            position = row.get('position', 0.0)
            print(f"Date: {date}, Clicks: {clicks}, Impressions: {impressions}, CTR: {ctr}, Position: {position}")
    else:
        print(f"No data found for {site_url} in the given date range.")

except Exception as e:
    print(f"Error fetching data for {site_url}: {e}")
