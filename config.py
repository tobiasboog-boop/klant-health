"""
Funnel Configuratie
===================
Methodiek (pijlers, weekfasen, KPI-targets) + interne-medewerkersfilter.

Vertrouwelijke data (top_12, klant_omzet, omzet_totalen) staat NIET in deze
repo, maar wordt at-runtime uit RAAS geladen (app_intern.lead_funnel_config).
Beheren kan via db.save_funnel_config(...).
"""
from dotenv import load_dotenv

load_dotenv()

FUNNEL_CONFIG = {
    "pijlers": ["Rendement", "Liquiditeit", "Resource Planning", "Capaciteitsplanning"],
    "huidige_pijler": 0,  # index: 0=Rendement
    "cyclus_startdatum": "2026-02-02",  # Start pijler Rendement
    "weekfasen": {
        1: {"naam": "Norm", "beschrijving": "Professionele standaard neerzetten. Zelfreflectie triggeren."},
        2: {"naam": "Frictie", "beschrijving": "Spanning zichtbaar maken. Urgentie verhogen."},
        3: {"naam": "Autoriteit", "beschrijving": "Webinar. Bewijzen dat je weet hoe het moet."},
        4: {"naam": "Concretisering", "beschrijving": "Persoonlijk maken. Van theorie naar praktijk."},
    },
    "kpi_targets": {
        "toolgebruikers": (40, 60),
        "webinar_deelnemers": (15, 25),
        "gesprekken": (25, 35),
        "nieuwe_klanten_upsells": (8, 12),
    },
    # Vertrouwelijk — leeg in git; wordt uit RAAS geladen (zie hieronder).
    "top_12": [],
    "klant_omzet": {},
    "omzet_totalen": {},
}

# Laad vertrouwelijke funnel-data uit RAAS (Azure SQL). Faalt stil naar leeg
# (bijv. lokaal zonder RAAS-creds) zodat de app blijft draaien.
try:
    from db import load_funnel_config as _load_funnel_config
    _conf = _load_funnel_config()
    for _key in ("top_12", "klant_omzet", "omzet_totalen"):
        if _conf.get(_key):
            FUNNEL_CONFIG[_key] = _conf[_key]
except Exception:
    pass

# Interne medewerkers uitsluiten uit Power BI views
INTERNE_MEDEWERKERS = [
    "mark leenders", "tobias boog", "arthur gartz",
    "chloe", "chloë", "notifica",
]
