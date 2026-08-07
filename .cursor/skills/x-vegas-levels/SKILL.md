---
name: x-vegas-levels
description: Use when the user sends an x-command for crypto levels such as `x ETH`, `x BTC`, `x ETH 空`, or asks for Gate short-term Vegas 入场/止损/止盈 point levels.
---

# x Vegas Levels

高杠杆短线点位指令。用户发 `x <币种>` 时，用 Gate 行情 + 改装维加斯规则，只输出死点位。

## Trigger

Match messages like:

- `x ETH`
- `x BTC`
- `x ETHUSDT`
- `x ETH 空` / `x ETH 多`
- `x eth`（大小写不敏感）

Default exchange: **Gate** spot `BASE_USDT`.

## REQUIRED workflow

1. Parse symbol (and optional side: `多`/`空`/`long`/`short`).
2. Run the script (do not invent prices):

```bash
python3 .cursor/skills/x-vegas-levels/scripts/levels.py ETH
# optional side:
python3 .cursor/skills/x-vegas-levels/scripts/levels.py ETH --side 空
```

3. Read JSON. Reply in **Simplified Chinese** using the Output Contract below.
4. If script errors, one-line failure + retry once; still no vague multi-scenario essay.

## Rules encoded in script

- **1H bias filter:** Vegas EMA 12 / 144 / 169 / 576 / 676  
  - long only if price & EMA12 above 144/169 and price above 576/676  
  - short only if opposite  
  - else `flat` → 空仓
- **Entry:** 15m micro-tunnel (EMA34/55) pullback rail (or last if already deeper)
- **Stop:** beyond micro tunnel by ~1×5m ATR (min distance enforced)
- **TP:** **2R** (or nearer recent 15m swing if between 1R and 2R)
- **Kill:** 1H mid-tunnel opposite rail (system flatten level)

## Output Contract (MANDATORY)

If `side` is long/short, reply with ONLY this shape (no confidence, no alternatives, no essay):

```text
做多 ETH（Gate）

入场：{entry}
止损：{stop}
止盈：{tp}
```

or

```text
做空 ETH（Gate）

入场：{entry}
止损：{stop}
止盈：{tp}
```

If `side` is `flat`:

```text
空仓 ETH（Gate）

原因：1H过滤无方向
熔断参考：{h1_144_169}
```

Optional one trailing line only if useful: `现价：{last}` — nothing else.

## Hard bans

| Excuse | Reality |
|--------|---------|
| "先分析再给点位" | `x` 指令只要三价 |
| "给几个方案让用户选" | 只给一套 entry/stop/tp |
| "信心/大概/可以考虑" | 禁止模糊词 |
| "行情不好建议观望" 却仍罗列多空 | flat 就输出空仓模板 |
| "编个点位先应付" | 必须跑脚本 |

## Red Flags — STOP

- Replying without running `levels.py`
- More than ~8 lines in the reply
- Multiple entry zones / “激进/稳健” 双方案
- Asking user to restate the Vegas rules

**Violating the letter of the rules is violating the spirit of the rules.**
