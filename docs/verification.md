# 验证记录

验证日期：2026-10-14（Asia/Shanghai）。本机环境：macOS arm64、Python 3.12.14。以下区分实际执行结果与尚未完成的外部验证。

| 检查 | 实际结果 |
|---|---|
| `uv sync --locked` | 成功建立独立环境并安装锁定依赖 |
| `ruff check .` | 通过 |
| `ruff format --check .` | 35 个 Python 文件格式通过 |
| `mypy` | 19 个源文件通过严格类型检查 |
| `pytest` | **50 passed**；中文样例更新后重新通过 |
| 源码／wheel 构建 | 成功生成 sdist 与 wheel |
| 干净环境 wheel 安装 | 安装后从仓库外运行默认简报成功，fixture 已包含在安装包 |
| 真实 MCP 协议 | 3 个独立子进程、5 个工具发现，默认简报 6 次成功调用 |
| 标准演示输出 | `examples/demo-brief.md` 与同名 JSON |
| 缺失日期演示 | `examples/missing-date-brief.md`；不把前一日价格当成指定日报价 |
| PDF fixture | 中文字体已嵌入；两页均已渲染检查，原文引用、物理页码、文件哈希验证通过 |
| live 模式降级 | MINING.COM Feed 返回 HTTP 403；无 PDF／行情配置时生成明确缺口，不填入 demo 数据 |

PyMuPDF 在当前 Python 版本下有 5 条 SWIG 类型相关 DeprecationWarning；没有测试失败。此处的 50 个测试并不代表在 50 份真实矿业报告上验证了准确率。

## 覆盖的失败情形

测试包含：错误数值、错页、分类互换、储量混淆、单位缩放、重复身份、NaN、空白 PDF、上下文超限、实时模式误用 fixture、缺失交易日、单点趋势、混合合约、冲突行情、未来价格、RSS 日期窗口与上海时区、跟踪参数去重、不同文章 query 保留、私网 URL、无效模型 JSON、429 有限重试、密钥不进入错误文本、非目标项目资源隐藏、HTML 转义、MCP 错误后继续调用等。

## 尚未通过本机实际验证的部分

- **真实模型 PDF 抽取**：未配置模型 Key；模型适配器完成 mock HTTP 契约与错误处理测试。
- **真实 LME 行情正确性**：未提供授权行情；CSV 路径以测试数据验证，不能视为真实市场接入证明。
- **真实报告精度**：没有 HR 提供的报告；本次是题目 2，不将题目 3 的 ground truth 验收混入结果。
- **Docker 本机运行**：当前机器未安装 Docker。仓库 CI 包含 Docker 构建和默认演示，实际结果以 GitHub Actions 为准。
- **Claude Desktop / Cursor UI**：配置已生成；协议层通过实际子进程测试，未操作这两个客户端完成 UI 验证。

## 复现

```bash
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
uv build
uv run mining-daily brief --output runs/brief.md
uv run mining-daily brief --as-of 2026-10-10 --output runs/missing-date.md
```

测试默认离线；成功路径、日期缺失和供应商失败均有独立结果。CI 不需要任何 API Key，上传的 CI artifact 只含演示数据。
