from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd

def render_daily_html(df: pd.DataFrame, day, title: str = "五大联赛每日盘口分析") -> str:
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    day_s = day.isoformat() if hasattr(day, "isoformat") else str(day)

    if df is None or df.empty:
        body = _empty_state(day_s)
    else:
        body = _matches_body(df)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{escape(title)} · {escape(day_s)}</title>
<style>
:root {{
  --bg0: #0f1714;
  --bg1: #16241e;
  --ink: #e8f0ea;
  --muted: #9bb0a3;
  --line: rgba(232,240,234,.12);
  --accent: #d7a35a;
  --good: #6fbf8a;
  --warn: #e0a45a;
  --bad: #e07a6a;
  --card: rgba(255,255,255,.04);
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: "Iowan Old Style", "Palatino Linotype", "Songti SC", "Noto Serif SC", Georgia, serif;
  color: var(--ink);
  background:
    radial-gradient(1200px 600px at 10% -10%, rgba(215,163,90,.18), transparent 55%),
    radial-gradient(900px 500px at 90% 0%, rgba(111,191,138,.12), transparent 50%),
    linear-gradient(180deg, var(--bg1), var(--bg0) 40%, #0c1210);
  min-height: 100vh;
}}
.wrap {{ max-width: 1100px; margin: 0 auto; padding: 32px 20px 64px; }}
header {{
  display: grid;
  gap: 10px;
  margin-bottom: 28px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 20px;
}}
.brand {{
  font-size: clamp(2rem, 4vw, 2.8rem);
  letter-spacing: .02em;
  margin: 0;
  line-height: 1.1;
}}
.sub {{
  color: var(--muted);
  font-family: "Segoe UI", "PingFang SC", "Noto Sans SC", sans-serif;
  font-size: .95rem;
  margin: 0;
}}
.meta {{
  display: flex; flex-wrap: wrap; gap: 10px 16px;
  font-family: "Segoe UI", "PingFang SC", sans-serif;
  font-size: .85rem;
  color: var(--muted);
}}
.pill {{
  border: 1px solid var(--line);
  background: var(--card);
  padding: .35rem .7rem;
  border-radius: 999px;
}}
.league-block {{ margin: 28px 0; }}
.league-title {{
  font-size: 1.25rem;
  margin: 0 0 12px;
  color: var(--accent);
}}
.table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 14px; background: var(--card); }}
table {{
  width: 100%;
  border-collapse: collapse;
  font-family: "Segoe UI", "PingFang SC", "Noto Sans SC", sans-serif;
  font-size: .9rem;
}}
th, td {{
  padding: .85rem .75rem;
  border-bottom: 1px solid var(--line);
  text-align: left;
  white-space: nowrap;
}}
th {{ color: var(--muted); font-weight: 600; font-size: .78rem; letter-spacing: .04em; text-transform: uppercase; }}
tr:last-child td {{ border-bottom: 0; }}
.match {{ font-weight: 600; }}
.muted {{ color: var(--muted); }}
.tag {{
  display: inline-block;
  padding: .2rem .55rem;
  border-radius: 999px;
  font-size: .75rem;
  border: 1px solid var(--line);
}}
.tag.ok {{ color: var(--good); border-color: rgba(111,191,138,.35); background: rgba(111,191,138,.08); }}
.tag.warn {{ color: var(--warn); border-color: rgba(224,164,90,.35); background: rgba(224,164,90,.08); }}
.tag.hot {{ color: var(--accent); border-color: rgba(215,163,90,.4); background: rgba(215,163,90,.1); }}
.cards {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
  margin-top: 18px;
}}
.card {{
  border: 1px solid var(--line);
  background: var(--card);
  border-radius: 14px;
  padding: 14px 16px;
}}
.card h3 {{ margin: 0 0 8px; font-size: 1.05rem; }}
.bars {{ display: grid; gap: 8px; margin-top: 10px; }}
.bar-row {{ display: grid; grid-template-columns: 42px 1fr 48px; gap: 8px; align-items: center; font-size: .8rem; font-family: "Segoe UI", "PingFang SC", sans-serif; }}
.track {{ height: 8px; background: rgba(255,255,255,.08); border-radius: 99px; overflow: hidden; }}
.fill {{ height: 100%; border-radius: 99px; }}
.fill.model {{ background: linear-gradient(90deg, #d7a35a, #e6c38a); }}
.fill.market {{ background: linear-gradient(90deg, #6fbf8a, #9fd7b0); }}
.legend {{ display:flex; gap:14px; color: var(--muted); font-size:.78rem; margin-top:8px; font-family:"Segoe UI","PingFang SC",sans-serif; }}
.dot {{ width:8px; height:8px; border-radius:50%; display:inline-block; margin-right:6px; }}
.dot.model {{ background:#d7a35a; }}
.dot.market {{ background:#6fbf8a; }}
.empty {{
  border: 1px dashed var(--line);
  border-radius: 16px;
  padding: 36px 22px;
  text-align: center;
  background: var(--card);
}}
.empty h2 {{ margin: 0 0 8px; }}
footer {{
  margin-top: 36px;
  color: var(--muted);
  font-size: .8rem;
  font-family: "Segoe UI", "PingFang SC", sans-serif;
  line-height: 1.6;
}}
@media (max-width: 720px) {{
  th:nth-child(n+6), td:nth-child(n+6) {{ display: none; }}
  th:nth-child(4), td:nth-child(4),
  th:nth-child(5), td:nth-child(5) {{ display: table-cell; }}
}}
</style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1 class="brand">{escape(title)}</h1>
      <p class="sub">Dixon-Coles 模型概率 × 市场去水欧赔 · 打开即看，无需服务器</p>
      <div class="meta">
        <span class="pill">日期 {escape(day_s)}</span>
        <span class="pill">生成 {escape(generated)}</span>
        <span class="pill">英超 / 西甲 / 意甲 / 德甲 / 法甲</span>
        <span class="pill">场次 {0 if df is None or df.empty else len(df)}</span>
      </div>
    </header>
    {body}
    <footer>
      数据：football-data.co.uk（历史赛果）+ OddsMath（当日欧赔）。模型为时间衰减 Dixon-Coles（penaltyblog）。
      仅供分析参考，不构成投注建议。盘口临场会变，请以最新赔率为准。
    </footer>
  </div>
</body>
</html>
"""


def write_daily_html(df: pd.DataFrame, day, path: Path, title: str = "五大联赛每日盘口分析") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_daily_html(df, day, title=title), encoding="utf-8")
    return path


def _empty_state(day_s: str) -> str:
    return f"""
    <section class="empty">
      <h2>今日暂无五大联赛正式场次</h2>
      <p class="muted">日期 {escape(day_s)} 可能处于休赛期。换个有联赛日的日期重新生成即可。</p>
      <p class="muted">命令示例：<code>python3 -m football_daily --date 2025-09-14 --html</code></p>
    </section>
    """


def _matches_body(df: pd.DataFrame) -> str:
    parts: list[str] = []
    # 按联赛分组
    if "league" not in df.columns:
        df = df.copy()
        df["league"] = "比赛"

    for league, g in df.groupby("league", sort=False):
        parts.append(f'<section class="league-block"><h2 class="league-title">{escape(str(league))}</h2>')
        parts.append('<div class="table-wrap"><table><thead><tr>')
        headers = ["开球", "对阵", "欧赔", "模型%", "市场%", "Δ主", "xG", "判断", "标签"]
        parts.extend(f"<th>{h}</th>" for h in headers)
        parts.append("</tr></thead><tbody>")
        for r in g.itertuples():
            tip_cls = "hot" if "更看" in str(r.tip) else "ok"
            risk_cls = "warn" if "谨慎" in str(r.risk) else "ok"
            parts.append("<tr>")
            parts.append(f'<td class="muted">{escape(str(r.kickoff))}</td>')
            parts.append(f'<td class="match">{escape(str(r.home))} vs {escape(str(r.away))}</td>')
            parts.append(
                f'<td class="muted">{r.odds_home:.2f} / {r.odds_draw:.2f} / {r.odds_away:.2f}</td>'
            )
            parts.append(
                f"<td>{r.model_home*100:.0f} / {r.model_draw*100:.0f} / {r.model_away*100:.0f}</td>"
            )
            parts.append(
                f"<td>{r.mkt_home*100:.0f} / {r.mkt_draw*100:.0f} / {r.mkt_away*100:.0f}</td>"
            )
            parts.append(f"<td>{r.edge_home_pp:+.1f}pp</td>")
            parts.append(f'<td class="muted">{r.xg_home:.2f}-{r.xg_away:.2f}</td>')
            parts.append(f'<td><span class="tag {tip_cls}">{escape(str(r.tip))}</span></td>')
            parts.append(f'<td><span class="tag {risk_cls}">{escape(str(r.risk))}</span></td>')
            parts.append("</tr>")
        parts.append("</tbody></table></div>")

        # 卡片详情
        parts.append('<div class="cards">')
        for r in g.itertuples():
            parts.append(_match_card(r))
        parts.append("</div></section>")
    return "\n".join(parts)


def _match_card(r) -> str:
    def bar(label: str, model: float, market: float) -> str:
        return f"""
        <div class="bar-row"><span>{label}</span>
          <div class="track"><div class="fill model" style="width:{model*100:.1f}%"></div></div>
          <span>{model*100:.0f}%</span></div>
        <div class="bar-row"><span></span>
          <div class="track"><div class="fill market" style="width:{market*100:.1f}%"></div></div>
          <span class="muted">{market*100:.0f}%</span></div>
        """

    return f"""
    <article class="card">
      <h3>{escape(str(r.home))} vs {escape(str(r.away))}</h3>
      <div class="muted" style="font-family:Segoe UI,PingFang SC,sans-serif;font-size:.82rem;">
        {escape(str(getattr(r, 'kickoff', '')))} · 大2.5 {r.over25*100:.0f}% · {escape(str(r.tip))}
      </div>
      <div class="bars">
        {bar("主", r.model_home, r.mkt_home)}
        {bar("平", r.model_draw, r.mkt_draw)}
        {bar("客", r.model_away, r.mkt_away)}
      </div>
      <div class="legend"><span><i class="dot model"></i>模型</span><span><i class="dot market"></i>市场</span></div>
    </article>
    """