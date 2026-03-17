#!/usr/bin/env python3
"""Render conversation-derived blog figures as Sourcegraph-style SVGs.

Reads CSV datasets from docs/assets/blog/medium/csv (or custom path) and writes
styled SVG charts to docs/assets/blog/medium/figures.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np


PALETTE = {
    "bg": "#020202",
    "text": "#ededed",
    "text_secondary": "#a9a9a9",
    "grid": "#343434",
    "pos": "#8552f2",
    "neg": "#ff7867",
    "base": "#6b7280",
    "accent": "#914bdc",
    "muted": "#4b5563",
}


def setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": PALETTE["bg"],
            "axes.facecolor": PALETTE["bg"],
            "axes.edgecolor": PALETTE["grid"],
            "axes.labelcolor": PALETTE["text"],
            "xtick.color": PALETTE["text"],
            "ytick.color": PALETTE["text"],
            "text.color": PALETTE["text"],
            "grid.color": PALETTE["grid"],
            "font.family": "sans-serif",
            "font.sans-serif": ["Poly Sans", "Arial", "DejaVu Sans", "sans-serif"],
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
        }
    )


def save_svg(fig: plt.Figure, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, format="svg", bbox_inches="tight")
    plt.close(fig)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    arr = np.array(sorted(values), dtype=float)
    return float(np.percentile(arr, q))


def plot_fig01(csv_dir: Path, out_dir: Path) -> None:
    rows = read_csv(csv_dir / "fig01_activity_timeline.csv")
    by_day = defaultdict(lambda: {"messages": 0, "sessions": 0})
    for r in rows:
        day = r["day"]
        by_day[day]["messages"] += int(r["messages"])
        by_day[day]["sessions"] += int(r["sessions"])

    days = sorted(by_day)
    x = [datetime.strptime(d, "%Y-%m-%d") for d in days]
    msgs = [by_day[d]["messages"] for d in days]
    sess = [by_day[d]["sessions"] for d in days]

    fig, ax = plt.subplots(figsize=(10.8, 4.6))
    ax.bar(x, msgs, width=0.85, color=PALETTE["pos"], alpha=0.25, label="Messages/day")
    ax.plot(x, msgs, color=PALETTE["pos"], linewidth=2.0, alpha=0.95)
    ax.set_ylabel("Messages/day", color=PALETTE["text_secondary"])
    ax.grid(axis="y", alpha=0.35)

    ax2 = ax.twinx()
    ax2.plot(x, sess, color=PALETTE["text_secondary"], linewidth=1.6, label="Sessions/day")
    ax2.set_ylabel("Sessions/day", color=PALETTE["text_secondary"])
    ax2.tick_params(axis="y", colors=PALETTE["text_secondary"])

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(x) // 10)))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    top_ix = sorted(range(len(msgs)), key=lambda i: msgs[i], reverse=True)[:3]
    for i in top_ix:
        ax.text(
            x[i],
            msgs[i] + max(msgs) * 0.02,
            f"{msgs[i]:,}",
            ha="center",
            va="bottom",
            fontsize=8,
            color=PALETTE["text"],
        )

    ax.set_title("Conversation Throughput Over Time")
    save_svg(fig, out_dir / "fig01_activity_timeline.svg")


def plot_fig02(csv_dir: Path, out_dir: Path) -> None:
    rows = read_csv(csv_dir / "fig02_agent_mix.csv")
    months = sorted({r["ym"] for r in rows})
    total_by_agent = Counter()
    for r in rows:
        total_by_agent[r["agent"]] += int(r["messages"])

    top_agents = [a for a, _ in total_by_agent.most_common(6)]
    series = {a: [0] * len(months) for a in top_agents + ["other"]}
    month_ix = {m: i for i, m in enumerate(months)}
    for r in rows:
        a = r["agent"]
        a_key = a if a in top_agents else "other"
        series[a_key][month_ix[r["ym"]]] += int(r["messages"])

    colors = [
        PALETTE["pos"],
        PALETTE["accent"],
        "#7c7f86",
        "#9ca3af",
        "#cbd5e1",
        "#a78bfa",
        PALETTE["neg"],
    ]

    fig, ax = plt.subplots(figsize=(10.2, 4.8))
    bottom = np.zeros(len(months))
    for i, agent in enumerate(top_agents + ["other"]):
        vals = np.array(series[agent], dtype=float)
        ax.bar(months, vals, bottom=bottom, color=colors[i], label=agent, width=0.7)
        bottom += vals

    ax.set_title("Agent Mix by Month (Conversation Messages)")
    ax.set_ylabel("Messages", color=PALETTE["text_secondary"])
    ax.grid(axis="y", alpha=0.35)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper left")
    save_svg(fig, out_dir / "fig02_agent_mix.svg")


def plot_fig03(csv_dir: Path, out_dir: Path) -> None:
    rows = read_csv(csv_dir / "fig03_tool_intensity.csv")
    by_agent: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        try:
            v = float(r["tools_per_msg"] or "0")
            if math.isfinite(v):
                by_agent[r["agent"]].append(v)
        except ValueError:
            continue

    agents = sorted(by_agent, key=lambda a: len(by_agent[a]), reverse=True)[:8]
    trimmed = []
    for a in agents:
        arr = by_agent[a]
        cap = percentile(arr, 99)
        trimmed.append([min(v, cap) for v in arr])

    fig, ax = plt.subplots(figsize=(10.6, 4.8))
    bp = ax.boxplot(trimmed, patch_artist=True, labels=agents, showfliers=False)
    for b in bp["boxes"]:
        b.set(facecolor=PALETTE["pos"], alpha=0.35, edgecolor=PALETTE["pos"], linewidth=1.1)
    for m in bp["medians"]:
        m.set(color=PALETTE["text"], linewidth=1.4)
    for w in bp["whiskers"]:
        w.set(color=PALETTE["text_secondary"], linewidth=1.0)
    for c in bp["caps"]:
        c.set(color=PALETTE["text_secondary"], linewidth=1.0)

    ax.set_title("Tool Intensity Distribution by Agent")
    ax.set_ylabel("Tools per message", color=PALETTE["text_secondary"])
    ax.grid(axis="y", alpha=0.35)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    save_svg(fig, out_dir / "fig03_tool_intensity_violin.svg")


def plot_fig04(csv_dir: Path, out_dir: Path) -> None:
    rows = read_csv(csv_dir / "fig04_error_retry_pressure.csv")
    x = [int(r["error_count"]) for r in rows]
    y = [int(r["retry_mentions"]) for r in rows]

    x_cap = percentile([float(v) for v in x], 99)
    y_cap = percentile([float(v) for v in y], 99)
    xf = [min(v, x_cap) for v in x]
    yf = [min(v, y_cap) for v in y]

    fig, ax = plt.subplots(figsize=(10.2, 4.6))
    hb = ax.hexbin(xf, yf, gridsize=40, cmap="magma", mincnt=1)
    cb = fig.colorbar(hb, ax=ax, pad=0.02)
    cb.ax.tick_params(colors=PALETTE["text"], labelsize=8)
    cb.outline.set_edgecolor(PALETTE["grid"])
    cb.set_label("Session density", color=PALETTE["text_secondary"])

    ax.set_title("Error vs Retry Pressure (Session Level)")
    ax.set_xlabel("error_count", color=PALETTE["text_secondary"])
    ax.set_ylabel("retry_mentions", color=PALETTE["text_secondary"])
    ax.grid(alpha=0.25)
    save_svg(fig, out_dir / "fig04_error_retry_pressure.svg")


def plot_fig05(csv_dir: Path, out_dir: Path) -> None:
    rows = read_csv(csv_dir / "fig05_incident_heatmap.csv")
    days = sorted({r["day"] for r in rows})
    themes = ["infra", "benchmark_ops", "agent_design"]
    day_ix = {d: i for i, d in enumerate(days)}
    matrix = np.zeros((len(themes), len(days)), dtype=float)
    theme_ix = {t: i for i, t in enumerate(themes)}

    for r in rows:
        if r["theme"] in theme_ix:
            matrix[theme_ix[r["theme"]], day_ix[r["day"]]] += int(r["hits"])

    fig, ax = plt.subplots(figsize=(11.5, 4.2))
    im = ax.imshow(matrix, aspect="auto", cmap="magma", interpolation="nearest")
    ax.set_yticks(range(len(themes)))
    ax.set_yticklabels(themes)
    step = max(1, len(days) // 12)
    xt = list(range(0, len(days), step))
    ax.set_xticks(xt)
    ax.set_xticklabels([days[i] for i in xt], rotation=30, ha="right")
    ax.set_title("Incident Theme Heatmap (Conversation Mentions)")
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.ax.tick_params(colors=PALETTE["text"], labelsize=8)
    cb.outline.set_edgecolor(PALETTE["grid"])
    cb.set_label("Hits", color=PALETTE["text_secondary"])
    save_svg(fig, out_dir / "fig05_incident_heatmap.svg")


def plot_fig06(csv_dir: Path, out_dir: Path) -> None:
    rows = read_csv(csv_dir / "fig06_dedupe_impact.csv")
    run_ids = [str(r["id"]) for r in rows]
    kept = []
    dropped = []
    inputs = []
    for r in rows:
        keep = int(float(r["dedupe_kept_rows"] or r["session_count"] or 0))
        drop = int(float(r["dedupe_dropped_rows"] or 0))
        inp = int(float(r["dedupe_input_rows"] or (keep + drop)))
        kept.append(keep)
        dropped.append(drop)
        inputs.append(inp)

    x = np.arange(len(run_ids))
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ax.bar(x, kept, color=PALETTE["pos"], alpha=0.85, label="kept")
    ax.bar(x, dropped, bottom=kept, color=PALETTE["neg"], alpha=0.85, label="dropped")
    ax.plot(x, inputs, color=PALETTE["text_secondary"], marker="o", linewidth=1.2, label="input")
    ax.set_xticks(x)
    ax.set_xticklabels([f"run {r}" for r in run_ids])
    ax.set_ylabel("Sessions", color=PALETTE["text_secondary"])
    ax.set_title("Dedupe Impact by Ingest Run")
    ax.grid(axis="y", alpha=0.35)
    ax.legend(frameon=False, ncol=3, loc="upper left", fontsize=8)

    for i, (k, d) in enumerate(zip(kept, dropped)):
        ax.text(i, k + d + max(inputs) * 0.02, f"{d} dropped", ha="center", va="bottom", fontsize=8)

    save_svg(fig, out_dir / "fig06_dedupe_impact.svg")


def plot_fig07(csv_dir: Path, out_dir: Path) -> None:
    rows = read_csv(csv_dir / "fig07_cost_throughput_proxy.csv")
    days = [datetime.strptime(r["day"], "%Y-%m-%d") for r in rows]
    msgs = [int(r["messages"]) for r in rows]
    tools = [int(r["tool_calls"]) for r in rows]

    fig, ax = plt.subplots(figsize=(11.2, 4.8))
    ax.plot(days, msgs, color=PALETTE["pos"], linewidth=2.0, label="messages/day")
    ax.fill_between(days, msgs, color=PALETTE["pos"], alpha=0.18)
    ax.set_ylabel("Messages/day", color=PALETTE["text_secondary"])
    ax.grid(axis="y", alpha=0.35)

    ax2 = ax.twinx()
    ax2.plot(days, tools, color=PALETTE["text_secondary"], linewidth=1.6, label="tool_calls/day")
    ax2.set_ylabel("Tool calls/day", color=PALETTE["text_secondary"])
    ax2.tick_params(axis="y", colors=PALETTE["text_secondary"])

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(days) // 10)))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    ax.set_title("Daily Throughput Proxy: Messages vs Tool Calls")
    save_svg(fig, out_dir / "fig07_cost_throughput_proxy.svg")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--csv-dir",
        default="docs/assets/blog/medium/csv",
        help="Directory containing fig01..fig07 CSV files",
    )
    p.add_argument(
        "--out-dir",
        default="docs/assets/blog/medium/figures",
        help="Directory for SVG outputs",
    )
    args = p.parse_args()

    csv_dir = Path(args.csv_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    setup_style()
    plot_fig01(csv_dir, out_dir)
    plot_fig02(csv_dir, out_dir)
    plot_fig03(csv_dir, out_dir)
    plot_fig04(csv_dir, out_dir)
    plot_fig05(csv_dir, out_dir)
    plot_fig06(csv_dir, out_dir)
    plot_fig07(csv_dir, out_dir)

    print(f"Wrote SVG figures to {out_dir}")
    for pth in sorted(out_dir.glob("fig0*.svg")):
        print(pth.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
