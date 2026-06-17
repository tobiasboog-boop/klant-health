"""Database helper voor klant-health dashboard (PostgreSQL op VPS3).

Schema klant_health met: powerbi_cache, klantreis_fasen, manual_bellijst, funnel_config.

Alle verbindingsgegevens komen uit environment variabelen (NOOIT hardcoded):
    STREAMLIT_DB_HOST
    STREAMLIT_DB_PORT     (optioneel, default 5432)
    STREAMLIT_DB_NAME
    STREAMLIT_DB_USER
    STREAMLIT_DB_PASSWORD
    STREAMLIT_DB_SCHEMA   (optioneel, default 'klant_health')
"""

import io
import os
import json
import psycopg2
from psycopg2.extras import Json
import pandas as pd


def _schema() -> str:
    return os.environ.get("STREAMLIT_DB_SCHEMA", "klant_health")


def _get_connection():
    host = os.environ.get("STREAMLIT_DB_HOST")
    user = os.environ.get("STREAMLIT_DB_USER")
    password = os.environ.get("STREAMLIT_DB_PASSWORD")
    dbname = os.environ.get("STREAMLIT_DB_NAME")
    port = int(os.environ.get("STREAMLIT_DB_PORT", "5432"))

    if not all([host, user, password, dbname]):
        raise RuntimeError(
            "Streamlit-DB credentials ontbreken. Zet STREAMLIT_DB_HOST / _NAME / "
            "_USER / _PASSWORD in .env."
        )
    return psycopg2.connect(host=host, port=port, user=user, password=password,
                            dbname=dbname, connect_timeout=10)


def check_connection() -> tuple[bool, str]:
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        conn.close()
        return True, "Verbonden"
    except Exception as e:
        return False, str(e)


# === Klantreis Fasen ===

def load_klantreis_fasen() -> dict:
    """Laad klantreis-fasen per email. Returns {email: fase}."""
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT email, fase FROM {_schema()}.klantreis_fasen")
        result = {row[0]: row[1] for row in cur.fetchall()}
        conn.close()
        return result
    except Exception:
        return {}


def save_klantreis_fasen(fasen: dict) -> bool:
    """Sla klantreis-fasen op. Returns True bij succes."""
    try:
        conn = _get_connection()
        cur = conn.cursor()
        for email, fase in fasen.items():
            cur.execute(
                f"INSERT INTO {_schema()}.klantreis_fasen (email, fase, updated_at) "
                f"VALUES (%s, %s, now()) "
                f"ON CONFLICT (email) DO UPDATE SET fase = EXCLUDED.fase, updated_at = now()",
                (email, fase)
            )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


# === Handmatige Bellijst ===

def load_manual_bellijst() -> list:
    """Laad handmatige bellijst."""
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT data FROM {_schema()}.manual_bellijst ORDER BY updated_at DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            return row[0] if isinstance(row[0], list) else json.loads(row[0])
        return []
    except Exception:
        return []


def save_manual_bellijst(entries: list) -> bool:
    """Sla handmatige bellijst op. Returns True bij succes."""
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {_schema()}.manual_bellijst")
        cur.execute(f"INSERT INTO {_schema()}.manual_bellijst (data) VALUES (%s)", (Json(entries),))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


# === Power BI Cache ===

def save_powerbi_cache(file_bytes: bytes, validated_df=None) -> bool:
    """Sla Power BI Excel op als parquet-blob. Returns True bij succes.
    Als validated_df meegegeven wordt, gebruik die (al genormaliseerd + gemapped)."""
    try:
        if validated_df is not None:
            df = validated_df
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))
            _aliases = {"Workspace name": "Pipedrive organisatie", "DisplayName": "Name"}
            rename_map = {old: new for old, new in _aliases.items() if old in df.columns and new not in df.columns}
            if rename_map:
                df = df.rename(columns=rename_map)
        parquet_buf = io.BytesIO()
        df.to_parquet(parquet_buf, index=False)

        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {_schema()}.powerbi_cache")
        cur.execute(
            f"INSERT INTO {_schema()}.powerbi_cache (data, rows_count) VALUES (%s, %s)",
            (psycopg2.Binary(parquet_buf.getvalue()), len(df))
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def load_powerbi_cache():
    """Laad Power BI data uit de DB. Returns (DataFrame, source, status) of (None, 'none', 'upload_nodig')."""
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT data FROM {_schema()}.powerbi_cache ORDER BY updated_at DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            df = pd.read_parquet(io.BytesIO(bytes(row[0])))
            return df, "db", "cache"
    except Exception:
        pass
    return None, "none", "upload_nodig"


# === Funnel-config (vertrouwelijk: top_12, klant_omzet, omzet_totalen) ===

def load_funnel_config() -> dict:
    """Laad de vertrouwelijke funnel-config. Returns {} bij ontbrekende data."""
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT data FROM {_schema()}.funnel_config ORDER BY updated_at DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            return row[0] if isinstance(row[0], dict) else json.loads(row[0])
    except Exception:
        pass
    return {}


def save_funnel_config(config: dict) -> bool:
    """Sla de funnel-config op als JSON. Returns True bij succes."""
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {_schema()}.funnel_config")
        cur.execute(f"INSERT INTO {_schema()}.funnel_config (data) VALUES (%s)", (Json(config),))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False
