from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
import penaltyblog as pb


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


def predict_match(model: pb.models.DixonColesGoalModel, home: str, away: str) -> dict:
    pred = model.predict(home, away)
    mh, md, ma = map(float, pred.home_draw_away)
    hx = float(pred.home_goal_expectation)
    ax = float(pred.away_goal_expectation)
    sm = np.array(pred.goal_matrix, copy=True)
    totals = np.add.outer(np.arange(sm.shape[0]), np.arange(sm.shape[1]))
    over25 = float(sm[totals >= 3].sum())
    return {
        "model_home": mh,
        "model_draw": md,
        "model_away": ma,
        "xg_home": hx,
        "xg_away": ax,
        "over25": over25,
    }