# 每日足球盘口分析工具

用 GitHub 开源库 [penaltyblog](https://github.com/martineastwood/penaltyblog) 做 **Dixon-Coles 模型概率**，对比当日欧赔去水概率，方便每天打开查看。

当前默认联赛：**韩国 K League 1**。

## 功能

- 自动拉取赛季历史赛果（TheSportsDB）
- 拉取当日欧赔（OddsMath；失败时回退演示盘口，保证页面可开）
- Dixon-Coles（时间衰减）预测 1X2 / xG / 大 2.5
- Shin 去水与市场对比，给出「模型更看主/客/平」判断
- Streamlit 页面每日查看 + CLI 导出 CSV

## 安装

```bash
cd football-daily
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 每日查看（网页）

```bash
cd football-daily
streamlit run app/streamlit_app.py
```

浏览器打开终端提示的本地地址（通常是 `http://localhost:8501`）。

## 命令行

```bash
# 今天
python -m football_daily

# 指定日期并强制刷新
python -m football_daily --date 2026-07-26 --no-cache

# 自定义导出路径
python -m football_daily --csv data/today.csv
```

## 怎么读结果

| 标签 | 含义 |
|------|------|
| 模型≈市场 | 模型与盘口接近，适合当基准 |
| 模型更看主/客/平 | 相对市场有方向差 |
| 偏差大·谨慎 | 裂口过大，建议只观察、不重仓结论 |
| 可参考 | 偏差小或焦点战，可用性更高 |

## 目录

```
football-daily/
  app/streamlit_app.py      # 每日查看页
  football_daily/           # 核心逻辑
  data/cache/               # 抓取缓存
  requirements.txt
```

## 说明

- 本工具只做数据分析与盘口对比，**不提供投注建议**。
- 盘口会临场变动；点侧栏「刷新数据」可重抓。
- 若外网源不稳定，会使用缓存或演示盘口，页面仍可浏览。