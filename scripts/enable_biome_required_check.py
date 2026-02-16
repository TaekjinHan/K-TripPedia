#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from urllib import error, request


def api_call(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "ktrippedia-branch-protection-script")
    if body is not None:
        req.add_header("Content-Type", "application/json")

    try:
        with request.urlopen(req, timeout=20) as resp:
            text = resp.read().decode("utf-8").strip()
            return json.loads(text) if text else {}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {exc.code} for {method} {url}: {detail}") from exc


def get_token() -> str:
    load_token_from_dotenv()
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("Set GH_TOKEN or GITHUB_TOKEN with repo admin permission")
    return token


def dotenv_candidate_paths() -> list[str]:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(repo_root, ".env"),
    ]
    unique_paths: list[str] = []
    for path in candidates:
        if path not in unique_paths:
            unique_paths.append(path)
    return unique_paths


def parse_env_assignment(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith("export "):
        stripped = stripped[len("export ") :].strip()
    if "=" not in stripped:
        return None
    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        return None
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return key, value


def load_token_from_dotenv() -> None:
    if os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN"):
        return

    for path in dotenv_candidate_paths():
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as handle:
                for raw_line in handle:
                    parsed = parse_env_assignment(raw_line)
                    if not parsed:
                        continue
                    key, value = parsed
                    if key not in {"GH_TOKEN", "GITHUB_TOKEN"}:
                        continue
                    if value and not os.getenv(key):
                        os.environ[key] = value
        except OSError as exc:
            raise RuntimeError(f"Failed to read dotenv file at {path}: {exc}") from exc

        if os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN"):
            return


def parse_owner_repo_from_remote(url: str) -> tuple[str, str] | None:
    text = url.strip()
    patterns = [
        r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$",
        r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.match(pattern, text)
        if match:
            return match.group("owner"), match.group("repo")
    return None


def resolve_owner_repo(owner: str | None, repo: str | None) -> tuple[str, str]:
    if owner and repo:
        return owner, repo

    try:
        raw = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        raw = ""

    parsed = parse_owner_repo_from_remote(raw)
    if parsed:
        return parsed

    raise ValueError("Provide --owner and --repo or configure origin remote to GitHub")


def normalize_contexts(existing: list[str], target: str) -> list[str]:
    merged = list(existing)
    if target not in merged:
        merged.append(target)
    return merged


def patch_required_status_checks(owner: str, repo: str, branch: str, context: str, token: str) -> None:
    base = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}/protection/required_status_checks"
    current = api_call("GET", base, token)
    strict = bool(current.get("strict", True))
    existing = [c for c in current.get("contexts", []) if isinstance(c, str)]
    payload = {
        "strict": strict,
        "contexts": normalize_contexts(existing, context),
    }
    api_call("PATCH", base, token, payload)


def bootstrap_branch_protection(owner: str, repo: str, branch: str, context: str, token: str) -> None:
    url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}/protection"
    payload = {
        "required_status_checks": {
            "strict": True,
            "contexts": [context],
        },
        "enforce_admins": False,
        "required_pull_request_reviews": None,
        "restrictions": None,
    }
    api_call("PUT", url, token, payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Enable Biome required status check on a protected branch")
    parser.add_argument("--owner", help="GitHub owner/org")
    parser.add_argument("--repo", help="GitHub repository name")
    parser.add_argument("--branch", default="main", help="Protected branch name")
    parser.add_argument("--context", default="Biome / biome", help="Required status check context")
    parser.add_argument(
        "--bootstrap-protection",
        action="store_true",
        help="Initialize minimal branch protection if required status checks are not enabled yet",
    )
    args = parser.parse_args()

    owner, repo = resolve_owner_repo(args.owner, args.repo)
    token = get_token()

    try:
        patch_required_status_checks(owner, repo, args.branch, args.context, token)
        print(f"Updated required status checks on {owner}/{repo}:{args.branch}")
        print(f"Required check ensured: {args.context}")
        return
    except RuntimeError as exc:
        message = str(exc)
        if "404" not in message or not args.bootstrap_protection:
            raise

    bootstrap_branch_protection(owner, repo, args.branch, args.context, token)
    print(f"Bootstrapped branch protection on {owner}/{repo}:{args.branch}")
    print(f"Required check set: {args.context}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
