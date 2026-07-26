from __future__ import annotations

from datetime import date, datetime

import numpy as np
import pandas as pd
import penaltyblog as pb

from .fetch_football_data import big5_club_set, fetch_big5_results
from .fetch_odds import (
    demo_kleague_odds,
    fetch_oddsmath_day,
    filter_big5,
    filter_kleague,
)
from .fetch_results import fetch_kleague1_results
from .leagues import BIG5
from .model import fit_dixon_coles, predict_match


def market_probs(odds_home: float, odds_draw: float, odds_away: float) -> dict:
    raw = np.array([1 / odds_home, 1 / odds_draw, 1 / odds_away], dtype=float)
    basic = raw / raw.sum()
    sp = basic.copy()
    try:
        shin = pb.implied.calculate_implied(
            [float(odds_home), float(odds_draw), float(odds_away)],
            method="shin",
        )
        sp = np.asarray(shin.probabilities, dtype=float)
    except Exception:
        pass
    return {
        "mkt_home": float(basic[0]),
        "mkt_draw": float(basic[1]),
        "mkt_away": float(basic[2]),
        "shin_home": float(sp[0]),
        "shin_draw": float(sp[1]),
        "shin_away": float(sp[2]),
    }


def classify(row: dict) -> tuple[str, str]:
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

    if gap < 0.04:
        risk = "可参考"
    elif gap > 0.12:
        risk = "偏差大·谨慎"
    else:
        risk = "常规"

    # 友谊赛默认更谨慎
    if row.get("league_key") == "FRIENDLY" or "友谊赛" in str(row.get("league", "")):
        if risk == "可参考":
            risk = "常规"
        tip = f"{tip}(友谊赛)"

    return tip, risk


def build_daily_big5(
    day: date | None = None,
    use_cache: bool = True,
    include_friendlies: bool = True,
) -> pd.DataFrame:
    """五大联赛每日分析；休赛期可附带五大联赛球队友谊赛。"""
    day = day or date.today()
    as_of = datetime.combine(day, datetime.min.time())

    results_all = fetch_big5_results(day=day, use_cache=use_cache)
    clubs = big5_club_set(results_all)

    try:
        odds_all = fetch_oddsmath_day(day, use_cache=use_cache)
        odds = filter_big5(odds_all, club_set=clubs, include_friendlies=include_friendlies)
    except Exception:
        odds = pd.DataFrame()

    if odds.empty:
        return pd.DataFrame()

    # 每个联赛单独拟合模型
    models = {}
    for key in BIG5:
        hist = results_all[results_all["league_key"] == key]
        hist = hist[hist["date"] < pd.Timestamp(as_of)]
        if len(hist) < 40:
            continue
        try:
            models[key] = fit_dixon_coles(hist, as_of=as_of)
        except Exception:
            continue

    rows: list[dict] = []
    for _, r in odds.iterrows():
        league_key = r.get("league_key")
        model = None
        sample_n = 0
        league_name = r.get("league", "")

        if league_key in models:
            model = models[league_key]
            sample_n = int(
                len(results_all[(results_all["league_key"] == league_key) & (results_all["date"] < pd.Timestamp(as_of))])
            )
            league_name = BIG5[league_key]["name"]
        elif league_key == "FRIENDLY":
            # 友谊赛：用主队所属联赛模型，否则跳过无法预测的
            model, league_name, sample_n = _pick_friendly_model(
                r["home"], r["away"], results_all, models, as_of
            )
            if model is None:
                continue
        else:
            continue

        try:
            pred = predict_match(model, r["home"], r["away"])
        except Exception:
            continue

        mkt = market_probs(r["odds_home"], r["odds_draw"], r["odds_away"])
        item = {
            "date": r["date"],
            "kickoff": r.get("kickoff", ""),
            "league": league_name,
            "league_key": league_key,
            "home": r["home"],
            "away": r["away"],
            "odds_home": float(r["odds_home"]),
            "odds_draw": float(r["odds_draw"]),
            "odds_away": float(r["odds_away"]),
            "status": r.get("status", ""),
            "source": r.get("source", ""),
            "sample_n": sample_n,
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
    return pd.DataFrame(rows).sort_values(["league", "kickoff", "home"]).reset_index(drop=True)


def _pick_friendly_model(home, away, results_all, models, as_of):
    for team in (home, away):
        for key, model in models.items():
            hist = results_all[results_all["league_key"] == key]
            clubs = set(hist["home"]).union(set(hist["away"]))
            if team in clubs:
                # 对方也尽量在同一模型里；否则仍用该联赛模型（客队可能是其他联赛）
                sample_n = int(len(hist[hist["date"] < pd.Timestamp(as_of)]))
                return model, f"{BIG5[key]['name']}相关友谊赛", sample_n
    return None, "", 0


def build_daily_kleague(
    day: date | None = None,
    season: int | None = None,
    use_cache: bool = True,
    allow_demo_odds: bool = True,
) -> pd.DataFrame:
    """保留韩职能力（可选）。"""
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
            continue
        mkt = market_probs(r["odds_home"], r["odds_draw"], r["odds_away"])
        item = {
            "date": r["date"],
            "kickoff": r.get("kickoff", ""),
            "league": "K League 1",
            "league_key": "KLEAGUE",
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
    return pd.DataFrame(rows).sort_values(["kickoff", "home"]).reset_index(drop=True)


def to_display(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return pd.DataFrame(
        {
            "联赛": df.get("league", ""),
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