# main.py
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import pika
import json
from contextlib import asynccontextmanager
from app.models import MODEL_MAP
from app.utils.rabbitmq import wait_for_rabbitmq

# Global reference
rabbitmq_channel = None
rabbitmq_connection = None


QUEUE_NAME = "recipe-image-gen"
ROUTING_KEY_PREFIX = "ai-tools"
EXCHANGE_NAME = "ai-tools"

@asynccontextmanager
async def lifespan(app: FastAPI):
    connection = wait_for_rabbitmq()
    channel = connection.channel()
    app.state.rabbitmq_connection = connection
    app.state.rabbitmq_channel = channel
    declare_exchanges()
    print("✅ RabbitMQ connection established.")
    yield
    connection.close()
    print("❌ RabbitMQ connection closed.")

app = FastAPI(lifespan=lifespan)

@app.post("/generate")
async def generate_image(model_type: str, payload: Dict[str, Any], request: Request):
    if model_type not in MODEL_MAP:
        raise HTTPException(status_code=400, detail=f"Unsupported type '{model_type}'")
    model_class = MODEL_MAP[model_type]
    try:
        model_instance = model_class(**payload)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        prompt = create_prompt(model_type, model_instance)
        publish_prompt(prompt, request, model_type)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Message queue unavailable")
    return {"status": "queued"}

def create_prompt(type: str, obj: Any) -> str:
    if type == "recipe":
        return (
            f"A professional food photography shot of {obj.title}, "
            f"made with {', '.join(obj.ingredients)}. "
            "Served in a beautiful setting. High resolution."
        )
    elif type == "profile":
        return (
            f"Portrait of {obj.name}, who enjoys {', '.join(obj.hobbies)}. "
            f"Bio: {obj.bio}"
        )
    else:
        return f"Prompt data: {obj.dict()}"

def declare_exchanges():
    channel = app.state.rabbitmq_channel
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic", durable=True)

def publish_prompt(prompt: str, request: Request, model_type: str):
    channel = request.app.state.rabbitmq_channel
    routing_key = f"{ROUTING_KEY_PREFIX}.{model_type}"
    channel.basic_publish(
        exchange=EXCHANGE_NAME,
        routing_key=routing_key,
        body=json.dumps({"prompt": prompt}),
        properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
    )