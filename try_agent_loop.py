'''Stage-2 runner: exercise the agent loop end-to-end.

Originally drove the loop with a fake get_weather tool to test the skeleton; that fake
tool was removed in stage 3, so this now runs against AgentLoop's default real tool set.
The weather prompt is a leftover -- with no weather tool, the agent just answers from
what it has. Kept as the stage-2 artifact.

Auth via env (DeepSeek's Anthropic-compatible endpoint):
  ANTHROPIC_BASE_URL = https://api.deepseek.com/anthropic
  ANTHROPIC_API_KEY  = <deepseek key>

Run:  python try_agent_loop.py
'''

from dotenv import load_dotenv

from miniclaudecode.config import Config
from miniclaudecode.agent_loop import AgentLoop

load_dotenv()  # load .env so the Anthropic client picks up credentials

cfg = Config()
cfg.model = 'deepseek-chat'

agent = AgentLoop(config=cfg)
final = agent.run('What is the weather in Tokyo right now?')

print('\n\n=== FINAL ANSWER ===')
print(final)
