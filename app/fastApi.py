from fastapi import FastAPI, Request, HTTPException
from typing import Dict, Any
from contextlib import asynccontextmanager
from app.interfaces.models import MODEL_MAP, create_prompt
from app.utils.rabbitMQPublisher import RabbitMQPublisher


@asynccontextmanager
async def lifespan(fast_app: FastAPI):
    publisher.connect()
    fast_app.state.publisher = publisher  # type: ignore[attr-defined]
    print("✅ RabbitMQ connection established.")
    yield
    publisher.close()
    print("❌ RabbitMQ connection closed.")


app = FastAPI(lifespan=lifespan)
publisher = RabbitMQPublisher()


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
        request.app.state.publisher.publish(prompt, model_type)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Message queue unavailable")
    return {"status": "queued"}
