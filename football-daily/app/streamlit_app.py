from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from football_daily.analyze import build_daily_kleague, to_display

st.set_page_config(
    page_title="每日足球盘口分析",
    page_icon="⚽",
    layout="wide",
)

st.title("每日足球盘口分析")
st.caption("Dixon-Coles 模型概率 × 市场去水赔率 · 当前支持 K League 1")

with st.sidebar:
    st.header("筛选")
    day = st.date_input("日期", value=date.today())
    refresh = st.button("刷新数据", type="primary")
    st.markdown("---")
    st.markdown(
        """
**怎么读**
- **模型≈市场**：双方定价接近，可作基准
- **模型更看主/客**：模型相对盘口有方向差
- **偏差大·谨慎**：裂口过大，建议只观察
        """
    )
    st.caption("数据源：TheSportsDB 赛果 + OddsMath 欧赔（失败时用演示盘口）")

@st.cache_data(ttl=1800, show_spinner=False)
def _load(day_iso: str, bust: int) -> pd.DataFrame:
    d = date.fromisoformat(day_iso)
    return build_daily_kleague(day=d, use_cache=bust == 0)


bust = int(datetime.now().timestamp()) if refresh else 0
with st.spinner("正在拉取赛果 / 盘口并拟合模型…"):
    try:
        df = _load(day.isoformat(), bust)
        err = None
    except Exception as e:
        df = pd.DataFrame()
        err = str(e)

if err:
    st.error(f"生成失败：{err}")
    st.stop()

if df.empty:
    st.warning("这一天没有解析到韩职场次。可换日期，或点击「刷新数据」。")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("场次", len(df))
c2.metric("样本场次", int(df["sample_n"].iloc[0]))
c3.metric("可参考", int((df["risk"] == "可参考").sum()))
c4.metric("需谨慎", int((df["risk"] == "偏差大·谨慎").sum()))

st.subheader("总览")
view = to_display(df)
st.dataframe(view, use_container_width=True, hide_index=True)

st.subheader("单场详情")
labels = [f"{r.kickoff} {r.home} vs {r.away}" for r in df.itertuples()]
choice = st.selectbox("选择比赛", labels)
row = df.iloc[labels.index(choice)]

m1, m2, m3 = st.columns(3)
m1.metric("模型主胜", f"{row['model_home']*100:.1f}%", f"{row['edge_home_pp']:+.1f}pp vs 市场")
m2.metric("模型平局", f"{row['model_draw']*100:.1f}%")
m3.metric("模型客胜", f"{row['model_away']*100:.1f}%", f"{row['edge_away_pp']:+.1f}pp vs 市场")

d1, d2, d3 = st.columns(3)
d1.write(f"**欧赔** `{row['odds_home']:.2f} / {row['odds_draw']:.2f} / {row['odds_away']:.2f}`")
d2.write(f"**期望进球** `{row['xg_home']:.2f} - {row['xg_away']:.2f}`")
d3.write(f"**大2.5球** `{row['over25']*100:.1f}%` · **判断** `{row['tip']}` · **标签** `{row['risk']}`")

chart_df = pd.DataFrame(
    {
        "结果": ["主胜", "平局", "客胜"],
        "模型": [row["model_home"], row["model_draw"], row["model_away"]],
        "市场去水": [row["mkt_home"], row["mkt_draw"], row["mkt_away"]],
        "Shin去水": [row["shin_home"], row["shin_draw"], row["shin_away"]],
    }
).set_index("结果")
st.bar_chart(chart_df)

st.download_button(
    "下载今日 CSV",
    data=view.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"kleague_daily_{day.isoformat()}.csv",
    mime="text/csv",
)

st.markdown("---")
st.caption(
    f"生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · "
    f"历史窗口截止 {day - timedelta(days=0)} 开赛前 · 仅供分析参考，不构成投注建议"
)