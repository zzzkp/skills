#!/usr/bin/env python3
"""Collect GitLab push commits and code-change evidence for a work report."""

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
from datetime import date, datetime, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


ZERO_SHA_RE = re.compile(r"^0+$")


def configure_utf8_output() -> None:
    """Keep JSON and error messages readable when Windows captures native output."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class GitLabApiError(RuntimeError):
    """Represent an actionable GitLab API error."""


class GitLabClient:
    def __init__(self, base_url: str, token: str, insecure: bool = False) -> None:
        self.base_url = normalize_base_url(base_url)
        self.api_url = f"{self.base_url}/api/v4"
        self.headers = {
            "PRIVATE-TOKEN": token,
            "Accept": "application/json",
            "User-Agent": "summarize-gitlab-work/1.0",
        }
        self.ssl_context = ssl.create_default_context()
        if insecure:
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE

    def get(self, path: str, params: dict[str, Any] | None = None) -> tuple[Any, Any]:
        query = urlencode(params or {}, doseq=True)
        url = f"{self.api_url}{path}"
        if query:
            url = f"{url}?{query}"
        request = Request(url, headers=self.headers, method="GET")
        try:
            with urlopen(request, context=self.ssl_context, timeout=60) as response:
                payload = response.read().decode("utf-8")
                return json.loads(payload), response.headers
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise GitLabApiError(f"GitLab API 请求失败：HTTP {exc.code}，{body}") from exc
        except URLError as exc:
            raise GitLabApiError(f"无法访问 GitLab：{exc.reason}") from exc

    def get_all(self, path: str, params: dict[str, Any] | None = None) -> list[Any]:
        page = 1
        result: list[Any] = []
        base_params = dict(params or {})
        while True:
            page_params = {**base_params, "page": page, "per_page": 100}
            data, headers = self.get(path, page_params)
            if not isinstance(data, list):
                raise GitLabApiError(f"分页接口返回了非列表数据：{path}")
            result.extend(data)
            next_page = headers.get("X-Next-Page", "").strip()
            if next_page:
                page = int(next_page)
                continue
            if len(data) < 100:
                break
            page += 1
        return result


def normalize_base_url(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("GitLab 地址不能为空")
    if "://" not in normalized:
        normalized = f"https://{normalized}"
    parsed = urlsplit(normalized)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"无效的 GitLab 地址：{value}")
    return f"{parsed.scheme}://{parsed.netloc}"


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("日期必须使用 YYYY-MM-DD 格式") from exc


def resolve_date_range(start_date: date | None, end_date: date | None) -> tuple[date, date]:
    today = datetime.now().astimezone().date()
    resolved_end = end_date or today
    resolved_start = start_date or (resolved_end - timedelta(days=resolved_end.weekday()))
    if resolved_start > resolved_end:
        raise ValueError("开始日期不能晚于结束日期")
    return resolved_start, resolved_end


def parse_event_date(value: str) -> date:
    event_time = datetime.fromisoformat(value.replace("Z", "+00:00"))
    local_timezone = datetime.now().astimezone().tzinfo
    return event_time.astimezone(local_timezone).date()


def is_zero_sha(value: str | None) -> bool:
    return not value or bool(ZERO_SHA_RE.fullmatch(value))


def changed_lines_excerpt(diff_text: str, limit: int) -> tuple[str, bool]:
    selected: list[str] = []
    for line in diff_text.splitlines():
        is_change = (
            (line.startswith("+") and not line.startswith("+++"))
            or (line.startswith("-") and not line.startswith("---"))
        )
        if line.startswith("@@") or is_change:
            selected.append(line)
    excerpt = "\n".join(selected)
    if len(excerpt) <= limit:
        return excerpt, False
    return f"{excerpt[:limit]}\n... [diff excerpt truncated]", True


def normalize_diffs(diffs: list[dict[str, Any]], total_limit: int) -> list[dict[str, Any]]:
    if not diffs:
        return []
    per_file_limit = max(120, total_limit // len(diffs))
    normalized: list[dict[str, Any]] = []
    for item in diffs:
        excerpt, truncated = changed_lines_excerpt(item.get("diff") or "", per_file_limit)
        normalized.append(
            {
                "old_path": item.get("old_path"),
                "new_path": item.get("new_path"),
                "new_file": bool(item.get("new_file")),
                "renamed_file": bool(item.get("renamed_file")),
                "deleted_file": bool(item.get("deleted_file")),
                "excerpt": excerpt,
                "excerpt_truncated": truncated,
            }
        )
    return normalized


def fetch_commit(
    client: GitLabClient,
    project_id: int,
    commit_sha: str,
    diff_limit: int,
) -> dict[str, Any]:
    detail, _ = client.get(f"/projects/{project_id}/repository/commits/{commit_sha}")
    diffs = client.get_all(f"/projects/{project_id}/repository/commits/{commit_sha}/diff")
    return {
        "id": detail.get("id"),
        "short_id": detail.get("short_id"),
        "title": detail.get("title"),
        "message": detail.get("message"),
        "author_name": detail.get("author_name"),
        "author_email": detail.get("author_email"),
        "authored_date": detail.get("authored_date"),
        "committer_name": detail.get("committer_name"),
        "committer_email": detail.get("committer_email"),
        "committed_date": detail.get("committed_date"),
        "web_url": detail.get("web_url"),
        "stats": detail.get("stats") or {},
        "files": normalize_diffs(diffs, diff_limit),
        "pushes": [],
    }


def fetch_event_commit_shas(
    client: GitLabClient,
    event: dict[str, Any],
    warnings: list[str],
) -> list[str]:
    project_id = int(event["project_id"])
    push_data = event.get("push_data") or {}
    commit_from = push_data.get("commit_from")
    commit_to = push_data.get("commit_to")
    if is_zero_sha(commit_to):
        warnings.append(f"事件 {event.get('id')} 没有有效的目标提交，已跳过")
        return []
    if is_zero_sha(commit_from):
        warnings.append(
            f"事件 {event.get('id')} 为新分支或缺少起始 SHA，仅采集目标提交 {commit_to[:8]}"
        )
        return [commit_to]
    compare, _ = client.get(
        f"/projects/{project_id}/repository/compare",
        {"from": commit_from, "to": commit_to, "straight": "true"},
    )
    commits = compare.get("commits") or []
    return [item["id"] for item in commits if item.get("id")]


def collect_period_commits(
    client: GitLabClient,
    start_date: date,
    end_date: date,
    diff_limit: int,
) -> dict[str, Any]:
    user, _ = client.get("/user")
    api_before = end_date + timedelta(days=1)
    events = client.get_all(
        f"/users/{user['id']}/events",
        {
            "action": "pushed",
            "after": start_date.isoformat(),
            "before": api_before.isoformat(),
        },
    )
    events = [
        event
        for event in events
        if event.get("created_at")
        and start_date <= parse_event_date(event["created_at"]) <= end_date
    ]
    events.sort(key=lambda item: item.get("created_at") or "")

    warnings: list[str] = []
    project_cache: dict[int, dict[str, Any]] = {}
    project_records: dict[int, dict[str, Any]] = {}
    commit_cache: dict[tuple[int, str], dict[str, Any]] = {}

    for event in events:
        project_id = int(event["project_id"])
        if project_id not in project_cache:
            project, _ = client.get(f"/projects/{project_id}")
            project_cache[project_id] = project
            project_records[project_id] = {
                "id": project_id,
                "name": project.get("name"),
                "path_with_namespace": project.get("path_with_namespace"),
                "description": project.get("description"),
                "web_url": project.get("web_url"),
                "commits": [],
            }

        commit_shas = fetch_event_commit_shas(client, event, warnings)
        push_data = event.get("push_data") or {}
        push_record = {
            "event_id": event.get("id"),
            "pushed_at": event.get("created_at"),
            "ref": push_data.get("ref"),
            "event_commit_count": push_data.get("commit_count"),
            "event_commit_title": push_data.get("commit_title"),
        }
        for commit_sha in commit_shas:
            key = (project_id, commit_sha)
            if key not in commit_cache:
                commit = fetch_commit(client, project_id, commit_sha, diff_limit)
                commit_cache[key] = commit
                project_records[project_id]["commits"].append(commit)
            commit_cache[key]["pushes"].append(push_record)

    projects = list(project_records.values())
    for project in projects:
        project["commits"].sort(
            key=lambda item: (item.get("pushes") or [{}])[0].get("pushed_at") or ""
        )

    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "scope": "authenticated_user_push_events",
        "user": {
            "id": user.get("id"),
            "username": user.get("username"),
            "name": user.get("name"),
        },
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "counts": {
            "events": len(events),
            "projects": len(projects),
            "commits": len(commit_cache),
        },
        "warnings": warnings,
        "projects": projects,
    }


def inspect_commit(
    client: GitLabClient,
    project_id: int,
    commit_sha: str,
    diff_limit: int,
) -> dict[str, Any]:
    project, _ = client.get(f"/projects/{project_id}")
    return {
        "project": {
            "id": project.get("id"),
            "name": project.get("name"),
            "path_with_namespace": project.get("path_with_namespace"),
            "description": project.get("description"),
        },
        "commit": fetch_commit(client, project_id, commit_sha, diff_limit),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="采集 GitLab 用户在指定周期内推送的提交及代码变更证据。"
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("GITLAB_BASE_URL"),
        help="GitLab 地址，也可通过 GITLAB_BASE_URL 设置。",
    )
    parser.add_argument(
        "--token-env",
        default="GITLAB_TOKEN",
        help="保存访问令牌的环境变量名，默认 GITLAB_TOKEN。",
    )
    parser.add_argument("--start-date", type=parse_date, help="开始日期，格式 YYYY-MM-DD。")
    parser.add_argument("--end-date", type=parse_date, help="结束日期，格式 YYYY-MM-DD。")
    parser.add_argument("--insecure", action="store_true", help="允许访问使用自签名证书的 GitLab。")
    parser.add_argument(
        "--diff-limit",
        type=int,
        default=12000,
        help="每个提交保留的 diff 摘要字符预算，默认 12000。",
    )
    parser.add_argument("--project-id", type=int, help="深入检查单个提交时指定项目 ID。")
    parser.add_argument("--commit-sha", help="深入检查单个提交时指定提交 SHA。")
    return parser


def main() -> int:
    configure_utf8_output()
    parser = build_parser()
    args = parser.parse_args()
    if not args.base_url:
        parser.error("请通过 --base-url 或 GITLAB_BASE_URL 提供 GitLab 地址")
    token = os.environ.get(args.token_env)
    if not token:
        parser.error(f"环境变量 {args.token_env} 中未找到 GitLab 访问令牌")
    if args.diff_limit <= 0:
        parser.error("--diff-limit 必须大于 0")
    if bool(args.project_id) != bool(args.commit_sha):
        parser.error("--project-id 与 --commit-sha 必须同时提供")

    try:
        client = GitLabClient(args.base_url, token, insecure=args.insecure)
        if args.project_id and args.commit_sha:
            result = inspect_commit(client, args.project_id, args.commit_sha, args.diff_limit)
        else:
            start_date, end_date = resolve_date_range(args.start_date, args.end_date)
            result = collect_period_commits(client, start_date, end_date, args.diff_limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (GitLabApiError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
