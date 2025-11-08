# Pipeline de Dados – Qualidade do Ar (Votorantim/Sorocaba)

[![Python](https://img.shields.io/badge/Python-3.11-blue)]() [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)]() [![Made with ❤️ in SP](https://img.shields.io/badge/Made%20in-São%20Paulo-red)]()

Automatiza a ingestão de **CETESB (qualidade do ar)** e **INMET (meteorologia)** para um **MySQL**, preparando a base para análises, ML e dashboards.

## 📦 Conteúdo
- `sql/db_schema.sql` — Criação do banco e tabelas.
- `scripts/db.py` — Helper de conexão via SQLAlchemy.
- `scripts/etl_cetesb.py` — Importa CSV da CETESB (ou fallback OpenAQ).
- `scripts/etl_inmet.py` — Importa dados horários do INMET (API).
- `pipeline.py` — Orquestra a execução dos dois ETLs.
- `config/.env.example` — Exemplo de configuração (.env).
- `requirements.txt` — Dependências Python.

## ⚙️ Pré-requisitos
- Python 3.10+
- MySQL 8+
- Criar um `.env` a partir de `config/.env.example` (na raiz do projeto).

## 🗄️ Banco de Dados
1. Suba o MySQL e crie o schema:
```sql
SOURCE sql/db_schema.sql;
```
2. Confirme usuário/senha e defina `DB_URL` no `.env`, por exemplo:
```env
DB_URL=mysql+pymysql://root:root@localhost:3306/air_quality?charset=utf8mb4
```

## 🧪 Ambiente Python
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp config/.env.example .env
# edite .env conforme necessário
```

## 📥 CETESB – Como obter o CSV
1. Acesse **https://qualar.cetesb.sp.gov.br/qualar/home.do**.
2. Menu **Consulta → Dados Horários**.
3. Selecione **Estação Sorocaba – Parque Vitória Régia** e os poluentes desejados (ex.: PM2.5, PM10, CO, NO2).
4. Exporte **CSV** e salve (ex.: `./data/cetesb_sorocaba_2024.csv`).
5. No `.env`, ajuste:
```env
CETESB_CSV_PATH=./data/cetesb_sorocaba_2024.csv
CETESB_STATION_CODE=29053002
CETESB_STATION_NAME=Sorocaba - Parque Vitória Régia
```
> Se você tiver um **URL direto** para o CSV, use `CETESB_CSV_URL`. Se nenhum for definido, o script tenta **OpenAQ (Sorocaba)** como fallback.

## 🌦️ INMET – API
Edite no `.env`:
```env
INMET_STATION=A703
INMET_START_DATE=2024-01-01
INMET_END_DATE=2024-12-31
```

## ▶️ Executar o Pipeline
```bash
python pipeline.py
```
Isso vai:
1) carregar a CETESB (CSV local/URL ou OpenAQ) → `cetesb_readings`
2) carregar INMET (API) → `inmet_readings`

## 🧩 Dicas de Uso
- Chave primária evita duplicidades (UPSERT).
- Depois de populado, consulte a *view* `vw_air_quality_join` para análises rápidas.
- Para dashboards (Power BI/Metabase), a conexão no MySQL já estará pronta.

## 🛠️ Troubleshooting
- **Erro de conexão DB_URL**: confira usuário/senha/host/porta no `.env`.
- **CSV CETESB com layout diferente**: ajuste parsing em `scripts/etl_cetesb.py` (_read_cetesb_csv).
- **Sem dados OpenAQ**: baixe manualmente o CSV da CETESB e aponte `CETESB_CSV_PATH`.


---

## 🐳 Docker Compose (MySQL + Adminer + Metabase)
1. Copie `.env.docker` para `.env` (ou exporte as variáveis no shell):
```bash
cp .env.docker .env
```
2. Suba a stack:
```bash
docker compose up -d
```
3. Acesse:
- Adminer: http://localhost:8080  (Server: `mysql`, User: `${MYSQL_USER}` ou `root`)
- Metabase: http://localhost:3000  (configure a conexão MySQL `aq_mysql`)

## 📊 EDA inicial (gráficos e CSVs)
Com o banco já populado, rode:
```bash
python scripts/eda_initial.py
```
Saídas ficam em `./outputs`:
- `00_counts.csv` — contagem de registros por tabela
- `01_date_ranges.csv` — intervalo de datas
- `02_pollutant_overview.csv` e `02a_pollutant_top10_count.png`
- `03_timeseries_hourly.png` — série por hora do poluente-alvo (padrão: pm2_5)
- `04_corr_pm25_temp.txt` e `04_scatter_pm25_vs_temp.png`

Para trocar o poluente, defina `EDA_POLLUTANT` no `.env`.


---

## 🚀 ETL em Container (serviço no docker-compose)
O `docker-compose.yml` agora inclui um serviço **etl** que constrói a imagem a partir de `Dockerfile.etl`, instala dependências e executa `pipeline.py` automaticamente.

### Subir tudo (DB + Adminer + Metabase + ETL)
```bash
cp .env.docker .env          # ou exporte as variáveis do compose
docker compose up -d --build  # constrói a imagem do ETL e sobe a stack
```

### Execução periódica
- Por padrão, o ETL roda **a cada 60 min** (variável `ETL_INTERVAL_MINUTES`).
- Para rodar **uma única vez**, remova `ETL_INTERVAL_MINUTES` do serviço `etl` no compose.

### Logs do ETL
```bash
docker compose logs -f etl
```

## 🧰 Publicar no GitHub
1. Crie um novo repositório no GitHub.
2. Execute no diretório do projeto:
```bash
git init
git add .
git commit -m "feat: ETL + Docker + EDA inicial"
git branch -M main
git remote add origin https://github.com/<usuario>/<repositorio>.git
git push -u origin main
```


---

## ✅ GitHub Actions (CI)
Workflow em `.github/workflows/ci.yml`:
- Sobe MySQL 8 como **service**
- Instala dependências
- Aplica `sql/db_schema.sql`
- Executa `pipeline.py` (usa OpenAQ como fallback se não houver CSV)
- Roda `scripts/eda_initial.py`
- Faz `docker build` do ETL

### Rodando localmente com Makefile
```bash
make install
make etl
make eda
```

## 📊 Metabase – Template
Importe `metabase/starter_dashboard.json` (Serialization) e ajuste as fontes. Veja `metabase/README.md`.
