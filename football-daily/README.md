# 每日足球盘口分析（HTML）

一键生成**独立 HTML 日报**，浏览器直接打开即可查看。

默认联赛：**英超 / 西甲 / 意甲 / 德甲 / 法甲**（不做中超）。  
模型：GitHub [penaltyblog](https://github.com/martineastwood/penaltyblog) Dixon-Coles × 市场去水欧赔。

## 安装

```bash
cd football-daily
pip install -r requirements.txt
```

## 每日生成 HTML

```bash
# 今天（默认输出 reports/daily_big5_YYYY-MM-DD.html）
python3 -m football_daily

# 指定日期，并自动打开浏览器
python3 -m football_daily --date 2026-07-26 --open

# 只要正式联赛，不要友谊赛
python3 -m football_daily --no-friendlies

# 自定义 HTML 路径
python3 -m football_daily --html reports/today.html --open
```

生成后打开：

```bash
open reports/daily_big5_2026-07-26.html   # macOS
xdg-open reports/daily_big5_2026-07-26.html  # Linux
```

## 说明

| 项目 | 内容 |
|------|------|
| 赛果 | football-data.co.uk 近两季 |
| 当日盘口 | OddsMath 欧赔 |
| 休赛期 | 自动附带「五大联赛球队友谊赛」（可用 `--no-friendlies` 关闭） |
| 输出 | `reports/*.html` + `data/*.csv` |

页面标签：

- **模型≈市场 / 模型更看主|客|平**
- **可参考 / 常规 / 偏差大·谨慎**

仅供分析参考，不构成投注建议。

## 可选：韩职 / Streamlit

```bash
python3 -m football_daily --kleague --html
streamlit run app/streamlit_app.py
```

## 目录

```
football-daily/
  reports/                 # 每日 HTML
  football_daily/          # 核心逻辑
  app/streamlit_app.py     # 可选网页服务
  data/cache/              # 抓取缓存
```