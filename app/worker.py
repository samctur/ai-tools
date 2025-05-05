# worker.py
import pika
import time
import json
import asyncio
import os
import httpx
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
API_KEY = os.getenv("STABILITY_API_KEY")

async def run_sdxl_via_api(prompt: str) -> str:
    print(f"Worker generating image with prompt: {prompt}")

    # Set to False to disable real API call
    use_api = False

    if use_api:
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

def callback(ch, method, properties, body):
    data = json.loads(body)
    prompt = data.get("prompt")
    if prompt:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_sdxl_via_api(prompt))
        if result:
            print(f"✅ Image generated: {result}")
        else:
            print("❌ Image generation failed")

def wait_for_rabbitmq():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
            print("✅ Connected to RabbitMQ!")
            return connection
        except pika.exceptions.AMQPConnectionError:
            print("❌ RabbitMQ not ready, retrying in 2s...")
            time.sleep(2)

def main():
    connection = wait_for_rabbitmq()
    channel = connection.channel()
    channel.queue_declare(queue="prompts")
    channel.basic_consume(queue="prompts", on_message_callback=callback, auto_ack=True)
    print(" [*] Worker listening for prompts...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
