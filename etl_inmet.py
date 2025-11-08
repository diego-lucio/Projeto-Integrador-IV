import os
import pandas as pd
import requests
from sqlalchemy import text
from dotenv import load_dotenv
from db import get_engine

load_dotenv()

def fetch_inmet(station: str, start: str, end: str) -> pd.DataFrame:
    url = f'https://apitempo.inmet.gov.br/estacao/{start}/{end}/{station}'
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    js = r.json()
    df = pd.DataFrame(js)
    if df.empty:
        return df
    if 'DT_MEDICAO' in df.columns and 'HR_MEDICAO' in df.columns:
        df['dt'] = pd.to_datetime(df['DT_MEDICAO'] + ' ' + df['HR_MEDICAO'].astype(str).str.zfill(4).str[:2] + ':' + df['HR_MEDICAO'].astype(str).str.zfill(4).str[2:], errors='coerce')
    elif 'data' in df.columns:
        df['dt'] = pd.to_datetime(df['data'], errors='coerce')
    else:
        first = df.columns[0]
        df['dt'] = pd.to_datetime(df[first], errors='coerce')
    def _to_num(s):
        return pd.to_numeric(s, errors='coerce')
    out = pd.DataFrame({
        'station_code': station,
        'dt': df['dt'],
        'temp_c': _to_num(df.get('TEM_INS', df.get('temp', None))),
        'umid_pct': _to_num(df.get('UMD_INS', df.get('umidade', None))),
        'press_hpa': _to_num(df.get('PRE_INS', df.get('pressao', None))),
        'wind_dir_deg': _to_num(df.get('VEN_DIR', df.get('vento_direcao', None))),
        'wind_vel_mps': _to_num(df.get('VEN_VEL', df.get('vento_velocidade', None))),
        'rain_mm': _to_num(df.get('CHUVA', df.get('precip', None)))
    })
    return out.dropna(subset=['dt']).sort_values('dt')

def load_to_mysql(df: pd.DataFrame):
    if df.empty:
        print('No INMET rows to insert.')
        return
    eng = get_engine()
    sql = text(
        'INSERT INTO inmet_readings (station_code, dt, temp_c, umid_pct, press_hpa, wind_dir_deg, wind_vel_mps, rain_mm) '
        'VALUES (:station_code, :dt, :temp_c, :umid_pct, :press_hpa, :wind_dir_deg, :wind_vel_mps, :rain_mm) '
        'ON DUPLICATE KEY UPDATE temp_c=VALUES(temp_c), umid_pct=VALUES(umid_pct), press_hpa=VALUES(press_hpa), wind_dir_deg=VALUES(wind_dir_deg), wind_vel_mps=VALUES(wind_vel_mps), rain_mm=VALUES(rain_mm)'
    )
    recs = df.to_dict(orient='records')
    with eng.begin() as conn:
        conn.execute(sql, recs)
    print(f'Inserted/updated {len(recs)} INMET rows.')

def run():
    station = os.getenv('INMET_STATION','A703')
    start = os.getenv('INMET_START_DATE','2024-01-01')
    end = os.getenv('INMET_END_DATE','2024-12-31')
    print(f'Fetching INMET {station} from {start} to {end}...')
    df = fetch_inmet(station, start, end)
    load_to_mysql(df)

if __name__ == '__main__':
    run()
