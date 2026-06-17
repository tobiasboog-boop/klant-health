# Klant Health — Sales & Customer Dashboard

Intern Notifica-dashboard dat **lead engagement** en **klant-health** samenbrengt
in één actiegericht overzicht voor het sales-/accountteam. Standalone Streamlit-app;
wordt via de Notifica-app draft-functionaliteit op VPS4 gedeployd.

## Tabbladen

- **Acties Vandaag** — top HOT/Warm leads + at-risk klanten en upsell-kansen, met CSV-export.
- **Lead Analyse** — volledige lead-tabel met engagement-scoring + website-bezoekers.
- **Klant Health** — Power BI rapport-gebruik per organisatie → **Groen / Oranje / Rood**, per-klant drill-down, Pipedrive-contacten.

## Customer Health scoring

| Status | Criteria |
|--------|----------|
| **Rood** | Geen views in de recente periode |
| **Oranje** | Dalende trend (>25% minder) of slechts 1 gebruiker |
| **Groen** | Stabiel/stijgend, meerdere gebruikers |

Logica: `calculate_customer_health()` in [data.py](data.py).

## Databronnen

| Bron | Gebruikt voor |
|------|---------------|
| Power BI Admin API | Report-views per organisatie (klant-health) |
| Azure SQL (`app_intern.lead_*`) | Opslag: PBI-cache, klantreis-fasen, bellijst, funnel-config |
| Pipedrive | Klant-contacten + lead-verrijking |
| EmailOctopus | Email opens/clicks (lead-scoring) |
| Cloudflare Worker | Website-bezoeken per bedrijf |

> **Geen secrets of vertrouwelijke data in deze repo.** Alle credentials staan in
> `.env` (zie `.env.example`). Vertrouwelijke funnel-data (top-12, klant-omzet,
> totalen) en de bezoekers-mapping staan **niet** in git — die worden at-runtime
> uit Azure SQL (`app_intern.lead_funnel_config`) resp. de Cloudflare-API geladen.

## Lokaal draaien

```bash
pip install -r requirements.txt
cp .env.example .env   # vul de waarden in
python -m streamlit run app.py
```

Opent op `http://localhost:8501`. Zonder `APP_PASSWORD` (env) of `[auth].password`
(`.streamlit/secrets.toml`) is er geen wachtwoord-gate; zodra die gezet is, vraagt de app erom.

## Deploy (Notifica-app, draft)

Registreer een draft via **App Beheer → Streamlit Instances → Nieuwe Draft**:
`git_repo_url` = deze repo, branch = `main`, submap leeg. Zet de env-vars op de
deployment en klik **Deploy**. URL: `https://app.notifica.nl/apps/klant-health/`.

## Power BI data verversen

Het live-pad toont de laatste cache uit Azure SQL (`app_intern.lead_powerbi_cache`).
Verversen kan via een Power BI "Activity Report Views"-Excel (upload → validatie →
`save_powerbi_cache`) of via de Admin API (`fetch_powerbi_api_data` in [data.py](data.py)).
