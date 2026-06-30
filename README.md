# miniClaudeCode-repro

从零复现 [miniClaudeCode](https://github.com/bcefghj/miniClaudeCode)（Claude Code 核心架构的蒸馏版）的学习项目。**当前进度：阶段五 · system_prompt + CLI 收口（整机可在终端运行）。**

> 目标是逐步复现一个具备 agent loop + 工具调用 + 权限 + 多轮上下文管理的 mini agent。本仓库按阶段提交，五个学习阶段已全部落地（地基 → 主循环 → 工具系统 → 权限 → prompt/CLI 收口），现可经 `cli.py` 在终端整机运行。

## 核心循环

整个仓库复现的就是这一个循环：

```
                 User prompt
                      |
                      v
       +------------------------------+ <--------------------+
       |     ConversationContext      |                      |
       |     (messages 累积 / 截断)     |  tool_result /       |
       +---------------+--------------+  deny 回灌            |
                       | 全量 messages                       |
                       v                                     |
                   +-------+                                 |
                   |  LLM  |                                 |
                   +---+---+                                 |
                       |                                     |
                  tool_use ?                                 |
                    /       \                                |
                 no          yes                             |
                  |           |                              |
                  v           v                              |
           +-----------+  +----------------+                 |
           |  reply to |  | PermissionGate |                 |
           |    User   |  | ASK/AUTO/PLAN  |                 |
           +-----------+  +-------+--------+                 |
                          allow   | deny --------------------+
                                  v                          |
                            +-----------+                    |
                            |   Tool    | bash/read/write/   |
                            |  execute  | list/append        |
                            +-----+-----+                    |
                                  | tool_result              |
                                  +--------------------------+
                                       loop continues
```

`ConversationContext` 是循环的中枢：用户输入、assistant 的 `tool_use`、工具回来的 `tool_result` 全累积在它的 messages 里，每轮把全量 messages 喂给 LLM——它是模型唯一的运行时通道（超 `max_context` 时截断早期消息）。

驱动循环往下转的是模型吐出的 `tool_use`。模型某轮**不再请求工具、只回纯文本**时，循环跳出、那段文本即最终答复返回 User；只要还有 `tool_use`，就先过 `PermissionGate`（工具自检 + ASK/AUTO/PLAN 模式）：放行则执行工具、把 `tool_result` 回灌 Context 进入下一轮，拒绝则不执行、把 deny 结果回灌让模型改道。`max_turns` 给单条用户输入内部的循环轮数封顶，兜底防止反复调工具转不停。

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
| `miniclaudecode/permissions.py` | stage-2 时为 stub 占位，**已在阶段四实现为真实两层权限**（见阶段四） |
| `miniclaudecode/system_prompt.py` | stage-2 时为 stub 占位，**已在阶段五实现为真实 prompt 构造**（见阶段五） |
| `try_agent_loop.py` | stage-2 runner：原用假 `WeatherTool` 跑通循环骨架，阶段三起已改用真实工具系统（保留为阶段二产物） |

> `permissions.py` / `system_prompt.py` 在阶段二仅为可 import 的最小 stub，现已分别在阶段四 / 阶段五替换为真实现——已无 stub 残留。

**阶段三 · 工具系统**

| 文件 | 作用 |
| --- | --- |
| `miniclaudecode/tools/base.py` | `Tool`(ABC) 工具合同 + `ToolResult` + `ToolRegistry`（注册 / 按名分发 / `api_schemas` / `default()`） |
| `miniclaudecode/tools/bash_tool.py` | `BashTool`：`subprocess` 跑 shell 命令 + deny-list 自检（`check_permissions`，已于阶段四接入 PermissionGate） |
| `miniclaudecode/tools/file_read.py` | `FileReadTool`：读文件为带行号文本，可选行范围 + 大小/类型 guard |
| `miniclaudecode/tools/file_write.py` | `FileWriteTool`：写文件、按需建父目录 |
| `miniclaudecode/tools/list_dir.py` | `ListDirTool`：列目录条目（目录优先排序）——阶段三自定义工具示例 |
| `try_real_tools.py` | 用真工具集驱动循环的 runner（让 agent 调 `list_dir` / 读写文件） |

**阶段四 · 权限系统**

| 文件 | 作用 |
| --- | --- |
| `miniclaudecode/permissions.py` | `PermissionGate`：执行前的两层权限闸门。layer-1 工具自检（`tool.check_permissions`，模式无关、最先短路）；layer-2 操作模式 ASK / AUTO / PLAN。`check()` 返回 `None` 放行 / `ToolResult(is_error)` 拒绝——拒绝走回灌不抛异常，模型可据此改道 |
| `miniclaudecode/agent_loop.py` | `_execute_tool_calls` 在 `execute()` 前接入 `gate.check`，被拒则跳过执行并把 deny 结果回灌（校验点本阶段生效） |
| `try_permissions.py` | 权限 runner：只打 `gate.check`、零副作用、无需 API key，打印「工具 × 三模式」判定矩阵 |

**阶段五 · system_prompt + CLI 收口**

| 文件 | 作用 |
| --- | --- |
| `miniclaudecode/system_prompt.py` | `build_system_prompt`：把 5 块拼成 system prompt——身份/规则模板 + 动态工具清单（`registry.all_tools()`）+ 当前权限模式说明 + 可选 `CLAUDE.md` |
| `miniclaudecode/cli.py` | 终端入口：one-shot（带 prompt 参数跑一轮）/ 交互式 REPL（无参数）/ 斜杠命令（`/tools`、`/mode`、`/help`、`/quit`）；`/mode` 热切换权限模式并即时联动 PermissionGate |

至此五个学习阶段全部完成，`cli.py` 把 context / loop / tools / permissions / prompt 串成可在终端整机运行的 mini agent。

**终测 · 跨阶段综合**

| 文件 | 作用 |
| --- | --- |
| `miniclaudecode/tools/append_file.py` | `AppendFileTool`：往文件尾部追加文本（不覆盖，`mode 'a'` + UTF-8）。跨阶段综合产物——新增工具 → `default()` 注册 → 加入 `PermissionGate` 的 `write_tools`（PLAN 下被拦）→ 由 agent 在两步任务中调起，验证整条链路。 |

## 运行

依赖为 `anthropic` 与 `python-dotenv`。推荐用 [uv](https://github.com/astral-sh/uv) 管理环境，一条命令按 `pyproject.toml` / `uv.lock` 装齐：

```powershell
uv sync
```

设置认证（**密钥只放 `.env`，不进 git、代码里不硬编码**）。复制示例文件并填入真实值：

```powershell
copy .env-example .env
# 然后编辑 .env：
#   ANTHROPIC_API_KEY=your-api-key
#   可选，指向 Anthropic 兼容端点（例如 DeepSeek）：
#   ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
```

CLI 启动时会自动 `load_dotenv()` 加载 `.env`，无需手动 export。`.env` 已被 `.gitignore` 忽略。

交互式 CLI（自动加载 `.env`）：

```powershell
uv run python -m miniclaudecode.cli
```

运行单轮 demo（阶段一）：

```powershell
uv run python try_single_turn.py
```

运行 agent loop demo（阶段二，现跑真实工具集）：

```powershell
uv run python try_agent_loop.py
```

运行真工具 demo（阶段三，bash / read / write / list_dir）：

```powershell
uv run python try_real_tools.py
```

运行权限矩阵（阶段四，无需 API key）：

```powershell
python try_permissions.py
```

整机运行（阶段五，终端入口 `cli.py`）：

```powershell
# one-shot：跑一轮即退
python -m miniclaudecode.cli --model <模型> "列出当前目录，并读 README.md 的前几行"
# 交互式 REPL：不带 prompt，多轮对话；REPL 内 /mode plan 可切只读模式
python -m miniclaudecode.cli --model <模型>
```

## 说明

- 这是学习用的**逐阶段复现**，不是完整项目；五个学习阶段的模块均已落地。
- 复现自上游 [`bcefghj/miniClaudeCode`](https://github.com/bcefghj/miniClaudeCode)，仅用于学习。
