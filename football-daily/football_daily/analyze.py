from __future__ import annotations

from datetime import date, datetime

import numpy as np
import pandas as pd
import penaltyblog as pb

from .fetch_odds import demo_kleague_odds, fetch_oddsmath_day, filter_kleague
from .fetch_results import fetch_kleague1_results
from .model import fit_dixon_coles, predict_match


def market_probs(odds_home: float, odds_draw: float, odds_away: float) -> dict:
    raw = np.array([1 / odds_home, 1 / odds_draw, 1 / odds_away], dtype=float)
    basic = raw / raw.sum()
    shin = pb.implied.calculate_implied(
        [float(odds_home), float(odds_draw), float(odds_away)],
        method="shin",
    )
    sp = np.asarray(shin.probabilities, dtype=float)
    return {
        "mkt_home": float(basic[0]),
        "mkt_draw": float(basic[1]),
        "mkt_away": float(basic[2]),
        "shin_home": float(sp[0]),
        "shin_draw": float(sp[1]),
        "shin_away": float(sp[2]),
    }


def classify(row: dict) -> tuple[str, str]:
    """返回 (方向判断, 诚信/可用性标签)。"""
    edge_h = row["model_home"] - row["mkt_home"]
    edge_a = row["model_away"] - row["mkt_away"]
    edge_d = row["model_draw"] - row["mkt_draw"]
    gap = max(abs(edge_h), abs(edge_a), abs(edge_d))

    if edge_h > 0.05:
        tip = "模型更看主"
    elif edge_a > 0.05:
        tip = "模型更看客"
    elif edge_d > 0.05:
        tip = "模型更看平"
    elif gap < 0.04:
        tip = "模型≈市场"
    else:
        tip = "小幅偏差"

    teams = {row["home"], row["away"]}
    if teams == {"Seoul", "Ulsan"} or gap < 0.04:
        risk = "可参考"
    elif gap > 0.12:
        risk = "偏差大·谨慎"
    else:
        risk = "常规"

    return tip, risk


def build_daily_kleague(
    day: date | None = None,
    season: int | None = None,
    use_cache: bool = True,
    allow_demo_odds: bool = True,
) -> pd.DataFrame:
    """生成某日韩职：模型概率 vs 盘口。"""
    day = day or date.today()
    season = season or day.year

    results = fetch_kleague1_results(season=season, use_cache=use_cache)
    as_of = datetime.combine(day, datetime.min.time())
    model = fit_dixon_coles(results, as_of=as_of)

    try:
        odds_all = fetch_oddsmath_day(day, use_cache=use_cache)
        odds = filter_kleague(odds_all)
        if odds.empty and allow_demo_odds:
            odds = demo_kleague_odds(day)
            odds["source"] = "demo-fallback"
    except Exception:
        if not allow_demo_odds:
            raise
        odds = demo_kleague_odds(day)
        odds["source"] = "demo-fallback"

    rows: list[dict] = []
    for _, r in odds.iterrows():
        try:
            pred = predict_match(model, r["home"], r["away"])
        except Exception:
            # 队名未出现在历史样本中
            continue
        mkt = market_probs(r["odds_home"], r["odds_draw"], r["odds_away"])
        item = {
            "date": r["date"],
            "kickoff": r.get("kickoff", ""),
            "league": "K League 1",
            "home": r["home"],
            "away": r["away"],
            "odds_home": float(r["odds_home"]),
            "odds_draw": float(r["odds_draw"]),
            "odds_away": float(r["odds_away"]),
            "status": r.get("status", ""),
            "source": r.get("source", ""),
            "sample_n": int(len(results[results["date"] < pd.Timestamp(as_of)])),
            **pred,
            **mkt,
        }
        tip, risk = classify(item)
        item["tip"] = tip
        item["risk"] = risk
        item["edge_home_pp"] = round((item["model_home"] - item["mkt_home"]) * 100, 1)
        item["edge_away_pp"] = round((item["model_away"] - item["mkt_away"]) * 100, 1)
        rows.append(item)

    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    return out.sort_values(["kickoff", "home"]).reset_index(drop=True)


def to_display(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    view = pd.DataFrame(
        {
            "开球": df["kickoff"],
            "主队": df["home"],
            "客队": df["away"],
            "欧赔": df.apply(
                lambda r: f"{r['odds_home']:.2f} / {r['odds_draw']:.2f} / {r['odds_away']:.2f}",
                axis=1,
            ),
            "模型主%": (df["model_home"] * 100).round(1),
            "模型平%": (df["model_draw"] * 100).round(1),
            "模型客%": (df["model_away"] * 100).round(1),
            "市场主%": (df["mkt_home"] * 100).round(1),
            "市场平%": (df["mkt_draw"] * 100).round(1),
            "市场客%": (df["mkt_away"] * 100).round(1),
            "Δ主(pp)": df["edge_home_pp"],
            "Δ客(pp)": df["edge_away_pp"],
            "xG": df.apply(lambda r: f"{r['xg_home']:.2f}-{r['xg_away']:.2f}", axis=1),
            "大2.5%": (df["over25"] * 100).round(1),
            "判断": df["tip"],
            "标签": df["risk"],
            "数据源": df["source"],
        }
    )
    return view