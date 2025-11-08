# Metabase – Template de Dashboard

Este diretório contém um **template inicial** para importar no Metabase.
> Observação: IDs de banco/tabela variam por instância; após importar, ajuste as **referências** para seu MySQL.

## Passos
1. Suba o Metabase (via `docker compose up -d`). Acesse `http://localhost:3000` e crie o admin.
2. Adicione a fonte **MySQL** apontando para o serviço `mysql` (host `mysql`, porta `3306`, DB `air_quality`).
3. Vá em **Admin > Troubleshooting > Serialization** e importe o arquivo `starter_dashboard.json` (ou use a API `/api` com `curl`/Postman).
4. Abra o dashboard importado e **edite cada card** para apontar para as tabelas certas.

Conteúdo do template:
- **Dash – Air Quality Starter**
  - *Card:* Contagem CETESB/INMET
  - *Card:* Top 10 poluentes por #leituras
  - *Card:* Série horária (PM2.5)
  - *Card:* Correlação (PM2.5 × Temp) — instrução de criar gráfico de dispersão via UI
