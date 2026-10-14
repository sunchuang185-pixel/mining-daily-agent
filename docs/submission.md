# 提交与面试演示

## 提交信息

您好，我选择完成第 2 题“矿权日报 MCP Agent”。仓库包含 3 个独立 MCP Server、1 个编排客户端、Markdown 日报与来源引用，以及 Claude Desktop / Cursor 配置。

默认演示使用明确标注的合成数据，无需 API Key，通过一条 Docker Compose 命令运行；真实模式支持 RSS、公开 PDF 和带来源及合约信息的 LME 数据接入。运行、验证结果和已知限制分别见 RUN.md、docs/verification.md 和 docs/architecture.md。

提交时附仓库地址及实际 commit SHA。私有仓库需要先让评审账号获得访问权限；只发私有 URL 不会自动授权。

## 5 分钟演示顺序

1. 打开 README 的题目要求对应表。
2. 执行 `mining-daily doctor`，展示真实发现的 3 个 Server 和 5 个工具。
3. 执行默认 brief 命令，查看 Markdown 与 JSON 调用轨迹。
4. 指定 `--as-of 2026-10-10`，展示当日缺失报价不会被前一日替代。
5. 解释 JORC 与 NI 43-101、Resources 与 Reserves、氢氧化锂与精矿报价的区别。
6. 展示测试与已知限制，说明真实模型及授权行情的接入方式。

## 推荐讨论的问题

- 为什么这里使用固定状态机，哪些需求出现后才值得引入动态规划？
- 如何证明调用走了 MCP 协议，而不是直接调用 Python 函数？
- 哪些字段由模型产生，哪些由确定性规则计算，哪些无法自动保证？
- 新闻和行情不可用时，如何生成有用但不误导的部分日报？
- 真实部署如何增加 OCR、来源授权、出口隔离与缓存？
