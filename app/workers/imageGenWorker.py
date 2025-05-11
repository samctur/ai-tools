import json
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
import httpx
import openai
import numpy as np
import psycopg2

from fastmcp import Client
from app.utils.rabbitMQConsumer import RabbitMQConsumer

load_dotenv()
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")
API_TO_USE = os.getenv("API_TO_USE", "mock").lower()

QUEUE_NAME = "recipe-image-gen"
ROUTING_KEY = "ai-tools.recipe"
EXCHANGE_NAME = "ai-tools"


async def run_mock(prompt: str) -> str:
    print(f"imageGenWorker generating image with prompt: {prompt}")
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"./output/mock_{timestamp}.webp"
    with open(filename, "wb") as f:
        f.write(b"")
    print(f"Mock image saved as {filename}")
    return filename


async def run_sdxl_via_api(prompt: str) -> str:
    print(f"imageGenWorker generating sdxl image with prompt: {prompt}")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.stability.ai/v2beta/stable-image/generate/core",
                headers={
                    "authorization": f"Bearer {STABILITY_API_KEY}",
                    "Accept": "image/*",
                },
                files={"none": ''},
                data={"prompt": prompt, "output_format": "webp"},
            )
            if response.status_code == 200:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"./output/image_{timestamp}.webp"
                with open(filename, "wb") as file:
                    file.write(response.content)
                return filename
            else:
                print(f"❌ API Error {response.status_code}: {response.text}")
                return None
    except httpx.RequestError as e:
        print(f"❌ HTTPX Error: {e}")
        return None


async def run_openai_dalle_image(prompt: str) -> str:
    print(f"imageGenWorker generating OpenAI image with prompt: {prompt}")
    try:
        response = await openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
            response_format="url"
        )
        image_url = response.data[0].url
        if image_url:
            print(f"✅ OpenAI image URL: {image_url}")
            async with httpx.AsyncClient() as client:
                img_response = await client.get(image_url)
                if img_response.status_code == 200:
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    filename = f"./output/openai_{timestamp}.png"
                    with open(filename, "wb") as f:
                        f.write(img_response.content)
                    return filename
        print("❌ No image URL returned")
        return None
    except Exception as e:
        print(f"❌ OpenAI Error: {e}")
        return None


async def insert_image_metadata_via_mcp(prompt: str, image_url: str, embedding: np.ndarray):
    print(f"imageGenWorker sending metadata to MCP for: {image_url}")
    async with Client("http://mcp-server:8000/mcp/") as client:
        await client.call_tool("store_image_metadata", {
            "prompt": prompt,
            "image_url": image_url,
            "embedding": embedding.tolist()
        })
        print(f"📦 Metadata sent to MCP for: {image_url}")


def insert_image_metadata(prompt: str, image_url: str, embedding: np.ndarray):
    conn = psycopg2.connect(
        host="db",
        port=5432,
        dbname="ai-tools",
        user="postgres",
        password="postgres"
    )
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO images (prompt, image_url, embedding)
            VALUES (%s, %s, %s)
        """, (prompt, image_url, embedding.tolist()))
        conn.commit()
    conn.close()
    print(f"📦 Metadata stored for: {image_url}")


def get_prompt_context(prompt: str, style: str = "realistic") -> str:
    STYLE_PRESETS = {
        "realistic": "highly detailed, 4k, sharp lighting, ",
        "fantasy": "epic fantasy, intricate environments, glowing elements, ",
        "cyberpunk": "cyberpunk cityscape, neon lights, rain, ",
        "surreal": "surrealistic, dreamlike, abstract forms, ",
        "minimalist": "minimalist, clean lines, simple colors, ",
        "retro": "retro style, vintage colors, grainy texture, ",
        "cartoon": "cartoonish, exaggerated features, bright colors, ",
        "abstract": "abstract art, geometric shapes, vibrant colors, ",
        "photorealistic": "photorealistic, ultra-realistic, ",
        "anime": "anime style, vibrant colors, dynamic poses, ",
        "watercolor": "watercolor painting, soft colors, fluid shapes, ",
        "oil_painting": "oil painting, rich textures, deep colors, ",
        "sketch": "sketch style, pencil drawing, rough lines, ",
        "3d_render": "3D render, realistic textures, dynamic lighting, ",
        "impressionist": "impressionist, soft brush strokes, light play, ",
        "gothic": "gothic style, dark colors, intricate details, ",
    }
    return STYLE_PRESETS.get(style, "") + prompt


def message_callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        context = data.get("context", {})
        input_data = data.get("input", {})
        prompt = input_data.get("prompt")

        if not prompt:
            print("❌ No prompt found in message.")
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        contextualized_prompt = get_prompt_context(prompt, style="realistic")

        match API_TO_USE:
            case "sdxl":
                image_path = loop.run_until_complete(run_sdxl_via_api(contextualized_prompt))
            case "openai":
                image_path = loop.run_until_complete(run_openai_dalle_image(contextualized_prompt))
            case _:
                image_path = loop.run_until_complete(run_mock(contextualized_prompt))

        if image_path:
            print(f"✅ Image generated: {image_path}")
            embedding = np.random.rand(768).astype(np.float32)  # Replace with real embedding
            image_url = f"mock://{image_path}"  # Replace with real URL in prod

            # Store metadata in PostgreSQL directly
            #insert_image_metadata(prompt, image_url, embedding)

            # or send to MCP
            loop.run_until_complete(insert_image_metadata_via_mcp(prompt, image_url, embedding))
        else:
            print("❌ Image generation failed")

    except Exception as e:
        print(f"❌ Error processing message: {e}")


def main():
    consumer = RabbitMQConsumer(
        host="rabbitmq",
        queue_name=QUEUE_NAME,
        exchange_name=EXCHANGE_NAME,
        routing_key=ROUTING_KEY,
        retry_delay=2
    )
    consumer.connect()
    print(" [*] imageGenWorker listening for prompts...")
    consumer.start_consuming(message_callback)


if __name__ == "__main__":
    main()
