import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Path ke file credentials.json
SERVICE_ACCOUNT_FILE = 'credentials/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

# Inisialisasi API GSC
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('searchconsole', 'v1', credentials=credentials)

# Mengambil semua properti situs di GSC
def get_sites_list():
    sites = service.sites().list().execute()
    site_list = [site['siteUrl'] for site in sites['siteEntry'] if site['permissionLevel'] != 'siteUnverifiedUser']
    print(f"Sites Found: {site_list}")
    return site_list

# Mengambil data performa dari satu domain dengan queries, pages, dan country
def get_performance_data(site_url, start_date='2024-01-01', end_date='2025-01-01'):
    request = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['query', 'page', 'country'],  # Menambahkan 'country' sebagai dimensi tambahan
        'rowLimit': 1000
    }
    try:
        response = service.searchanalytics().query(siteUrl=site_url, body=request).execute()
        print(f"API Response for {site_url}: {response}")
        
        if 'rows' not in response or not response['rows']:
            print(f"No data found for {site_url} in the given date range.")
            return pd.DataFrame()
        
        rows = []
        for row in response['rows']:
            rows.append([
                site_url, 
                row['keys'][0] if len(row['keys']) > 0 else '',  # query
                row['keys'][1] if len(row['keys']) > 1 else '',  # page
                row['keys'][2] if len(row['keys']) > 2 else '',  # country
                row.get('clicks', 0), 
                row.get('impressions', 0), 
                row.get('ctr', 0.0), 
                row.get('position', 0.0)
            ])
        
        return pd.DataFrame(rows, columns=['Site', 'Query', 'Page', 'Country', 'Clicks', 'Impressions', 'CTR', 'Position'])
    
    except Exception as e:
        print(f"Error fetching data for {site_url}: {e}")
        return pd.DataFrame()

# Menggabungkan data dari semua domain dengan queries, pages, dan country
def fetch_all_data(start_date='2024-01-01', end_date='2025-01-01'):
    all_sites = get_sites_list()
    combined_data = pd.DataFrame()
    
    for site in all_sites:
        print(f"Fetching data for {site}...")
        site_data = get_performance_data(site, start_date, end_date)
        combined_data = pd.concat([combined_data, site_data], ignore_index=True)
    
    return combined_data
