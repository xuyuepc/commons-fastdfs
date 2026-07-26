from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from football_daily.analyze import build_daily_big5, to_display
from football_daily.report_html import write_daily_html

st.set_page_config(page_title="五大联赛每日盘口分析", page_icon="⚽", layout="wide")
st.title("五大联赛每日盘口分析")
st.caption("更推荐直接生成 HTML：`python3 -m football_daily --open`")

with st.sidebar:
    day = st.date_input("日期", value=date.today())
    friendlies = st.checkbox("含五大联赛球队友谊赛", value=True)
    refresh = st.button("刷新", type="primary")

@st.cache_data(ttl=1800, show_spinner=False)
def _load(day_iso: str, friendlies: bool, bust: int) -> pd.DataFrame:
    return build_daily_big5(
        day=date.fromisoformat(day_iso),
        use_cache=bust == 0,
        include_friendlies=friendlies,
    )

bust = int(datetime.now().timestamp()) if refresh else 0
with st.spinner("生成中…"):
    try:
        df = _load(day.isoformat(), friendlies, bust)
        err = None
    except Exception as e:
        df, err = pd.DataFrame(), str(e)

if err:
    st.error(err)
    st.stop()

if df.empty:
    st.warning("今日暂无五大联赛正式场次（可能休赛期）。可勾选友谊赛或换日期。")
else:
    st.dataframe(to_display(df), use_container_width=True, hide_index=True)

html_path = ROOT / "reports" / f"daily_big5_{day.isoformat()}.html"
write_daily_html(df, day, html_path)
st.download_button(
    "下载 HTML 日报",
    data=html_path.read_bytes(),
    file_name=html_path.name,
    mime="text/html",
)
st.caption(f"已写入 {html_path}")