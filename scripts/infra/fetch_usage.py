#!/usr/bin/env python3
"""Fetch live usage data for all accounts via Anthropic API response headers.

Makes a minimal API call per account and reads rate-limit headers to get
5-hour and 7-day utilization. Writes results to ~/.claude-usage/usage_cache.json
in the same format as the Mac push agent, so capacity.py and account_status.py
can read it transparently.

Usage:
    python3 fetch_usage.py              # fetch and update cache
    python3 fetch_usage.py --json       # print JSON to stdout only
    python3 fetch_usage.py --dry-run    # show what would be fetched
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOMES = Path.home() / ".claude-homes"
USAGE_CACHE = Path.home() / ".claude-usage" / "usage_cache.json"

# Map account dirs to profile names (must match Mac push agent format)
ACCOUNT_PROFILES = {
    "account1": {"name": "steph-gmail", "email": "steph.jarmak@gmail.com"},
    "account2": {"name": "harvard", "email": "stephanie.jarmak@cfa.harvard.edu"},
    "account3": {"name": "gmail-2", "email": "stephanie.jarmak@gmail.com"},
    "account4": {"name": "gmail-3", "email": "stephanie.jarmak1@gmail.com"},
    "account5": {"name": "gmail-4", "email": "gibsonsteph42@gmail.com"},
}

API_URL = "https://api.anthropic.com/v1/messages"
PROBE_MODEL = "claude-haiku-4-5-20251001"


def load_token(account_dir: Path) -> str | None:
    creds_file = account_dir / ".claude" / ".credentials.json"
    if not creds_file.exists():
        return None
    try:
        creds = json.loads(creds_file.read_text())
        oauth = creds.get("claudeAiOauth", {})
        expires_at = oauth.get("expiresAt", 0) / 1000
        if expires_at < time.time():
            return None  # expired
        return oauth.get("accessToken")
    except Exception:
        return None


def fetch_usage_for_token(token: str) -> dict | None:
    """Make a minimal API call and extract usage from response headers."""
    try:
        from curl_cffi import requests as cffi_requests
        session = cffi_requests.Session(impersonate="chrome131")
    except ImportError:
        # Fall back to urllib
        import urllib.request
        req = urllib.request.Request(
            API_URL,
            data=json.dumps({
                "model": PROBE_MODEL,
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "x"}],
            }).encode(),
            headers={
                "x-api-key": token,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                headers = {k.lower(): v for k, v in resp.getheaders()}
        except Exception as e:
            # Even 429 has the headers we need
            if hasattr(e, "headers"):
                headers = {k.lower(): v for k, v in e.headers.items()}
            else:
                return None
        return _parse_headers(headers)

    resp = session.post(
        API_URL,
        headers={
            "x-api-key": token,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": PROBE_MODEL,
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "x"}],
        },
        timeout=15,
    )
    headers = {k.lower(): v for k, v in resp.headers.items()}
    return _parse_headers(headers)


def _parse_headers(headers: dict) -> dict:
    """Extract usage data from Anthropic rate-limit response headers."""
    def _get_float(key: str) -> float | None:
        val = headers.get(key)
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def _get_int(key: str) -> int | None:
        val = headers.get(key)
        if val is None:
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    five_h_util = _get_float("anthropic-ratelimit-unified-5h-utilization")
    five_h_reset = _get_int("anthropic-ratelimit-unified-5h-reset")
    seven_d_util = _get_float("anthropic-ratelimit-unified-7d-utilization")
    seven_d_reset = _get_int("anthropic-ratelimit-unified-7d-reset")

    result = {}
    if five_h_util is not None:
        result["five_hour"] = {
            "utilization": round(five_h_util * 100, 1),
            "resets_at": (
                datetime.fromtimestamp(five_h_reset, tz=timezone.utc).isoformat()
                if five_h_reset else None
            ),
        }
    if seven_d_util is not None:
        result["seven_day"] = {
            "utilization": round(seven_d_util * 100, 1),
            "resets_at": (
                datetime.fromtimestamp(seven_d_reset, tz=timezone.utc).isoformat()
                if seven_d_reset else None
            ),
        }

    # Also grab sonnet-specific if available
    sonnet_util = _get_float("anthropic-ratelimit-unified-7d-sonnet-utilization")
    sonnet_reset = _get_int("anthropic-ratelimit-unified-7d-sonnet-reset")
    if sonnet_util is not None:
        result["seven_day_sonnet"] = {
            "utilization": round(sonnet_util * 100, 1),
            "resets_at": (
                datetime.fromtimestamp(sonnet_reset, tz=timezone.utc).isoformat()
                if sonnet_reset else None
            ),
        }

    return result if result else None


def update_cache(accounts: list[dict]) -> None:
    """Write or merge results into the usage cache."""
    USAGE_CACHE.parent.mkdir(parents=True, exist_ok=True)

    # Load existing cache to preserve entries we didn't fetch
    existing = {}
    if USAGE_CACHE.exists():
        try:
            data = json.loads(USAGE_CACHE.read_text())
            for a in data.get("accounts", []):
                key = a.get("name") or a.get("email", "")
                if key:
                    existing[key] = a
        except Exception:
            pass

    # Merge our fetched data
    for acct in accounts:
        existing[acct["name"]] = acct

    output = {
        "accounts": list(existing.values()),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    USAGE_CACHE.write_text(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="Print JSON to stdout only, don't update cache")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show accounts without fetching")
    parser.add_argument("--account", type=int, default=None,
                        help="Fetch only accountN")
    parser.add_argument("--stagger", type=float, default=2.0,
                        help="Seconds between API calls (default: 2)")
    args = parser.parse_args()

    account_dirs = sorted(HOMES.glob("account*"))
    if args.account is not None:
        account_dirs = [d for d in account_dirs if d.name == f"account{args.account}"]

    if not account_dirs:
        print("No account homes found.")
        sys.exit(1)

    if args.dry_run:
        for d in account_dirs:
            profile = ACCOUNT_PROFILES.get(d.name, {})
            token = load_token(d)
            print(f"{d.name} ({profile.get('email', '?')}): token={'valid' if token else 'EXPIRED'}")
        return

    results = []
    for i, d in enumerate(account_dirs):
        profile = ACCOUNT_PROFILES.get(d.name, {})
        acct_name = profile.get("name", d.name)
        email = profile.get("email", "")

        token = load_token(d)
        if not token:
            print(f"{d.name}: token expired, skipping")
            results.append({
                "name": acct_name,
                "email": email,
                "profile": f"Profile {i}",
                "rate_limit_tier": "unknown",
                "five_hour": None,
                "seven_day": None,
                "seven_day_sonnet": None,
                "seven_day_opus": None,
                "extra_usage_enabled": False,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "error": "token expired",
            })
            continue

        if i > 0:
            time.sleep(args.stagger)

        print(f"{d.name}: fetching...", end=" ", flush=True)
        try:
            usage = fetch_usage_for_token(token)
            if usage:
                entry = {
                    "name": acct_name,
                    "email": email,
                    "profile": f"Profile {i}",
                    "rate_limit_tier": "default_claude_max_20x",
                    "five_hour": usage.get("five_hour"),
                    "seven_day": usage.get("seven_day"),
                    "seven_day_sonnet": usage.get("seven_day_sonnet"),
                    "seven_day_opus": None,
                    "extra_usage_enabled": False,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "error": None,
                }
                five = (usage.get("five_hour") or {}).get("utilization", "?")
                seven = (usage.get("seven_day") or {}).get("utilization", "?")
                print(f"5h={five}% 7d={seven}%")
                results.append(entry)
            else:
                print("no usage headers in response")
                results.append({
                    "name": acct_name,
                    "email": email,
                    "profile": f"Profile {i}",
                    "rate_limit_tier": "unknown",
                    "five_hour": None,
                    "seven_day": None,
                    "seven_day_sonnet": None,
                    "seven_day_opus": None,
                    "extra_usage_enabled": False,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "error": "no usage headers",
                })
        except Exception as exc:
            print(f"FAILED ({exc})")
            results.append({
                "name": acct_name,
                "email": email,
                "profile": f"Profile {i}",
                "rate_limit_tier": "unknown",
                "five_hour": None,
                "seven_day": None,
                "seven_day_sonnet": None,
                "seven_day_opus": None,
                "extra_usage_enabled": False,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc)[:200],
            })

    if args.as_json:
        print(json.dumps(results, indent=2))
    else:
        update_cache(results)
        print(f"\nUpdated {USAGE_CACHE}")


if __name__ == "__main__":
    main()
