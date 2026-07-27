import os
os.environ['LLM_API_KEY'] = open('/opt/data/.env').read().split('OPENROUTER_API_KEY=')[1].split('\n')[0].strip()
os.environ['COGNEE_SKIP_CONNECTION_TEST'] = 'true'
# Don't set LLM_PROVIDER - let it default to 'openai' which works with OpenRouter

from cognee.infrastructure.llm.config import get_llm_context_config
from cognee.infrastructure.llm.structured_output_framework.litellm_instructor.llm.get_llm_client import get_llm_client

config = get_llm_context_config()
print('Config:', config.llm_api_key[:20], config.llm_provider)

# Test the client
client = get_llm_client()
print('Client:', client)