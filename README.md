# miniClaudeCode-repro

从零复现 [miniClaudeCode](https://github.com/bcefghj/miniClaudeCode)（Claude Code 核心架构的蒸馏版）的学习项目。**当前进度：阶段一 · 地基。**

> 目标是逐步复现一个具备 agent loop + 工具调用 + 权限 + 多轮上下文管理的 mini agent。本仓库按阶段提交，当前仅包含「地基」部分，后续阶段会陆续补齐。

## 当前内容（阶段一）

| 文件 | 作用 |
| --- | --- |
| `miniclaudecode/config.py` | `Config` 数据类：模型、上下文/轮数上限、权限模式与命令白/黑名单等配置 |
| `miniclaudecode/context.py` | `ConversationContext`：消息列表累积、超限截断；`load_project_instructions()` 读取 `CLAUDE.md` |
| `try_single_turn.py` | 最小可运行 demo：搭起 context、发起一次单轮 LLM 调用并打印回复 |

## 运行

直接依赖仅 `anthropic`。推荐用 [uv](https://github.com/astral-sh/uv) 管理环境：

```powershell
uv venv
.\.venv\Scripts\activate
uv pip install anthropic
```

设置认证（**密钥只放环境变量，代码里不硬编码**）：

```powershell
$env:ANTHROPIC_API_KEY = "your-api-key"
# 可选：指向 Anthropic 兼容端点（例如 DeepSeek）
$env:ANTHROPIC_BASE_URL = "https://api.deepseek.com/anthropic"
```

运行单轮 demo：

```powershell
python try_single_turn.py
```

## 说明

- 这是学习用的**逐阶段复现**，不是完整项目；后续阶段会补齐其余模块。
- 复现自上游 [`bcefghj/miniClaudeCode`](https://github.com/bcefghj/miniClaudeCode)，仅用于学习。
