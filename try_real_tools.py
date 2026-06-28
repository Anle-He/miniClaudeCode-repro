'''Stage-3 runner: drive the agent loop with the REAL tool set (bash / read_file / write_file).

Auth via env (DeepSeek's Anthropic-compatible endpoint):
  ANTHROPIC_BASE_URL = https://api.deepseek.com/anthropic
  ANTHROPIC_API_KEY  = <deepseek key>

Run:  python try_real_tools.py

Note: the permission deny-list is NOT wired into the loop yet (stage 4), so bash runs
unguarded. The task below only writes/reads one local temp file -- keep test tasks harmless.
'''

from miniclaudecode.config import Config
from miniclaudecode.agent_loop import AgentLoop

cfg = Config()
cfg.model = 'deepseek-chat'

# AgentLoop falls back to ToolRegistry.default() (now the real tools) when registry is omitted.
agent = AgentLoop(config=cfg)

# Stage-3 quiz check: a task that should drive the agent to call the new list_dir tool.
task = 'List the entries (files and folders) in the current directory.'
final = agent.run(task)

print('\n\n=== FINAL ANSWER ===')
print(final)
