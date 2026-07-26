from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

from .analyze import build_daily_kleague, to_display
from .config import DATA_DIR


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="每日韩职：Dixon-Coles 模型 vs 盘口")
    parser.add_argument("--date", help="YYYY-MM-DD，默认今天")
    parser.add_argument("--no-cache", action="store_true", help="强制重新抓取")
    parser.add_argument("--csv", help="导出 CSV 路径")
    args = parser.parse_args(argv)

    day = date.fromisoformat(args.date) if args.date else date.today()
    df = build_daily_kleague(day=day, use_cache=not args.no_cache)
    view = to_display(df)

    print(f"日期: {day.isoformat()}  场次: {len(view)}")
    if view.empty:
        print("今日暂无韩职场次或抓取失败。")
        return 1

    print(view.to_string(index=False))

    out = Path(args.csv) if args.csv else DATA_DIR / f"daily_kleague_{day.isoformat()}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    view.to_csv(out, index=False)
    print(f"\n已导出: {out}")
    print(f"生成时间: {datetime.now().isoformat(timespec='seconds')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())