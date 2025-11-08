import os
import math
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Regras do projeto: usar matplotlib, 1 gráfico por figura e não definir cores explicitamente
load_dotenv()  # carrega DB_URL do .env
DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise RuntimeError("Defina DB_URL no .env (ex.: mysql+pymysql://user:pass@localhost:3306/air_quality?charset=utf8mb4)")

engine = create_engine(DB_URL, pool_pre_ping=True, future=True)

OUT_DIR = os.getenv("EDA_OUT_DIR", "./outputs")
os.makedirs(OUT_DIR, exist_ok=True)

def fetch_df(query: str, params: dict | None = None) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn, params=params)

# 1) Amostras e contagens
counts = {}
for tbl in ["cetesb_readings", "inmet_readings"]:
    q = f"SELECT COUNT(*) AS n FROM {tbl}"
    dfc = fetch_df(q)
    counts[tbl] = int(dfc.loc[0, "n"])
pd.DataFrame([counts]).to_csv(os.path.join(OUT_DIR, "00_counts.csv"), index=False)

# 2) Últimas datas por tabela
last_dates = {}
for tbl in ["cetesb_readings", "inmet_readings"]:
    q = f"SELECT MAX(dt) AS last_dt, MIN(dt) AS first_dt FROM {tbl}"
    dfc = fetch_df(q)
    last_dates[tbl] = {"first_dt": dfc.loc[0, "first_dt"], "last_dt": dfc.loc[0, "last_dt"]}
pd.DataFrame(last_dates).to_csv(os.path.join(OUT_DIR, "01_date_ranges.csv"))

# 3) Distribuição de poluentes (média e n leituras)
df_pol = fetch_df("""SELECT pollutant, COUNT(*) AS n, AVG(value) AS avg_value
FROM cetesb_readings
GROUP BY pollutant
ORDER BY n DESC
""")
df_pol.to_csv(os.path.join(OUT_DIR, "02_pollutant_overview.csv"), index=False)

# 3a) Barra: top 10 por número de leituras
top = df_pol.head(10)
plt.figure()
plt.bar(top["pollutant"], top["n"])
plt.xticks(rotation=45, ha="right")
plt.title("Top 10 poluentes por número de leituras")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "02a_pollutant_top10_count.png"), dpi=160)
plt.close()

# 4) Série temporal por hora (ex.: PM2.5) — média por hora
target_pollutant = os.getenv("EDA_POLLUTANT", "pm2_5")
df_ts = fetch_df("""SELECT DATE_FORMAT(dt, '%Y-%m-%d %H:00:00') AS hr, AVG(value) AS avg_value
FROM cetesb_readings
WHERE pollutant = :p
GROUP BY hr
ORDER BY hr
""", {"p": target_pollutant})
if not df_ts.empty:
    df_ts['hr'] = pd.to_datetime(df_ts['hr'])
    plt.figure()
    plt.plot(df_ts['hr'], df_ts['avg_value'])
    plt.title(f"Série temporal (média por hora) - {target_pollutant}")
    plt.xlabel("Hora")
    plt.ylabel("Média")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "03_timeseries_hourly.png"), dpi=160)
    plt.close()

# 5) Correlação simples: PM2.5 x Temperatura (join por hora exata)
df_corr = fetch_df("""SELECT 
  c.dt AS dt,
  c.value AS pm25,
  i.temp_c AS temp_c
FROM cetesb_readings c
JOIN inmet_readings i
  ON i.dt = c.dt
WHERE c.pollutant = :p
ORDER BY c.dt
""", {"p": target_pollutant})

if not df_corr.empty:
    df_corr = df_corr.dropna(subset=["pm25","temp_c"]).copy()
    if not df_corr.empty:
        corr_val = df_corr["pm25"].corr(df_corr["temp_c"])
        with open(os.path.join(OUT_DIR, "04_corr_pm25_temp.txt"), "w", encoding="utf-8") as f:
            f.write(f"Correlação Pearson PM2.5 x Temperatura: {corr_val:.4f}\n")

        # Dispersão
        plt.figure()
        plt.scatter(df_corr["temp_c"], df_corr["pm25"], s=10)
        plt.title("Dispersão: PM2.5 x Temperatura")
        plt.xlabel("Temperatura (°C)")
        plt.ylabel("PM2.5 (µg/m³)")
        plt.tight_layout()
        plt.savefig(os.path.join(OUT_DIR, "04_scatter_pm25_vs_temp.png"), dpi=160)
        plt.close()

print("EDA finalizada. Resultados em:", os.path.abspath(OUT_DIR))
