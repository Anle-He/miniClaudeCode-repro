# miniClaudeCode-repro

从零复现 [miniClaudeCode](https://github.com/bcefghj/miniClaudeCode)（Claude Code 核心架构的蒸馏版）的学习项目。**当前进度：阶段三 · 工具系统。**

> 目标是逐步复现一个具备 agent loop + 工具调用 + 权限 + 多轮上下文管理的 mini agent。本仓库按阶段提交，当前已含「地基 + 主循环 + 工具系统」，后续阶段（权限、prompt + CLI）会陆续补齐。

## 当前内容

**阶段一 · 地基**

| 文件 | 作用 |
| --- | --- |
| `miniclaudecode/config.py` | `Config` 数据类：模型、上下文/轮数上限、权限模式与命令白/黑名单等配置 |
| `miniclaudecode/context.py` | `ConversationContext`：消息列表累积、超限截断；`load_project_instructions()` 读取 `CLAUDE.md` |
| `try_single_turn.py` | 最小可运行 demo：搭起 context、发起一次单轮 LLM 调用并打印回复 |

**阶段二 · agent loop 主循环**

| 文件 | 作用 |
| --- | --- |
| `miniclaudecode/agent_loop.py` | `AgentLoop`：由 tool_use 驱动、`max_turns` 封顶的内层循环；assistant(tool_use) 先入列再回灌 tool_result，多结果批成一条 user 消息（遵 API 交替/配对） |
| `miniclaudecode/permissions.py` | **stub**：`PermissionGate.check` 永远放行（真实两层权限留待后续阶段） |
| `miniclaudecode/system_prompt.py` | **stub**：`build_system_prompt` 返回固定串（真实 prompt 构造留待后续阶段） |
| `try_agent_loop.py` | 用假工具把循环骨架跑通的 stage-2 runner（其依赖的假 `WeatherTool` 已在阶段三换成真实工具系统） |

> 仍标 **stub** 的 `permissions.py` / `system_prompt.py` 是让主循环能 import / 跑通的最小占位，后续阶段（权限、prompt + CLI）会替换成真实现。

**阶段三 · 工具系统**

| 文件 | 作用 |
| --- | --- |
| `miniclaudecode/tools/base.py` | `Tool`(ABC) 工具合同 + `ToolResult` + `ToolRegistry`（注册 / 按名分发 / `api_schemas` / `default()`） |
| `miniclaudecode/tools/bash_tool.py` | `BashTool`：`subprocess` 跑 shell 命令 + deny-list 自检（`check_permissions`，接线待阶段四） |
| `miniclaudecode/tools/file_read.py` | `FileReadTool`：读文件为带行号文本，可选行范围 + 大小/类型 guard |
| `miniclaudecode/tools/file_write.py` | `FileWriteTool`：写文件、按需建父目录 |
| `miniclaudecode/tools/list_dir.py` | `ListDirTool`：列目录条目（目录优先排序）——阶段三自定义工具示例 |
| `try_real_tools.py` | 用真工具集驱动循环的 runner（让 agent 调 `list_dir` / 读写文件） |

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

运行单轮 demo（阶段一）：

```powershell
python try_single_turn.py
```

运行 agent loop demo（阶段二，假工具 `get_weather`）：

```powershell
python try_agent_loop.py
```

运行真工具 demo（阶段三，bash / read / write / list_dir）：

```powershell
python try_real_tools.py
```

## 说明

- 这是学习用的**逐阶段复现**，不是完整项目；后续阶段会补齐其余模块。
- 复现自上游 [`bcefghj/miniClaudeCode`](https://github.com/bcefghj/miniClaudeCode)，仅用于学习。
