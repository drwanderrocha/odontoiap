import os
os.environ['LLM_API_KEY'] = os.getenv('OPENROUTER_API_KEY', '')
os.environ['COGNEE_SKIP_CONNECTION_TEST'] = 'true'

import cognee
import asyncio

async def test():
    # Don't call serve() - just use local embedded mode
    await cognee.remember('Test biomechanical rule for intrusion', dataset_name='test_dataset')
    results = await cognee.recall('biomechanical rule', datasets=['test_dataset'])
    print('Results:', results)
    await cognee.disconnect()

asyncio.run(test())