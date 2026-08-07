#!/usr/bin/env python3
"""Gate spot short-term Vegas levels for `x <SYMBOL>` skill.

Outputs machine-readable JSON with hard entry/stop/tp.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone


GATE = "https://api.gateio.ws/api/v4"


def http_get(url: str):
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "x-vegas-levels/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def fetch_candles(pair: str, interval: str, limit: int = 1000, pages: int = 1):
    rows = []
    to_ = None
    for _ in range(pages):
        url = (
            f"{GATE}/spot/candlesticks?currency_pair={pair}"
            f"&interval={interval}&limit={limit}"
        )
        if to_ is not None:
            url += f"&to={to_}"
        batch = http_get(url)
        if not batch:
            break
        rows = batch + rows
        to_ = int(batch[0][0]) - 1
    seen = set()
    out = []
    for row in rows:
        t = int(row[0])
        if t not in seen:
            seen.add(t)
            out.append(row)
    out.sort(key=lambda x: int(x[0]))
    return out


def pack(rows):
    # Gate: [t, quote_vol, close, high, low, open, base_vol, closed]
    return {
        "ts": [int(r[0]) for r in rows],
        "c": [float(r[2]) for r in rows],
        "h": [float(r[3]) for r in rows],
        "l": [float(r[4]) for r in rows],
        "o": [float(r[5]) for r in rows],
    }


def ema(series, period):
    if len(series) < period:
        return [None] * len(series)
    k = 2 / (period + 1)
    out = [None] * (period - 1)
    out.append(sum(series[:period]) / period)
    for price in series[period:]:
        out.append(price * k + out[-1] * (1 - k))
    return out


def atr(h, l, c, period=14):
    trs = []
    for i in range(1, len(c)):
        tr = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        trs.append(tr)
    if len(trs) < period:
        return None
    return sum(trs[-period:]) / period


def round_px(x: float) -> float:
    if x >= 1000:
        return round(x, 1)
    if x >= 100:
        return round(x, 2)
    if x >= 1:
        return round(x, 3)
    return round(x, 6)


def normalize_symbol(raw: str) -> str:
    s = raw.strip().upper().replace("-", "").replace("_", "").replace("/", "")
    if s.endswith("USDT"):
        base = s[: -4]
    else:
        base = s
    if not base:
        raise ValueError("empty symbol")
    return f"{base}_USDT"


def compute(pair: str, side_hint: str | None = None):
    ticker = http_get(f"{GATE}/spot/tickers?currency_pair={pair}")[0]
    last = float(ticker["last"])

    h1 = pack(fetch_candles(pair, "1h", pages=2))
    m15 = pack(fetch_candles(pair, "15m", pages=2))
    m5 = pack(fetch_candles(pair, "5m", pages=1))

    e12_1 = ema(h1["c"], 12)
    e144 = ema(h1["c"], 144)
    e169 = ema(h1["c"], 169)
    e576 = ema(h1["c"], 576)
    e676 = ema(h1["c"], 676)

    if None in (e12_1[-1], e144[-1], e169[-1], e576[-1], e676[-1]):
        raise RuntimeError("insufficient 1H history for Vegas EMAs")

    tu1, tl1 = max(e144[-1], e169[-1]), min(e144[-1], e169[-1])
    lu1, ll1 = max(e576[-1], e676[-1]), min(e576[-1], e676[-1])

    long_ok = last > lu1 and last > tu1 and e12_1[-1] > tu1
    short_ok = last < ll1 and last < tl1 and e12_1[-1] < tl1

    if side_hint in ("long", "多", "做多", "l"):
        side = "long"
        if not long_ok:
            bias = "forced_long_against_filter"
        else:
            bias = "long"
    elif side_hint in ("short", "空", "做空", "s"):
        side = "short"
        if not short_ok:
            bias = "forced_short_against_filter"
        else:
            bias = "short"
    else:
        if long_ok:
            side, bias = "long", "long"
        elif short_ok:
            side, bias = "short", "short"
        else:
            side, bias = "flat", "flat"

    f12 = ema(m15["c"], 12)
    f34 = ema(m15["c"], 34)
    f55 = ema(m15["c"], 55)
    mtu, mtl = max(f34[-1], f55[-1]), min(f34[-1], f55[-1])
    atr5 = atr(m5["h"], m5["l"], m5["c"], 14) or (last * 0.003)
    s21 = ema(m5["c"], 21)[-1]

    kill_long = round_px(tl1)
    kill_short = round_px(tu1)

    if side == "flat":
        return {
            "exchange": "gate",
            "pair": pair,
            "last": round_px(last),
            "side": "flat",
            "bias": bias,
            "action": "空仓",
            "entry": None,
            "stop": None,
            "tp": None,
            "kill": None,
            "reason": "1H过滤无方向（未同时满足隧道多/空条件）",
            "levels": {
                "h1_144_169": [round_px(tl1), round_px(tu1)],
                "h1_576_676": [round_px(ll1), round_px(lu1)],
                "m15_micro": [round_px(mtl), round_px(mtu)],
            },
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

    if side == "long":
        # Prefer pullback to 15m micro upper; if already nearby, use mid of zone.
        ideal = mtu
        entry = round_px(ideal)
        # If price already below ideal (deeper pullback), use current area.
        if last < ideal:
            entry = round_px(last)
        stop = round_px(min(mtl, s21) - 1.0 * atr5)
        # Ensure stop below entry with minimum distance ~0.8*ATR
        min_risk = max(0.8 * atr5, last * 0.0015)
        if entry - stop < min_risk:
            stop = round_px(entry - min_risk)
        risk = entry - stop
        tp = round_px(entry + 2.0 * risk)
        # Cap tp near recent swing if closer but still >=1R
        swing = max(m15["h"][-32:])
        if entry + risk <= swing < tp:
            tp = round_px(swing)
        return {
            "exchange": "gate",
            "pair": pair,
            "last": round_px(last),
            "side": "long",
            "bias": bias,
            "action": "做多",
            "entry": entry,
            "stop": stop,
            "tp": tp,
            "kill": kill_long,
            "rr": round((tp - entry) / risk, 2) if risk else None,
            "levels": {
                "h1_144_169": [round_px(tl1), round_px(tu1)],
                "h1_576_676": [round_px(ll1), round_px(lu1)],
                "m15_micro": [round_px(mtl), round_px(mtu)],
                "atr5": round_px(atr5),
            },
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

    # short
    ideal = mtl
    entry = round_px(ideal)
    if last > ideal:
        entry = round_px(last)
    stop = round_px(max(mtu, s21) + 1.0 * atr5)
    min_risk = max(0.8 * atr5, last * 0.0015)
    if stop - entry < min_risk:
        stop = round_px(entry + min_risk)
    risk = stop - entry
    tp = round_px(entry - 2.0 * risk)
    swing = min(m15["l"][-32:])
    if tp < swing <= entry - risk:
        tp = round_px(swing)
    return {
        "exchange": "gate",
        "pair": pair,
        "last": round_px(last),
        "side": "short",
        "bias": bias,
        "action": "做空",
        "entry": entry,
        "stop": stop,
        "tp": tp,
        "kill": kill_short,
        "rr": round((entry - tp) / risk, 2) if risk else None,
        "levels": {
            "h1_144_169": [round_px(tl1), round_px(tu1)],
            "h1_576_676": [round_px(ll1), round_px(lu1)],
            "m15_micro": [round_px(mtl), round_px(mtu)],
            "atr5": round_px(atr5),
        },
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol", help="ETH / BTC / ETHUSDT ...")
    ap.add_argument("--side", default=None, help="long/short/多/空; default auto")
    args = ap.parse_args()
    try:
        pair = normalize_symbol(args.symbol)
        result = compute(pair, args.side)
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
