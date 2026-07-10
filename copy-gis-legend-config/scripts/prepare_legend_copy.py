#!/usr/bin/env python3
"""Prepare GIS legend configuration copy analysis and SQL.

The script only queries source configuration with SELECT and writes local files.
It never executes generated INSERT SQL.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    import psycopg2.extras
except ImportError:  # pragma: no cover - reported at runtime for users.
    psycopg2 = None  # type: ignore[assignment]

from common import (
    KPI_FIELDS,
    connect,
    dump_json,
    load_json,
    schema_name,
    sql_quote,
    target_kpi_type,
    unique_ints,
    with_database_config,
)


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATCHING_RULES = SCRIPT_ROOT / "references" / "matching-rules.json"
DEFAULT_SCORING = {
    "candidate_threshold": 35.0,
    "name_similarity_points": 55.0,
    "normalized_exact_points": 90.0,
    "semantic_family_points": 30.0,
    "field_points": {
        "net_type": 8.0,
        "kpi_dim": 8.0,
        "kpi_type": 6.0,
    },
}


def load_matching_rules(path: Optional[str] = None) -> Dict[str, Any]:
    rules_path = Path(path) if path else DEFAULT_MATCHING_RULES
    if not rules_path.exists():
        return {
            "normalization": {"remove_pattern": r"[\s_（）()\[\]【】%％]", "stop_words": []},
            "semantic_families": [],
            "scoring": DEFAULT_SCORING,
        }
    rules = load_json(rules_path)
    rules.setdefault("normalization", {})
    rules.setdefault("semantic_families", [])
    rules["scoring"] = {**DEFAULT_SCORING, **rules.get("scoring", {})}
    rules["scoring"]["field_points"] = {
        **DEFAULT_SCORING["field_points"],
        **rules["scoring"].get("field_points", {}),
    }
    return rules


def normalize_name(value: str, rules: Dict[str, Any]) -> str:
    value = value or ""
    normalization = rules.get("normalization", {})
    value = re.sub(normalization.get("remove_pattern", r"[\s_（）()\[\]【】%％]"), "", value)
    stop_words = normalization.get("stop_words") or []
    if stop_words:
        value = re.sub("(" + "|".join(re.escape(word) for word in stop_words) + ")", "", value, flags=re.IGNORECASE)
    return value.lower()


def semantic_family(value: str, rules: Dict[str, Any]) -> Optional[str]:
    upper_value = (value or "").upper()
    for family in rules.get("semantic_families", []):
        family_name = family.get("name")
        keywords = family.get("keywords", [])
        if any(keyword.upper() in upper_value for keyword in keywords):
            return family_name
    return None


def fetch_source_kpis(db_config: Dict[str, Any], source_filter: Dict[str, Any]) -> List[Dict[str, Any]]:
    schema = schema_name(db_config)
    where = []
    params: List[Any] = []
    for field in ("business_name", "net_type", "kpi_dim", "kpi_type"):
        if source_filter.get(field):
            where.append(f"{field} = %s")
            params.append(source_filter[field])
    where_sql = " AND ".join(where) if where else "1=1"
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


def fetch_colors(db_config: Dict[str, Any], kpi_ids: Iterable[int]) -> Dict[str, List[Dict[str, Any]]]:
    ids = unique_ints(kpi_ids)
    if not ids:
        return {}
    schema = schema_name(db_config)
    query = f"""
        SELECT kpi_id, min_value, max_value, kpi_color, order_num
        FROM {schema}.cfg_gis_kpi_color
        WHERE kpi_id = ANY(%s)
        ORDER BY kpi_id, order_num
    """
    with connect(db_config) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (ids,))
            grouped: Dict[str, List[Dict[str, Any]]] = {}
            for row in cur.fetchall():
                item = dict(row)
                grouped.setdefault(str(item["kpi_id"]), []).append(item)
            return grouped


def candidate_score(target: Dict[str, Any], source: Dict[str, Any], rules: Dict[str, Any]) -> tuple[float, List[str]]:
    target_name = target.get("search") or target.get("kpi_name_cn") or ""
    source_name = source.get("kpi_name_cn") or ""
    scoring = rules.get("scoring", DEFAULT_SCORING)
    reasons: List[str] = []
    score = 0.0

    if target_name == source_name:
        return 100.0, ["指标中文名完全一致"]

    target_norm = normalize_name(target_name, rules)
    source_norm = normalize_name(source_name, rules)
    if target_norm and target_norm == source_norm:
        score += float(scoring["normalized_exact_points"])
        reasons.append("规范化名称一致")
    elif target_norm and source_norm:
        ratio = difflib.SequenceMatcher(None, target_norm, source_norm).ratio()
        score += ratio * float(scoring["name_similarity_points"])
        if ratio >= 0.55:
            reasons.append(f"名称相似度{ratio:.2f}")

    target_family = semantic_family(target_name, rules)
    source_family = semantic_family(source_name, rules)
    if target_family and target_family == source_family:
        score += float(scoring["semantic_family_points"])
        reasons.append(f"同属{target_family}类")

    for field, points in scoring.get("field_points", {}).items():
        if target.get(field) and source.get(field) and target[field] == source[field]:
            score += float(points)
            reasons.append(f"{field}一致")

    return score, reasons


def analyze(config: Dict[str, Any], source_kpis: List[Dict[str, Any]], rules: Dict[str, Any]) -> Dict[str, Any]:
    source_filter = config.get("source_filter") or config.get("filter") or {}
    target_defaults = config.get("target", {})
    results: List[Dict[str, Any]] = []
    by_name = {item.get("kpi_name_cn"): item for item in source_kpis}

    for idx, raw_target in enumerate(config.get("kpis", []), start=1):
        target = {**source_filter, **target_defaults, **raw_target}
        target_name = target.get("kpi_name_cn")
        search_name = target.get("search") or target_name
        result = {
            "index": idx,
            "target": target,
            "status": "unmatched",
            "source": None,
            "candidates": [],
            "reason": "",
        }

        exact = by_name.get(search_name)
        if exact:
            result.update(status="matched", source=exact, reason="指标中文名完全一致" if search_name == target_name else "使用search精确匹配")
            results.append(result)
            continue

        scored = []
        for source in source_kpis:
            score, reasons = candidate_score(target, source, rules)
            if score >= float(rules.get("scoring", DEFAULT_SCORING)["candidate_threshold"]):
                scored.append((score, source, reasons))

        scored.sort(key=lambda item: item[0], reverse=True)
        result["candidates"] = [
            {
                "score": round(score, 2),
                "source_kpi_id": source.get("kpi_id"),
                "source_kpi_name_cn": source.get("kpi_name_cn"),
                "source_kpi_name": source.get("kpi_name"),
                "source_kpi_type": source.get("kpi_type"),
                "source_net_type": source.get("net_type"),
                "source_kpi_dim": source.get("kpi_dim"),
                "reasons": reasons,
            }
            for score, source, reasons in scored[:8]
        ]
        if result["candidates"]:
            result["status"] = "needs_ai_decision"
            result["reason"] = "存在候选项，需要AI结合全部源指标和业务语义选择最合理复制来源"
        else:
            result["reason"] = "没有找到足够接近的候选项"
        results.append(result)

    return {
        "source_filter": source_filter,
        "target": target_defaults,
        "source_count": len(source_kpis),
        "results": results,
    }


def source_index(source_kpis: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {str(item["kpi_id"]): item for item in source_kpis}


def resolve_source(result: Dict[str, Any], sources_by_id: Dict[str, Dict[str, Any]]) -> tuple[Optional[Dict[str, Any]], str]:
    source = result.get("source")
    if source:
        return source, result.get("reason", "")
    selected = result.get("selected_source_kpi_id") or result.get("source_kpi_id")
    if selected is not None:
        return sources_by_id.get(str(selected)), result.get("decision_reason") or result.get("reason", "AI选择候选项")
    return None, result.get("reason", "")


def target_kpi_lookup_sql(schema: str, merged: Dict[str, Any]) -> List[str]:
    return [
        f"    SELECT kpi_id FROM {schema}.cfg_gis_kpi",
        f"    WHERE business_name = {sql_quote(merged['business_name'])}",
        f"      AND net_type = {sql_quote(merged['net_type'])}",
        f"      AND kpi_dim = {sql_quote(merged['kpi_dim'])}",
        f"      AND kpi_name = {sql_quote(merged['kpi_name'])}",
        "    ORDER BY kpi_id DESC",
        "    LIMIT 1",
    ]


def generate_sql(config: Dict[str, Any], analysis_data: Dict[str, Any], source_kpis: List[Dict[str, Any]], output: str) -> Dict[str, int]:
    db_config = config["database"]
    schema = schema_name(db_config)
    sources_by_id = source_index(source_kpis)
    resolved_ids = []
    for result in analysis_data.get("results", []):
        source, _ = resolve_source(result, sources_by_id)
        if source:
            resolved_ids.append(source["kpi_id"])
    colors = fetch_colors(db_config, resolved_ids)

    today = dt.datetime.now().strftime("%Y%m%d")
    lines = [
        "-- 图例配置复制SQL",
        f"-- 生成时间: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"-- 源范围: {analysis_data.get('source_filter', {})}",
        f"-- 目标: {analysis_data.get('target', {})}",
        "",
        "BEGIN;",
        "",
    ]
    matched = 0
    unresolved = 0

    for result in analysis_data.get("results", []):
        target = result.get("target") or {}
        target_name = target.get("kpi_name_cn")
        source, reason = resolve_source(result, sources_by_id)
        if not source:
            unresolved += 1
            lines.append(f"-- 未生成: {target_name}, 原因: {reason or '未找到匹配来源'}")
            lines.append("")
            continue
        if not target.get("kpi_name"):
            unresolved += 1
            lines.append(f"-- 未生成: {target_name}, 原因: 缺少目标kpi_name字段")
            lines.append("")
            continue

        matched += 1
        new_kpi_id = int(f"{today}{matched:03d}")
        merged = {
            "net_type": target.get("net_type", source.get("net_type")),
            "kpi_dim": target.get("kpi_dim", source.get("kpi_dim")),
            "kpi_type": target_kpi_type(target, source),
            "kpi_name": target["kpi_name"],
            "kpi_name_cn": target_name,
            "order_num": target.get("order_num", source.get("order_num")),
            "visable": 1,
            "colored": 1,
            "business_name": target.get("business_name", config.get("target", {}).get("business_name")),
            "login_id": None,
        }

        lines.append(f"-- 指标 {result.get('index')}: {target_name} -> 复用 {source.get('kpi_name_cn')} (source_kpi_id={source.get('kpi_id')})")
        if reason:
            lines.append(f"-- 匹配原因: {reason}")
        lines.append(f"INSERT INTO {schema}.cfg_gis_kpi (")
        lines.append("    kpi_id, net_type, kpi_dim, kpi_type, kpi_name, kpi_name_cn,")
        lines.append("    order_num, visable, colored, business_name, login_id")
        lines.append(")")
        lines.append("SELECT")
        lines.append(f"    {new_kpi_id},")
        lines.append(f"    {sql_quote(merged['net_type'])},")
        lines.append(f"    {sql_quote(merged['kpi_dim'])},")
        lines.append(f"    {sql_quote(merged['kpi_type'])},")
        lines.append(f"    {sql_quote(merged['kpi_name'])},")
        lines.append(f"    {sql_quote(merged['kpi_name_cn'])},")
        lines.append(f"    {merged['order_num'] if merged['order_num'] is not None else 'NULL'},")
        lines.append(f"    {merged['visable'] if merged['visable'] is not None else 'NULL'},")
        lines.append(f"    {merged['colored'] if merged['colored'] is not None else 'NULL'},")
        lines.append(f"    {sql_quote(merged['business_name'])},")
        lines.append(f"    {sql_quote(merged['login_id'])}")
        lines.append("WHERE NOT EXISTS (")
        lines.append(f"    SELECT 1 FROM {schema}.cfg_gis_kpi")
        lines.append(f"    WHERE business_name = {sql_quote(merged['business_name'])}")
        lines.append(f"      AND net_type = {sql_quote(merged['net_type'])}")
        lines.append(f"      AND kpi_dim = {sql_quote(merged['kpi_dim'])}")
        lines.append(f"      AND kpi_name = {sql_quote(merged['kpi_name'])}")
        lines.append(");")
        lines.append("")

        color_rows = colors.get(str(source["kpi_id"]), [])
        if int(merged.get("colored") or 0) == 1 and color_rows:
            lines.append(f"-- 颜色配置: 复用 source_kpi_id={source.get('kpi_id')}")
            lines.append(f"INSERT INTO {schema}.cfg_gis_kpi_color (")
            lines.append("    kpi_id, min_value, max_value, kpi_color, order_num")
            lines.append(")")
            lines.append("SELECT target.kpi_id, v.min_value, v.max_value, v.kpi_color, v.order_num")
            lines.append("FROM (VALUES")
            for idx, color in enumerate(color_rows):
                comma = "," if idx < len(color_rows) - 1 else ";"
                lines.append(
                    "    ("
                    f"{sql_quote(color.get('min_value'))}, "
                    f"{sql_quote(color.get('max_value'))}, "
                    f"{sql_quote(color.get('kpi_color'))}, "
                    f"{color.get('order_num') if color.get('order_num') is not None else 'NULL'}"
                    f"){comma}"
                )
            lines[-1] = lines[-1].rstrip(";")
            lines.append(") AS v(min_value, max_value, kpi_color, order_num)")
            lines.append("JOIN (")
            lines.extend(target_kpi_lookup_sql(schema, merged))
            lines.append(") target ON TRUE")
            lines.append("WHERE NOT EXISTS (")
            lines.append(f"    SELECT 1 FROM {schema}.cfg_gis_kpi_color existing")
            lines.append("    WHERE existing.kpi_id = target.kpi_id")
            lines.append("      AND existing.min_value IS NOT DISTINCT FROM v.min_value")
            lines.append("      AND existing.max_value IS NOT DISTINCT FROM v.max_value")
            lines.append("      AND existing.kpi_color IS NOT DISTINCT FROM v.kpi_color")
            lines.append("      AND existing.order_num IS NOT DISTINCT FROM v.order_num")
            lines.append(");")
            lines.append("")
        elif int(merged.get("colored") or 0) == 1:
            lines.append(f"-- 颜色配置: source_kpi_id={source.get('kpi_id')} 没有颜色行，未生成颜色插入")
            lines.append("")

    lines.append(f"-- 统计: 生成 {matched} 条, 未生成 {unresolved} 条")
    lines.append("COMMIT;")
    Path(output).write_text("\n".join(lines), encoding="utf-8")
    return {"generated": matched, "unresolved": unresolved}


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare GIS legend configuration copy SQL")
    parser.add_argument("--input", "-i", required=True, help="Input request JSON")
    parser.add_argument("--analysis", help="Write match analysis JSON")
    parser.add_argument("--decisions", help="Read AI decisions JSON; defaults to --analysis data when omitted")
    parser.add_argument("--output", "-o", help="Write SQL output")
    parser.add_argument("--matching-rules", help="Optional matching rules JSON; defaults to references/matching-rules.json")
    args = parser.parse_args()

    config = with_database_config(load_json(args.input))
    source_filter = config.get("source_filter") or config.get("filter")
    if not source_filter:
        raise SystemExit("Input JSON must contain source_filter or filter")
    if "kpis" not in config:
        raise SystemExit("Input JSON must contain kpis")

    rules = load_matching_rules(args.matching_rules)
    source_kpis = fetch_source_kpis(config["database"], source_filter)
    analysis_data = load_json(args.decisions) if args.decisions else analyze(config, source_kpis, rules)

    if args.analysis:
        dump_json(args.analysis, analysis_data)
    if args.output:
        stats = generate_sql(config, analysis_data, source_kpis, args.output)
        print(json.dumps(stats, ensure_ascii=False))
    elif not args.analysis:
        print(json.dumps(analysis_data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
