# 矿权日报 MCP Agent

题目 2：三个独立 MCP Server 与一个编排客户端，将项目新闻、资源报告和价格观测组合成有引用的 Markdown 日报。

```bash
docker compose run --build --rm agent
```

生成 `runs/brief.md` 和 `runs/brief.json`。默认是**离线演示**：真实 MCP 协议、真实 PDF 解析、合成新闻／资源／价格，以及明确标注的 PDF 模型响应回放。无需账号或 API Key；不将演示数字冒充市场数据。

也可使用 Python 3.11+：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
mining-daily brief '给我生成一份关于 Pilbara 锂矿的今日简报'
```

完整说明见 [RUN.md](RUN.md)，实现边界见 [架构与取舍](docs/architecture.md)。

## 题目要求对应

| 要求 | 实现 |
|---|---|
| mining-news-mcp | `search(query, days)`、`fetch_article(url)` |
| mineral-pdf-mcp | `extract_resources(pdf_url)`，物理页码、原文证据、单位校验 |
| lme-price-mcp | `get_price(commodity, date)`、`get_trend(commodity, days)` |
| Agent 编排 | 自定义有界状态机；实际 MCP initialize、list_tools、call_tool |
| Markdown 简报与引用 | 新闻摘录、资源量、价格走势、风险与来源；JSON 保存完整调用轨迹 |
| Claude Desktop / Cursor | `mcp-config.json`；命令可生成本机绝对路径配置 |
| 5 分钟运行 | 默认离线演示；Docker Compose 和 Python 两种入口 |

## 数据可信度

- Resources 不等于 Reserves；保留 NI 43-101 / JORC、报告日期、分类与原始单位。
- 每个资源数字有原文和物理页码；不通过证据／单位／质量平衡校验的数值不进入日报。
- 新闻使用可追溯摘录；RSS 无结果不等于没有新闻，不伪装为全网搜索。
- 价格不跨合约合并、不补造缺失日期；锂合约报价不等于锂辉石精矿价格。
- 真实模式不会回退到演示数据；失败会显示不可用或部分结果。

## 模式与外部条件

| 能力 | 演示模式 | 真实模式 |
|---|---|---|
| 新闻 | 固定合成条目 | 配置的公开 RSS + 正文抓取 |
| PDF | 生成的两页 PDF + 固定模型响应 + 校验 | HTTPS PDF + 可配置 JSON Chat 模型 + 校验 |
| 价格 | 明确标注的合成价格 | 有来源和合约信息的 LME CSV / HTTPS JSON 数据源 |
| 报告 | 真实 MCP 调用后生成 | 同一条编排路径，保留缺口 |

真实行情需要使用者提供合法可用的数据源。项目没有声称已获得 LME 授权，也没有把其他交易所或第三方商品现货报价自动当成 LME 行情。真实 PDF 模型需要 API Key；密钥不得提交到仓库。

## 检查

```bash
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
uv run mining-daily doctor
```

测试覆盖证据缺失、错误单位、价格日期与合约、RSS 时间范围、输入 URL 防护、失败降级，以及三个 MCP 子进程的端到端协议调用。实际执行结果见 [验证记录](docs/verification.md)。

## 目录

```text
src/mining_daily/
  servers/             # 三个独立 MCP 入口
  client.py            # 协议会话、工具发现、调用和超时
  agent.py             # 固定任务计划与有界编排
  news.py              # RSS 检索及正文提取
  resources.py         # PDF 下载、模型抽取与证据校验
  prices.py            # 可替换行情数据适配器
  report.py            # 引用、风险与 Markdown 输出
  fixtures/            # 可重建的合成数据，不含 HR 文件
tests/                 # 单元测试、故障用例、MCP 集成测试
examples/              # 已生成的演示简报及 fixture 生成器
docs/                  # 架构、数据说明、验证、AI 使用记录
```

限制：自然语言入口内置 Pilbara/Pilgangoora 识别，其他项目使用显式参数；不支持扫描 PDF OCR，不证明矿权法律状态；单元校验无法单独证明跨行表格语义正确，真实输出需要人工抽查。PDF 的候选页选择与上下文大小也有明确上限。
