# 数据契约与来源

## 工具响应

所有工具返回同一封装：`status`、`mode`、`data`、`warnings`、`sources`、`fetched_at`。时间使用 ISO 8601，抓取时间为 UTC；日报日期及新闻自然日边界使用 Asia/Shanghai。

`mode=demo` 时仅允许显式 fixture；`mode=live` 从不读取 fixture 作为降级结果。JSON 轨迹记录来源的实际状态，不将“未找到”解释为“没有发生”。

## 新闻

字段：`title`、`url`、`published_at`、`summary`、`publisher`。没有可解析发布时间的条目不进入时间窗口。URL 主机名规范化，去除 fragment 和跟踪参数后去重；保留文章身份相关 query 参数。

检索范围仅限配置 Feed 的条目标题和摘要。Pilbara 的别名包括 Pilgangoora、PLS；其他项目使用关键词匹配。返回最多 10 条，Agent 获取最多 3 篇正文，避免无限工具循环。

## 资源量

资源记录主键由项目、矿区、生效日、报告标准、分类、商品、储量包含口径和 cut-off 组成。Indicated 和 Inferred 独立保存，不合并 Total、Measured 或 Proven/Probable。

`ore`、`grade`、`contained_metal` 各含 `value`、`unit`、`evidence` 和 `unit_evidence`。证据为 `page` 与原文 `quote`。页码从 PDF 第一页开始计数，不等同于报告印刷页码。文件 SHA-256 标识输入版本。

支持矿石量 Mt/kt/t；黄金品位 g/t、金属量 oz/koz/Moz；铜和明确标注的 Li2O 品位 %、含量 t/kt/Mt。未披露的金属量不会用计算结果替代。Li2O 是氧化锂含量，不是元素锂或碳酸锂当量。

校验包括证据存在、数值词元、单位、分类、日期、重复身份与矿石量×品位质量平衡。质量平衡使用 5% 的保守容差，可能拒绝经过粗粒度四舍五入的真实表格；不会因此改写原值。校验无法独自识别所有跨行串值，应人工检查原文。

## 价格

CSV 列头：

```csv
commodity,date,price,currency,unit,exchange,contract,source_url,synthetic
```

JSON Feed 是同字段对象数组。`commodity` 为 copper/zinc/nickel/lithium，`date` 为 YYYY-MM-DD，`price` 为正数，`currency=USD`，`exchange=LME`。铜锌镍使用 USD/t；锂使用 USD/kg，需接入相符的氢氧化锂合约。`contract` 必须包括实际报价口径及必要到期信息，`source_url` 为 HTTPS 来源。真实模式拒绝 `synthetic=true`。

价格身份为 commodity/date/contract。冲突重复记录拒绝；相同窗口中若存在不同合约、单位或币种，拒绝计算混合走势。get_price 只返回指定日期，get_trend 的 days 是自然日窗口，缺失交易日不填充。趋势为首末实际观测值的百分比变化，至少需要两个观测值。

该适配器是数据接入边界，不等于获得 LME 授权。来源标签由数据供应者提供，接入前需核对其真实性。项目不将 COMEX 铜、现货氢氧化锂、碳酸锂或精矿价格自动标记成 LME 数据。

## 合成数据与公开参考

`src/mining_daily/fixtures/` 的新闻、价格、资源 JSON 和 PDF 都由项目生成。固定日期为 2026-10-14，URL 使用 `demo://`，不能用作行业事实或投资依据。生成脚本保存在 `examples/generate_fixtures.py`。

设计时核对过 [2025-06-11 Pilgangoora Mineral Resource Update 的公开转录](https://www.listcorp.com/asx/pls/pls-group-limited/news/pilgangoora-mineral-resource-update-3200119.html)：其原文明确采用 JORC 2012，并以 2025-03-31 为资源估算日期。此参考支持标准与日期区分；不作为“最新资源量”或今日新闻注入 demo，也未复制整份公告入仓库。

私有 PDF、行情和密钥分别放入忽略的 `data/private/`、`.env` 或外部路径。`runs/` 中的真实内容与调用轨迹同样默认不提交。
