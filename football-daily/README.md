# 每日足球盘口分析（HTML）

一键生成**独立 HTML 日报**，浏览器直接打开即可查看。

默认联赛：**英超 / 西甲 / 意甲 / 德甲 / 法甲**（不做中超）。  
模型：GitHub [penaltyblog](https://github.com/martineastwood/penaltyblog) Dixon-Coles × 市场去水欧赔。

## 在你自己电脑上用（推荐）

### Windows
1. 安装 [Python 3.10+](https://www.python.org/downloads/)（勾选 Add Python to PATH）
2. 把本仓库的 `football-daily` 文件夹放到本地
3. **双击** `生成日报.bat`
4. 浏览器会自动打开；文件在 `reports\daily_big5_今天日期.html`

指定日期：双击 `生成指定日期.bat`，按提示输入 `YYYY-MM-DD`。

### macOS / Linux
```bash
cd football-daily
python3 -m pip install -r requirements.txt
python3 -m football_daily --open
```

HTML 生成在本地：
`football-daily/reports/daily_big5_YYYY-MM-DD.html`

### 常用命令

```bash
# 今天
python3 -m football_daily --open

# 指定日期
python3 -m football_daily --date 2025-12-14 --open

# 不要友谊赛
python3 -m football_daily --no-friendlies --open
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