# Pilbara 矿权日报

报告日期：2026-10-14（Asia/Shanghai）｜新闻窗口：近 7 个自然日

> **离线演示：新闻、资源和价格均为合成样例，不是真实行情或公司披露。**

## 新闻摘要

- **Pilbara Demo announces a synthetic operating update**（2026-10-13）[S1]
  原文摘录：Synthetic maintenance review. Invented news for testing.
- **Pilbara Demo reviews synthetic expansion timetable**（2026-10-12）[S2]
  原文摘录：Synthetic expansion review. Not a real announcement.

## 资源量与报告口径

资源量（Resources）不等于可采储量（Reserves）；以下数据按报告日期披露。

| 矿区 | 分类 | 矿石量 | 品位 | 披露金属／氧化物量 | 日期／标准 |
|---|---|---:|---:|---:|---|
| Synthetic Deposit | Indicated | 100 Mt | 1.2 % Li2O | 1.2e+06 t | 2026-06-30 / JORC |
| Synthetic Deposit | Inferred | 50 Mt | 0.9 % Li2O | 450000 t | 2026-06-30 / JORC |

- Synthetic Deposit Indicated：cut-off `0.2% Li2O`；储量包含口径 `inclusive_of_reserves`；PDF 第 2 页。[S3]
- Synthetic Deposit Inferred：cut-off `0.2% Li2O`；储量包含口径 `inclusive_of_reserves`；PDF 第 2 页。[S3]

## 价格与走势

指定日期 2026-10-14：**12.5 USD/kg**；SYNTHETIC lithium hydroxide contract fixture。[S4]

| 观测日期 | 价格 |
|---|---:|
| 2026-10-08 | 12 USD/kg |
| 2026-10-09 | 12.2 USD/kg |
| 2026-10-12 | 12.1 USD/kg |
| 2026-10-13 | 12.4 USD/kg |
| 2026-10-14 | 12.5 USD/kg |

窗口内首末观测值变化：**+4.17%**（2026-10-08 至 2026-10-14，共 5 个观测值）。[S4]

## 风险与待核验事项

- 该资源数据按 JORC 披露，不能称为 NI 43-101 报告。
- 氢氧化锂合约、锂辉石精矿报价及矿石中的 Li2O 含量口径不同，不可直接替代。
- Lithium hydroxide contract is not spodumene concentrate or Li2O resource value
- 新闻采用带来源的摘录；未从新闻或资源表推断采矿权法律状态。

## 引用来源

- [S1] 演示引用 `demo://news/operations`，对应仓库 `src/mining_daily/fixtures/` 中的合成数据。
- [S2] 演示引用 `demo://news/expansion`，对应仓库 `src/mining_daily/fixtures/` 中的合成数据。
- [S3] 演示引用 `demo://pilbara-resources.pdf`，对应仓库 `src/mining_daily/fixtures/` 中的合成数据。
- [S4] 演示引用 `demo://prices/lithium`，对应仓库 `src/mining_daily/fixtures/` 中的合成数据。

## 执行记录

通过 MCP 协议调用 6 次工具；发现 3 个独立 Server。完整工具响应和耗时见同名 JSON。
