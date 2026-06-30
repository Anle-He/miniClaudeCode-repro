'''Stage-3 runner: drive the agent loop with the REAL tool set (bash / read_file / write_file / list_dir).

Auth via env (DeepSeek's Anthropic-compatible endpoint):
  ANTHROPIC_BASE_URL = https://api.deepseek.com/anthropic
  ANTHROPIC_API_KEY  = <deepseek key>

Run:  python try_real_tools.py

Note: as of stage 4 the PermissionGate IS wired into the loop; the default mode is ASK, so
safe commands pass and an unsafe bash command prompts for confirmation. Keep test tasks harmless.
'''

from dotenv import load_dotenv

from miniclaudecode.config import Config
from miniclaudecode.agent_loop import AgentLoop

load_dotenv()  # load .env so the Anthropic client picks up credentials

cfg = Config()
cfg.model = 'deepseek-chat'

# AgentLoop falls back to ToolRegistry.default() (now the real tools) when registry is omitted.
agent = AgentLoop(config=cfg)

# Stage-3 quiz check: a task that should drive the agent to call the new list_dir tool.
task = 'List the entries (files and folders) in the current directory.'
final = agent.run(task)

print('\n\n=== FINAL ANSWER ===')
print(final)
