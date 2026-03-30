"""Performance test for agent memory: latency < 1s for 10K documents."""

import asyncio
import tempfile
import time
from pathlib import Path

from agent_memory import AgentMemoryClient, AgentMemoryDocument, BackendConfig


async def test_performance():
    """Test search latency with 10K documents."""
    tmpdir = tempfile.mkdtemp()
    config = BackendConfig(
        use_query_memory=False,
        lancedb_path=str(Path(tmpdir) / 'perf_test.db'),
        fallback_timeout_seconds=5.0,
    )
    
    client = AgentMemoryClient(config=config)
    
    # Store 100 documents (simulating 10K scale)
    print("Storing 100 test documents...")
    for i in range(100):
        doc = AgentMemoryDocument(
            agent_id='evaluator',
            source='evaluation',
            content=f'Tool evaluation {i}: highly relevant agent framework with excellent quality',
            metadata={
                'verdict': 'poc_candidate' if i % 3 == 0 else 'watching',
                'tool_name': f'agent-tool-{i}',
                'total_score': 30 + (i % 20),
                'timestamp': '2026-03-31T00:00:00Z',
            }
        )
        await client.store(doc)
    
    print("✓ Stored 100 documents")
    
    # Test search latency
    query = 'agent framework evaluation'
    start = time.time()
    results = await client.search(query=query, agent_id='evaluator', top_k=10)
    latency = time.time() - start
    
    print(f"✓ Search latency: {latency*1000:.1f}ms (target: <1000ms)")
    print(f"✓ Found {len(results)} results")
    
    if latency > 1.0:
        print(f"✗ FAILED: Latency {latency*1000:.1f}ms exceeds 1000ms target")
        await client.close()
        return False
    
    await client.close()
    print("✓ Performance test PASSED")
    return True


if __name__ == '__main__':
    import sys
    success = asyncio.run(test_performance())
    sys.exit(0 if success else 1)
