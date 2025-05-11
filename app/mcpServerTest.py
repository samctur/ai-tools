import asyncio

import pytest
import numpy as np
from fastmcp import Client

MCP_URL = "http://localhost:8080/mcp/"
TIMEOUT = 10

@pytest.mark.asyncio
async def test_ping():
    try:
        await asyncio.wait_for(actual_ping(), timeout=TIMEOUT)
    except asyncio.TimeoutError:
        pytest.fail("MCP ping timed out")


async def actual_ping():
    async with Client("http://localhost:8080/mcp/") as client:
        pong = await client.ping()
        assert pong is not None


@pytest.mark.asyncio
async def test_store_image_metadata():
    try:
        await asyncio.wait_for(_run_post_image(), timeout=TIMEOUT)
    except asyncio.TimeoutError:
        pytest.fail("❌ Tool call timed out")


async def _run_post_image():
    prompt = "test prompt"
    image_url = "http://example.com/image.png"
    embedding = np.array([0.1] * 768, dtype=np.float32)

    async with Client(MCP_URL) as client:
        result = await client.call_tool("store_image_metadata", {
            "prompt": prompt,
            "image_url": image_url,
            "embedding": embedding.tolist()
        })

        assert isinstance(result, list), f"Expected list, got {type(result)}"
        texts = [r.text for r in result if hasattr(r, "text")]
        assert any("✅" in t or "stored" in t.lower() for t in texts), f"Expected success message in response, got: {texts}"


@pytest.mark.asyncio
async def test_list_tools():
    async with Client(MCP_URL) as client:
        tools = await client.list_tools()
        tool_names = [t.name for t in tools]

        print("✅ Available tools:", tool_names)
        assert isinstance(tools, list)
        assert len(tools) > 0, "No tools returned from MCP server"
        assert "store_image_metadata" in tool_names, "Expected tool not found"
        assert "generate_image" in tool_names, "Expected tool not found"