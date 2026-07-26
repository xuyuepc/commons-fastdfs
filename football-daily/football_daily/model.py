from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
import penaltyblog as pb
from scipy.stats import poisson


def fit_dixon_coles(
    results: pd.DataFrame,
    as_of: datetime | None = None,
    xi: float = 0.0065,
) -> pb.models.DixonColesGoalModel:
    """用历史赛果拟合时间衰减 Dixon-Coles。"""
    df = results.copy()
    if as_of is not None:
        df = df[df["date"] < pd.Timestamp(as_of)]
    if df.empty:
        raise ValueError("没有可用于建模的历史赛果")

    hg = np.array(df["hg"], dtype=np.int64, copy=True)
    ag = np.array(df["ag"], dtype=np.int64, copy=True)
    home = np.array(df["home"], dtype=object, copy=True)
    away = np.array(df["away"], dtype=object, copy=True)
    weights = np.array(
        pb.models.dixon_coles_weights(list(df["date"]), xi=xi),
        dtype=np.float64,
        copy=True,
    )
    model = pb.models.DixonColesGoalModel(hg, ag, home, away, weights=weights)
    model.fit()
    return model


def predict_match(
    model: pb.models.DixonColesGoalModel,
    home: str,
    away: str,
    max_goals: int = 8,
) -> dict:
    """预测单场；未知球队用联赛平均攻防（适合友谊赛）。"""
    params = model.get_params()
    teams = _teams_from_params(params)
    if home in teams and away in teams:
        pred = model.predict(home, away)
        mh, md, ma = map(float, pred.home_draw_away)
        hx = float(pred.home_goal_expectation)
        ax = float(pred.away_goal_expectation)
        sm = np.array(pred.goal_matrix, copy=True)
    else:
        hx, ax, sm = _predict_with_averages(params, home, away, max_goals=max_goals)
        idx_h, idx_a = np.indices(sm.shape)
        mh = float(sm[idx_h > idx_a].sum())
        md = float(sm[idx_h == idx_a].sum())
        ma = float(sm[idx_h < idx_a].sum())

    totals = np.add.outer(np.arange(sm.shape[0]), np.arange(sm.shape[1]))
    over25 = float(sm[totals >= 3].sum())
    return {
        "model_home": mh,
        "model_draw": md,
        "model_away": ma,
        "xg_home": float(hx),
        "xg_away": float(ax),
        "over25": over25,
    }


def _teams_from_params(params: dict) -> set[str]:
    teams = set()
    for k in params:
        if k.startswith("attack_"):
            teams.add(k[len("attack_") :])
    return teams


def _predict_with_averages(params: dict, home: str, away: str, max_goals: int = 8):
    attacks = {k[len("attack_") :]: float(v) for k, v in params.items() if k.startswith("attack_")}
    defences = {k[len("defence_") :]: float(v) for k, v in params.items() if k.startswith("defence_")}
    avg_att = float(np.mean(list(attacks.values())))
    avg_def = float(np.mean(list(defences.values())))
    home_adv = float(params.get("home_advantage", 0.25))

    att_h = attacks.get(home, avg_att)
    def_h = defences.get(home, avg_def)
    att_a = attacks.get(away, avg_att)
    def_a = defences.get(away, avg_def)

    # 未知客/主队略降强度，避免友谊赛虚高
    if home not in attacks:
        att_h *= 0.9
        def_h *= 0.9
    if away not in attacks:
        att_a *= 0.9
        def_a *= 0.9

    mu_h = float(np.exp(att_h + def_a + home_adv))
    mu_a = float(np.exp(att_a + def_h))

    xs = np.arange(max_goals + 1)
    ph = poisson.pmf(xs, mu_h)
    pa = poisson.pmf(xs, mu_a)
    # 截断归一
    ph = ph / ph.sum()
    pa = pa / pa.sum()
    sm = np.outer(ph, pa)
    return mu_h, mu_a, sm