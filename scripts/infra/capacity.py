#!/usr/bin/env python3
"""
Account capacity planner for benchmark parallelization.

Shows how many parallel containers each account can support based on
remaining usage windows and token validity.

Usage:
    python3 capacity.py                    # table view
    python3 capacity.py --json             # machine-readable
    python3 capacity.py --slots 20         # distribute N slots across accounts
    python3 capacity.py --max-per-account 4  # cap containers per account
"""
import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOMES = Path.home() / ".claude-homes"
USAGE_CACHE = Path.home() / ".claude-usage" / "usage_cache.json"
DEFAULT_MAX_PER_ACCOUNT = 6
SKIP_THRESHOLD = 5  # % remaining below which account is considered exhausted


def load_tokens() -> dict:
    accounts = {}
    for acct_dir in sorted(HOMES.glob("account*")):
        acct = acct_dir.name
        creds_file = acct_dir / ".claude" / ".credentials.json"
        try:
            creds = json.loads(creds_file.read_text())
            oauth = creds.get("claudeAiOauth", {})
            expires_at = oauth.get("expiresAt", 0) / 1000
            token_hours = (expires_at - time.time()) / 3600
            accounts[acct] = {
                "token_hours": token_hours,
                "token_ok": token_hours > 0.25,
                "tier": oauth.get("rateLimitTier", "unknown"),
            }
        except Exception:
            accounts[acct] = {"token_hours": 0, "token_ok": False, "tier": "unknown"}
    return accounts


def load_usage() -> tuple[dict, float]:
    if not USAGE_CACHE.exists():
        return {}, 0

    data = json.loads(USAGE_CACHE.read_text())
    fetched_at = data.get("fetched_at", "")
    try:
        age_min = (time.time() - datetime.fromisoformat(
            fetched_at.replace("Z", "+00:00")).timestamp()) / 60
    except Exception:
        age_min = 999

    usage = {}
    email_to_acct = {
        "steph.jarmak@gmail.com": "account1",
        "stephanie.jarmak@cfa.harvard.edu": "account2",
        "stephanie.jarmak@gmail.com": "account3",
        "stephanie.jarmak1@gmail.com": "account4",
        "gibsonsteph42@gmail.com": "account5",
    }
    # Fallback: map profile names to accounts for cache entries missing email
    name_to_acct = {
        "steph-gmail": "account1",
        "sourcegraph": "account1",
        "harvard": "account2",
        "gmail-2": "account3",
        "gmail-3": "account4",
        "gmail-4": "account5",
    }

    for acct_data in data.get("accounts", []):
        email = acct_data.get("email", "")
        acct = email_to_acct.get(email)
        if not acct:
            # Fallback to profile name when email is missing from cache
            profile_name = acct_data.get("name", "")
            acct = name_to_acct.get(profile_name)
        if not acct:
            continue
        # Skip entries with fetch errors — data is unreliable
        if acct_data.get("error"):
            usage.setdefault(acct, {
                "five_h_pct": 0, "seven_d_pct": 0,
                "five_h_remaining": 100, "seven_d_remaining": 100,
                "five_h_resets_at": None, "seven_d_resets_at": None,
                "seven_d_resets_in_h": None,
                "email": email or acct_data.get("name", "?"),
                "fetch_error": acct_data["error"],
            })
            continue
        five_h = (acct_data.get("five_hour") or {}).get("utilization", 0)
        seven_d = (acct_data.get("seven_day") or {}).get("utilization", 0)
        five_h_reset = (acct_data.get("five_hour") or {}).get("resets_at")
        seven_d_reset = (acct_data.get("seven_day") or {}).get("resets_at")

        # Parse reset times into hours from now
        seven_d_resets_in_h = _hours_until(seven_d_reset)

        # Multiple profiles may map to the same account (e.g. account1 has
        # steph-gmail + sourcegraph). Take the worst-case (highest usage).
        if acct in usage:
            five_h = max(five_h, usage[acct]["five_h_pct"])
            seven_d = max(seven_d, usage[acct]["seven_d_pct"])

        usage[acct] = {
            "five_h_pct": five_h,
            "seven_d_pct": seven_d,
            "five_h_remaining": max(0, 100 - five_h),
            "seven_d_remaining": max(0, 100 - seven_d),
            "five_h_resets_at": five_h_reset,
            "seven_d_resets_at": seven_d_reset,
            "seven_d_resets_in_h": seven_d_resets_in_h,
            "email": email or usage.get(acct, {}).get("email", ""),
        }

    return usage, age_min


def _hours_until(iso_str: str | None) -> float | None:
    """Hours from now until an ISO timestamp. Returns None if unparseable."""
    if not iso_str:
        return None
    try:
        reset_ts = datetime.fromisoformat(iso_str.replace("Z", "+00:00")).timestamp()
        return (reset_ts - time.time()) / 3600
    except Exception:
        return None


def capacity_score(token_ok: bool, five_h_remaining: float,
                    seven_d_remaining: float, seven_d_resets_in_h: float | None) -> float:
    """0-100 capacity score based on rate-limit risk.

    The 5-hour session window is what actually causes rate limiting during a
    run.  The 7-day window only constrains capacity when it is nearly
    exhausted AND won't reset soon (within 48h).  If the 7-day window resets
    soon, the account is safe to use at full session capacity.
    """
    if not token_ok:
        return 0

    # 7-day remaining only matters if it won't reset soon
    effective_7d = seven_d_remaining
    if seven_d_resets_in_h is not None and seven_d_resets_in_h <= 48:
        # Resets within 48h — safe to use remaining budget aggressively.
        # Only gate on 7d if truly exhausted (< 5% left).
        if seven_d_remaining >= SKIP_THRESHOLD:
            effective_7d = 100  # treat as unconstrained

    return min(five_h_remaining, effective_7d)


def recommended_slots(score: float, max_per_account: int) -> int:
    if score < SKIP_THRESHOLD:
        return 0
    # Linear scale from 1 slot at threshold to max at 100%
    frac = (score - SKIP_THRESHOLD) / (100 - SKIP_THRESHOLD)
    return max(1, round(frac * max_per_account))


def distribute_slots(accounts_info: list, total: int, max_per: int) -> dict:
    """Distribute total slots proportionally by capacity score."""
    eligible = [(a, i) for a, i in accounts_info if i["capacity_score"] >= SKIP_THRESHOLD]
    if not eligible:
        return {a: 0 for a, _ in accounts_info}

    total_score = sum(i["capacity_score"] for _, i in eligible)
    alloc = {}
    remaining = total

    # Proportional allocation, capped at max_per
    for acct, info in eligible:
        share = (info["capacity_score"] / total_score) * total
        alloc[acct] = min(max_per, max(1, round(share)))

    # Fill skipped accounts with 0
    for acct, _ in accounts_info:
        if acct not in alloc:
            alloc[acct] = 0

    return alloc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", dest="as_json", action="store_true")
    parser.add_argument("--slots", type=int, default=None,
                        help="Total parallel slots to distribute across accounts")
    parser.add_argument("--max-per-account", type=int, default=DEFAULT_MAX_PER_ACCOUNT)
    args = parser.parse_args()

    tokens = load_tokens()
    usage, age_min = load_usage()

    accounts_info = []
    for acct in sorted(tokens):
        tok = tokens[acct]
        _no_data = acct not in usage
        _fetch_error = bool(usage.get(acct, {}).get("fetch_error"))
        u = usage.get(acct, {"five_h_pct": 0, "seven_d_pct": 0,
                              "five_h_remaining": 100, "seven_d_remaining": 100,
                              "five_h_resets_at": None, "seven_d_resets_at": None,
                              "seven_d_resets_in_h": None, "email": "?"})
        u["no_usage_data"] = _no_data
        u["fetch_error"] = u.get("fetch_error")

        # Stale/errored accounts: assume 50% used to avoid over-allocation.
        # Better to under-assign than to rate-limit an account we can't measure.
        if _no_data or _fetch_error:
            u["five_h_remaining"] = 50
            u["seven_d_remaining"] = 50

        score = capacity_score(tok["token_ok"], u["five_h_remaining"],
                               u["seven_d_remaining"], u.get("seven_d_resets_in_h"))
        slots = recommended_slots(score, args.max_per_account)
        accounts_info.append((acct, {
            **tok, **u,
            "capacity_score": score,
            "recommended_slots": slots,
        }))

    if args.slots is not None:
        distribution = distribute_slots(accounts_info, args.slots, args.max_per_account)
    else:
        distribution = None

    if args.as_json:
        out = []
        for acct, info in accounts_info:
            out.append({
                "account": acct,
                "email": info.get("email"),
                "token_hours": round(info["token_hours"], 1),
                "token_ok": info["token_ok"],
                "five_h_used_pct": round(info["five_h_pct"], 1),
                "seven_d_used_pct": round(info["seven_d_pct"], 1),
                "capacity_score": round(info["capacity_score"], 1),
                "recommended_slots": info["recommended_slots"] if distribution is None
                                     else distribution.get(acct, 0),
                "available": info["capacity_score"] >= SKIP_THRESHOLD,
            })
        result = {"usage_age_min": round(age_min, 1), "accounts": out}
        if distribution is not None:
            result["slot_distribution"] = distribution
            result["total_slots"] = sum(distribution.values())
        print(json.dumps(result, indent=2))
        return

    # Table view
    print(f"\nUsage data age: {age_min:.0f} min\n")
    header = (f"{'Account':<10} {'Token':>6}  {'5h sess':>8}  {'7d used':>8}  "
              f"{'7d resets':>10}  {'Capacity':>9}  {'Slots':>5}")
    print(header)
    print("-" * len(header))
    for acct, info in accounts_info:
        slots = info["recommended_slots"] if distribution is None else distribution.get(acct, 0)
        status = "SKIP" if info["capacity_score"] < SKIP_THRESHOLD else f"{slots} slots"
        if not info["token_ok"]:
            status = "NO TOKEN"
        elif info.get("no_usage_data"):
            status += " (no data!)"
        elif info.get("fetch_error"):
            status += " (STALE!)"

        # Format 7d reset time
        resets_h = info.get("seven_d_resets_in_h")
        if resets_h is not None:
            if resets_h < 1:
                reset_str = f"{resets_h * 60:.0f}m"
            elif resets_h < 48:
                reset_str = f"{resets_h:.0f}h"
            else:
                reset_str = f"{resets_h / 24:.1f}d"
        else:
            reset_str = "?"

        print(
            f"{acct:<10} "
            f"{info['token_hours']:>5.1f}h  "
            f"{info['five_h_pct']:>7.0f}%  "
            f"{info['seven_d_pct']:>7.0f}%  "
            f"{reset_str:>10}  "
            f"{info['capacity_score']:>8.0f}%  "
            f"  {status}"
        )

    total_slots = sum(
        (distribution.get(a, 0) if distribution else info["recommended_slots"])
        for a, info in accounts_info
    )
    print(f"\nTotal available slots: {total_slots} (max {args.max_per_account}/account)")
    if distribution:
        print(f"Distributing {args.slots} requested slots:")
        for acct, n in distribution.items():
            if n > 0:
                print(f"  {acct}: {n}")


if __name__ == "__main__":
    main()
