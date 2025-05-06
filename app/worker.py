# worker.py
import json
import asyncio
import os
import httpx
from dotenv import load_dotenv
from datetime import datetime
from app.utils.rabbitmq import wait_for_rabbitmq
import psycopg2
from psycopg2.extras import execute_values
import numpy as np

load_dotenv()
API_KEY = os.getenv("STABILITY_API_KEY")
USE_STABILITY_API_KEY = os.getenv("USE_STABILITY_API_KEY", "false").lower() == "true"

QUEUE_NAME = "recipe-image-gen"
ROUTING_KEY = "ai-tools.recipe"
EXCHANGE_NAME = "ai-tools"

async def run_sdxl_via_api(prompt: str) -> str:
    print(f"Worker generating image with prompt: {prompt}")

    if USE_STABILITY_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.stability.ai/v2beta/stable-image/generate/core",
                    headers={
                        "authorization": f"Bearer {API_KEY}",
                        "Accept": "image/*",
                    },
                    files={"none": ''},
                    data={
                        "prompt": prompt,
                        "output_format": "webp",
                    },
                )

                if response.status_code == 200:
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    filename = f"./output/image_{timestamp}.webp"
                    with open("./output/output.webp", "wb") as file:
                        file.write(response.content)
                    return file.name
                else:
                    print(f"❌ API Error {response.status_code}: {response.text}")
                    return None
        except httpx.RequestError as e:
            print(f"❌ HTTPX Error: {e}")
            return None
    else:
        # Mock mode: generate placeholder file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"./output/mock_{timestamp}.webp"
        with open(filename, "wb") as f:
            f.write(b"")  # Placeholder for actual image data
        print(f"Mock image saved as {filename}")

        return filename

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

def callback(ch, method, properties, body):
    data = json.loads(body)
    prompt = data.get("prompt")
    if not prompt:
        print("❌ No prompt found in message.")
        return
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    image_path = loop.run_until_complete(run_sdxl_via_api(prompt))

    if image_path:
        print(f"✅ Image generated: {image_path}")

        # TODO: Replace this with actual embedding generation
        embedding = np.random.rand(768).astype(np.float32)  # Mock embedding

        # Store metadata
        image_url = f"mock://{image_path}"  # Replace with real URL in prod
        insert_image_metadata(prompt, image_url, embedding)

    else:
        print("❌ Image generation failed")

def main():
    # Wait for RabbitMQ to be ready
    connection = wait_for_rabbitmq()
    channel = connection.channel()
    # Declare exchange and queue
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic", durable=True)
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    # Bind the queue to the exchange with the routing key
    channel.queue_bind(queue=QUEUE_NAME, exchange=EXCHANGE_NAME, routing_key=ROUTING_KEY)

    print(" [*] Worker listening for image-generation prompts...")
    # Set QoS to limit the number of unacknowledged messages
    channel.basic_qos(prefetch_count=1)
    # Start consuming messages from the queue
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == "__main__":
    main()
