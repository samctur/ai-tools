import asyncio
import numpy as np
from fastmcp import Client

async def ping_test():
    try:
        async with Client("http://localhost:8080/mcp/") as client:
            pong = await client.ping()
            print("✅ Ping successful:", pong)
    except Exception as e:
        print("❌ Client error:", e)


async def post_image_test(prompt: str, image_url: str, embedding: np.ndarray):
    async with Client("http://localhost:8080/mcp/") as client:
        result = await client.call_tool("store_image_metadata", {
            "prompt": prompt,
            "image_url": image_url,
            "embedding": embedding.tolist()
        })
        print("✅ Tool response:", result)


if __name__ == "__main__":
    print("Starting mcpClient tests...")
    asyncio.run(ping_test())
    asyncio.run(post_image_test("test prompt", "http://example.com/image.png", np.array([0.1] * 768, dtype=np.float32)))
