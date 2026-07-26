from __future__ import annotations

import argparse
import webbrowser
from datetime import date, datetime
from pathlib import Path

from .analyze import build_daily_big5, build_daily_kleague, to_display
from .config import DATA_DIR, ROOT
from .report_html import write_daily_html


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="每日足球盘口分析（默认五大联赛 → HTML）")
    parser.add_argument("--date", help="YYYY-MM-DD，默认今天")
    parser.add_argument("--no-cache", action="store_true", help="强制重新抓取")
    parser.add_argument("--kleague", action="store_true", help="改为输出韩职")
    parser.add_argument("--no-friendlies", action="store_true", help="不附带友谊赛")
    parser.add_argument("--html", nargs="?", const="AUTO", help="导出 HTML（默认开启）")
    parser.add_argument("--no-html", action="store_true", help="不生成 HTML")
    parser.add_argument("--csv", help="导出 CSV 路径")
    parser.add_argument("--open", action="store_true", help="生成后用浏览器打开 HTML")
    args = parser.parse_args(argv)

    day = date.fromisoformat(args.date) if args.date else date.today()
    use_cache = not args.no_cache

    if args.kleague:
        df = build_daily_kleague(day=day, use_cache=use_cache)
        title = "韩职每日盘口分析"
        stem = "daily_kleague"
    else:
        df = build_daily_big5(
            day=day,
            use_cache=use_cache,
            include_friendlies=not args.no_friendlies,
        )
        title = "五大联赛每日盘口分析"
        stem = "daily_big5"

    view = to_display(df)
    print(f"日期: {day.isoformat()}  场次: {len(view)}")
    if view.empty:
        print("今日暂无目标联赛场次（可能是休赛期）。仍会生成空状态 HTML。")
    else:
        print(view.to_string(index=False))

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    reports = ROOT / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    if args.csv:
        csv_path = Path(args.csv)
    else:
        csv_path = DATA_DIR / f"{stem}_{day.isoformat()}.csv"
    if not view.empty:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        view.to_csv(csv_path, index=False)
        print(f"CSV: {csv_path}")

    html_path = None
    if not args.no_html:
        if args.html and args.html != "AUTO":
            html_path = Path(args.html)
        else:
            html_path = reports / f"{stem}_{day.isoformat()}.html"
        write_daily_html(df, day, html_path, title=title)
        print(f"HTML: {html_path.resolve()}")
        if args.open:
            webbrowser.open(html_path.resolve().as_uri())

    print(f"生成时间: {datetime.now().isoformat(timespec='seconds')}")
    return 0 if (not view.empty or html_path) else 1


if __name__ == "__main__":
    raise SystemExit(main())