#!/usr/bin/env python3
"""Export GIS legend configuration tables to CSV with read-only queries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    import psycopg2.extras
except ImportError:  # pragma: no cover - reported at runtime for users.
    psycopg2 = None  # type: ignore[assignment]

from common import (
    COLOR_FIELDS,
    KPI_FIELDS,
    connect,
    load_json,
    sanitize_filename_part,
    schema_name,
    unique_ints,
    with_database_config,
    write_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export GIS legend configuration tables to CSV")
    parser.add_argument("--business-name", help="Business/module name, e.g. 统一GIS-V2")
    parser.add_argument("--net-type", help="Optional net_type filter")
    parser.add_argument("--kpi-dim", help="Optional kpi_dim filter")
    parser.add_argument("--input", "-i", help="Optional input JSON for filter/database overrides")
    parser.add_argument("--output-dir", "-o", required=True, help="Directory to write CSV files into")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> Dict[str, Any]:
    raw_config = load_json(args.input) if args.input else {}
    config = with_database_config(raw_config)
    filter_config = dict(config.get("filter") or config.get("source_filter") or {})

    if args.business_name:
        filter_config["business_name"] = args.business_name
    if args.net_type:
        filter_config["net_type"] = args.net_type
    if args.kpi_dim:
        filter_config["kpi_dim"] = args.kpi_dim

    if not filter_config.get("business_name"):
        raise SystemExit("business_name is required via --business-name or input JSON filter")

    return {
        "database": config["database"],
        "filter": filter_config,
        "output_dir": args.output_dir,
    }


def build_where_clause(filters: Dict[str, Any]) -> tuple[str, List[Any]]:
    where = []
    params: List[Any] = []
    for field in ("business_name", "net_type", "kpi_dim"):
        value = filters.get(field)
        if value:
            where.append(f"{field} = %s")
            params.append(value)
    return (" AND ".join(where) if where else "1=1"), params


def fetch_kpis(db_config: Dict[str, Any], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    schema = schema_name(db_config)
    where_sql, params = build_where_clause(filters)
    fields_sql = ", ".join(KPI_FIELDS)
    query = f"""
        SELECT {fields_sql}
        FROM {schema}.cfg_gis_kpi
        WHERE {where_sql}
        ORDER BY order_num NULLS LAST, kpi_id
    """
    with connect(db_config) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]


def fetch_colors(db_config: Dict[str, Any], kpi_ids: Iterable[Any]) -> List[Dict[str, Any]]:
    normalized_ids = unique_ints(kpi_ids)
    if not normalized_ids:
        return []
    schema = schema_name(db_config)
    fields_sql = ", ".join(COLOR_FIELDS)
    query = f"""
        SELECT {fields_sql}
        FROM {schema}.cfg_gis_kpi_color
        WHERE kpi_id = ANY(%s)
        ORDER BY kpi_id, order_num
    """
    with connect(db_config) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (normalized_ids,))
            return [dict(row) for row in cur.fetchall()]


def export_csv(config: Dict[str, Any]) -> Dict[str, Any]:
    filters = config["filter"]
    db_config = config["database"]
    business_name = filters["business_name"]
    output_dir = Path(config["output_dir"])
    file_prefix = sanitize_filename_part(business_name)

    kpis = fetch_kpis(db_config, filters)
    colors = fetch_colors(db_config, [row["kpi_id"] for row in kpis])

    kpi_path = output_dir / f"{file_prefix}_cfg_gis_kpi.csv"
    color_path = output_dir / f"{file_prefix}_cfg_gis_kpi_color.csv"
    write_csv(kpi_path, kpis, KPI_FIELDS)
    write_csv(color_path, colors, COLOR_FIELDS)

    return {
        "business_name": business_name,
        "kpi_count": len(kpis),
        "color_count": len(colors),
        "kpi_csv": str(kpi_path),
        "color_csv": str(color_path),
    }


def main() -> None:
    args = parse_args()
    config = build_config(args)
    result = export_csv(config)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
