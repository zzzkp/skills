#!/usr/bin/env python3
"""Shared helpers for GIS legend configuration scripts."""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    import psycopg2
except ImportError:  # pragma: no cover - reported at runtime for users.
    psycopg2 = None


SKILL_ROOT = Path(__file__).resolve().parents[1]
LOCAL_DATABASE_FILE = SKILL_ROOT / "local.database.json"

KPI_FIELDS = [
    "kpi_id",
    "net_type",
    "kpi_dim",
    "kpi_type",
    "kpi_name",
    "kpi_name_cn",
    "order_num",
    "visable",
    "colored",
    "business_name",
    "login_id",
]

COLOR_FIELDS = [
    "kpi_id",
    "min_value",
    "max_value",
    "kpi_color",
    "order_num",
]

DATABASE_ENV_MAP = {
    "host": "LEGEND_DB_HOST",
    "port": "LEGEND_DB_PORT",
    "database": "LEGEND_DB_NAME",
    "user": "LEGEND_DB_USER",
    "password": "LEGEND_DB_PASSWORD",
    "schema": "LEGEND_DB_SCHEMA",
}


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(path: str | Path, data: Dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def database_from_env() -> Dict[str, Any]:
    database: Dict[str, Any] = {}
    for key, env_name in DATABASE_ENV_MAP.items():
        value = os.getenv(env_name)
        if value:
            database[key] = int(value) if key == "port" else value
    return database


def database_from_local_file() -> Dict[str, Any]:
    database: Dict[str, Any] = {}
    for path in (LOCAL_DATABASE_FILE, Path(os.getenv("LEGEND_DB_CONFIG", ""))):
        if not str(path) or not path.exists():
            continue
        data = load_json(path)
        database.update(data.get("database", data))
    return database


def with_database_config(config: Dict[str, Any]) -> Dict[str, Any]:
    database = {}
    database.update(database_from_local_file())
    database.update(database_from_env())
    database.update(config.get("database") or {})

    required = ("host", "database", "user", "password")
    missing = [field for field in required if not database.get(field)]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(
            "Missing database config fields: "
            f"{joined}. Provide input JSON database, LEGEND_DB_* env vars, "
            "LEGEND_DB_CONFIG, or local.database.json."
        )

    database.setdefault("port", 5432)
    database.setdefault("schema", "tas_master")
    return {**config, "database": database}


def schema_name(db_config: Dict[str, Any]) -> str:
    schema = db_config.get("schema", "tas_master")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
        raise ValueError(f"Unsafe schema name: {schema!r}")
    return schema


def connect(db_config: Dict[str, Any]):
    if psycopg2 is None:
        raise RuntimeError("Missing dependency: install psycopg2-binary before querying PostgreSQL")
    return psycopg2.connect(
        host=db_config["host"],
        port=db_config.get("port", 5432),
        database=db_config["database"],
        user=db_config["user"],
        password=db_config["password"],
    )


def sql_quote(value: Any) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def target_kpi_type(target: Dict[str, Any], source: Dict[str, Any]) -> Any:
    return target.get("kpi_type") or target.get("kpiType") or source.get("kpi_type")


def sanitize_filename_part(value: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "_", value).strip() or "export"


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def unique_ints(values: Iterable[Any]) -> List[int]:
    return list(dict.fromkeys(int(value) for value in values if value is not None))
