# main.py
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import pika
import json
from contextlib import asynccontextmanager
from app.models import MODEL_MAP

# Global reference
rabbitmq_channel = None
rabbitmq_connection = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()
    channel.queue_declare(queue="prompts")
    app.state.rabbitmq_connection = connection
    app.state.rabbitmq_channel = channel
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
        publish_prompt(prompt, request)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Message queue unavailable")
    return {"status": "queued"}

def create_prompt(type: str, obj: Any) -> str:
    elif type == "profile":
        return (
            f"Portrait of {obj.name}, who enjoys {', '.join(obj.hobbies)}. "
            f"Bio: {obj.bio}"
        )
    else:
        return f"Prompt data: {obj.dict()}"

def publish_prompt(prompt: str, request: Request):
    channel = request.app.state.rabbitmq_channel
    channel.basic_publish(
        exchange="",
        routing_key="prompts",
        body=json.dumps({"prompt": prompt})
    )
