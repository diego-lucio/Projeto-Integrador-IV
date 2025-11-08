import os
import io
import pandas as pd
import requests
from sqlalchemy import text
from dotenv import load_dotenv
from db import get_engine

load_dotenv()

def _read_cetesb_csv(path_or_bytes) -> pd.DataFrame:
    if isinstance(path_or_bytes, (bytes, bytearray)):
        data = io.BytesIO(path_or_bytes)
    else:
        data = path_or_bytes
    df = pd.read_csv(data, sep=';', engine='python', encoding='latin1', dtype=str)
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    if {'data','hora'}.issubset(df.columns):
        df['dt'] = pd.to_datetime(df['data'] + ' ' + df['hora'], dayfirst=True, errors='coerce')
    elif 'datahora' in df.columns:
        df['dt'] = pd.to_datetime(df['datahora'], errors='coerce')
    else:
        first = df.columns[0]
        df['dt'] = pd.to_datetime(df[first], errors='coerce')
    return df

def _melt_pollutants(df: pd.DataFrame) -> pd.DataFrame:
    keep = {'dt','data','hora','date','time','unidade','estacao','estação','local'}
    meta_cols = [c for c in df.columns if c in keep]
    if 'dt' not in meta_cols:
        meta_cols = ['dt'] + meta_cols
    value_cols = [c for c in df.columns if c not in meta_cols]
    long = df.melt(id_vars=meta_cols, value_vars=value_cols, var_name='pollutant', value_name='value_raw')
    # decimal comma -> dot
    long['value'] = (
        long['value_raw'].astype(str)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
    )
    long['value'] = pd.to_numeric(long['value'], errors='coerce')
    # Extract unit if present in header: e.g., pm2_5(µg/m3)
    ext = long['pollutant'].str.extract(r'^([^()]+)(?:\(([^)]+)\))?')
    long['pollutant'] = ext[0].str.strip().str.lower()
    long['unit'] = ext[1].str.strip()
    return long

def load_to_mysql(df_long: pd.DataFrame):
    engine = get_engine()
    station_code = os.getenv('CETESB_STATION_CODE','')
    station_name = os.getenv('CETESB_STATION_NAME','')
    rows = []
    for _, r in df_long.iterrows():
        if pd.isna(r.get('dt')) or pd.isna(r.get('pollutant')):
            continue
        rows.append({
            'station_code': station_code,
            'station_name': station_name,
            'dt': pd.to_datetime(r['dt']).to_pydatetime(),
            'pollutant': str(r['pollutant']).lower(),
            'value': None if pd.isna(r.get('value')) else float(r['value']),
            'unit': None if pd.isna(r.get('unit')) else str(r['unit']),
            'valid_flag': None,
            'source': 'CETESB'
        })
    if not rows:
        print('No rows to insert.')
        return
    sql = text(
        "INSERT INTO cetesb_readings (station_code, station_name, dt, pollutant, value, unit, valid_flag, source) "
        "VALUES (:station_code, :station_name, :dt, :pollutant, :value, :unit, :valid_flag, :source) "
        "ON DUPLICATE KEY UPDATE value=VALUES(value), unit=VALUES(unit), station_name=VALUES(station_name)"
    )
    with engine.begin() as conn:
        conn.execute(sql, rows)
    print(f'Inserted/updated {len(rows)} CETESB rows.')

def run():
    csv_url = os.getenv('CETESB_CSV_URL','').strip()
    csv_path = os.getenv('CETESB_CSV_PATH','').strip()
    if csv_url:
        print(f'Downloading CETESB CSV from {csv_url}...')
        resp = requests.get(csv_url, timeout=60)
        resp.raise_for_status()
        df = _read_cetesb_csv(resp.content)
    elif csv_path and os.path.exists(csv_path):
        print(f'Reading CETESB CSV from local path {csv_path}...')
        df = _read_cetesb_csv(csv_path)
    else:
        # Fallback: OpenAQ latest by city
        city = os.getenv('OPENAQ_CITY','Sorocaba')
        print(f'No CETESB CSV defined. Using OpenAQ latest for {city}...')
        r = requests.get(f'https://api.openaq.org/v2/latest?city={city}', timeout=60)
        js = r.json().get('results', [])
        recs = []
        for st in js:
            stname = st.get('location')
            for m in st.get('measurements', []):
                recs.append({'dt': pd.to_datetime(m.get('lastUpdated')), 'pollutant': m.get('parameter'), 'value': m.get('value'), 'unit': m.get('unit'), 'station_name': stname})
        df = pd.DataFrame(recs)
        if df.empty:
            print('OpenAQ returned no data. Abort.')
            return
        # Adapt to long schema already
        df['pollutant'] = df['pollutant'].str.lower()
        df_long = df.rename(columns={'dt':'dt','value':'value','unit':'unit'})
        load_to_mysql(df_long)
        return
    df_long = _melt_pollutants(df)
    load_to_mysql(df_long)

if __name__ == '__main__':
    run()
