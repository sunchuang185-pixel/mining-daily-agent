# 运行与验收

默认演示无需模型 Key 和真实行情账号。首次安装依赖需要网络；安装后 demo 数据处理完全离线。首次镜像下载时间取决于网络，不能保证慢网环境也在 5 分钟内完成。

## 一条 Docker Compose 命令

安装 Docker Engine / Docker Desktop 与 Compose v2 后，在仓库根目录执行：

```bash
docker compose run --build --rm agent
```

查看 `runs/brief.md` 和 `runs/brief.json`。默认查询为“给我生成一份关于 Pilbara 锂矿的今日简报”。演示固定在 **2026-10-14**；文件首部明确标注数据是合成样例。

## 不使用 Docker

推荐 Python 3.12；支持 Python 3.11+。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
mining-daily doctor
mining-daily brief '给我生成一份关于 Pilbara 锂矿的今日简报'
```

Windows 使用 `.venv\Scripts\activate`。若安装了 uv，使用 `uv sync --locked` 后执行 `uv run mining-daily brief` 可以严格复现锁定依赖。

`doctor` 应发现：

```json
{
  "mining-news-mcp": ["fetch_article", "search"],
  "mineral-pdf-mcp": ["extract_resources"],
  "lme-price-mcp": ["get_price", "get_trend"]
}
```

默认日报完成 6 次 MCP 工具调用：新闻检索、两次正文获取、PDF 抽取、指定日期报价、价格走势。JSON 中保留每次请求参数、状态、来源和耗时。

## Claude Desktop 或 Cursor

有 Docker 时先执行 `docker compose build`。根目录的 `mcp-config.json` 使用固定本地镜像名 `mining-daily-agent:local`，没有用户绝对路径，构建后可直接合并到客户端的 `mcpServers` 配置。每个 Server 启动一个独立容器，通过 stdio 通信。

没有 Docker 时，在安装项目的虚拟环境中运行：

```bash
mining-daily mcp-config --output runs/mcp-config.local.json
```

它会生成当前 Python 解释器的绝对路径。将生成文件的 `mcpServers` 内容合并到 Claude Desktop 配置，或写入项目 `.cursor/mcp.json`，重启或重新加载 MCP。不要把本机路径版配置提交到仓库。

客户端可验证以下工具调用：

```json
{"name": "search", "arguments": {"query": "Pilbara", "days": 7}}
{"name": "fetch_article", "arguments": {"url": "demo://news/operations"}}
{"name": "extract_resources", "arguments": {"pdf_url": "demo://pilbara-resources.pdf"}}
{"name": "get_price", "arguments": {"commodity": "lithium", "date": "2026-10-14"}}
{"name": "get_trend", "arguments": {"commodity": "lithium", "days": 7}}
```

## 真实数据模式

三个数据源互相独立；缺一个不会用演示数据顶替。需要：

1. 可访问的新闻 RSS，默认 MINING.COM；可用 `NEWS_RSS_URLS` 配置最多 5 个逗号分隔的公开 HTTPS Feed。
2. 可下载的资源报告 PDF URL，以及支持 JSON Chat 响应的模型配置。
3. 合法可用且附带来源、合约、单位和日期的 LME 数据文件或 JSON Feed。

在终端设置自己的环境变量（不要将真实 Key 写入 Git）：

```bash
export EXTRACTOR_BASE_URL='https://api.openai.com/v1'
export EXTRACTOR_MODEL='gpt-4o'
export EXTRACTOR_API_KEY='填写自己的 Key'
export LME_PRICE_CSV='/绝对路径/authorized-lme-prices.csv'

mining-daily brief '给我生成一份关于 Pilbara 锂矿的今日简报' \
  --mode live \
  --pdf-url 'https://你的公开来源/technical-report.pdf' \
  --output runs/live-brief.md
```

这里的 PDF URL 是明确标注的配置占位符。项目没有预设未经验证的 PDF 下载地址。没有 `--pdf-url` 时，客户端尝试使用获取到的新闻正文中的第一个 PDF 链接；只有匹配日报项目且通过验证的资源记录才会展示。

CSV 格式见 [DATA_NOTES.md](DATA_NOTES.md)。也可设置 `LME_PRICE_JSON_URL`，其返回值为相同字段的 JSON 数组。提供者需在接入前核实 exchange 和 contract 标签的真实性；程序无法凭标签证明行情授权或真实性。

Docker 真实模式：复制 `.env.example` 为 `.env` 并设置字段，把私有行情文件放入 `data/private/`，容器内路径使用 `/app/data/private/文件名.csv`，然后运行：

```bash
docker compose run --rm agent brief \
  '给我生成一份关于 Pilbara 锂矿的今日简报' \
  --mode live --pdf-url 'https://你的公开来源/technical-report.pdf'
```

其他项目需指定范围，不让系统猜矿山：

```bash
mining-daily brief '生成铜矿日报' --mode live \
  --project '明确的项目名' --commodity copper --days 7 \
  --pdf-url 'https://你的公开来源/report.pdf'
```

`--as-of YYYY-MM-DD` 可以回放指定日期的窗口。真实模式默认 Asia/Shanghai 的当日日期；RSS 只能覆盖 Feed 实际保留的条目，不保证历史覆盖。

## 常见结果

| 状态 | 含义 | 操作 |
|---|---|---|
| ok | 工具产出符合自身约束的结果 | 根据来源抽查，尤其是 PDF 表格语义 |
| partial | 数据不完整或校验未通过 | 查看 warnings；不合格资源数值会被隐藏 |
| unavailable | 来源、模型配置或指定日期数据不可用 | 补充来源或配置后复跑 |
| error | MCP 工具异常、输入错误或协议调用失败 | 查看轨迹，修正后重试 |

正文抓取不绕过登录墙；扫描 PDF 不自动 OCR；文件超过 50 MiB、1000 页或候选证据超过 180,000 字符时会停止处理并说明原因。

## 开发验证

```bash
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
uv build
```

本仓库 CI 不需要模型 Key。默认测试不访问真实新闻、模型或收费数据源。合成 fixture 可通过 `uv run python examples/generate_fixtures.py` 重建。
