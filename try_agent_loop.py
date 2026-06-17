'''Stage-2 runner: drive the agent loop with one fake tool (get_weather).

Expects auth in env (DeepSeek via its Anthropic-compatible endpoint):
  ANTHROPIC_BASE_URL = https://api.deepseek.com/anthropic
  ANTHROPIC_API_KEY  = <deepseek key>

Run:  python try_agent_loop.py
'''

from miniclaudecode.config import Config
from miniclaudecode.agent_loop import AgentLoop

cfg = Config()
cfg.model = 'deepseek-chat'

agent = AgentLoop(config=cfg)
final = agent.run('What is the weather in Tokyo right now?')

print('\n\n=== FINAL ANSWER ===')
print(final)
