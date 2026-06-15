import anthropic

from miniclaudecode.config import Config
from miniclaudecode.context import ConversationContext


client = anthropic.Anthropic()

cfg = Config()
# Use DeepSeek via its Anthropic-compatible endpoint.
# Auth/endpoint come from env: ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic, ANTHROPIC_API_KEY=<deepseek key>
cfg.model = 'deepseek-chat'
ctx = ConversationContext(config=cfg)

ctx.set_system_prompt('You are a concise assistant.')
ctx.add_user_message('Introduce yourself.')

resp = client.messages.create(
    model=cfg.model,
    max_tokens=512,
    system=ctx.system_prompt,
    messages=ctx.get_api_messages(),
)

print(resp.content[0].text)
ctx.add_assistant_message(resp.content[0].text)
