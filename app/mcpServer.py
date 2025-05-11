import os
from contextlib import asynccontextmanager
from typing import Dict, Any

import numpy as np
import psycopg2
from fastmcp import FastMCP

from app.utils.rabbitMQPublisher import RabbitMQPublisher
from interfaces.modelTypes import MODEL_TYPES
from interfaces.models import MODEL_MAP, create_prompt

mcp = FastMCP(name="mcp-ai-tools")
publisher = RabbitMQPublisher()

USER_AGENT = "ai-tools/0.1.0"
SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8080")


@mcp.resource("image://{image_id}")
def get_image(image_id: str) -> dict[str, str]:
    """
    Get a previously generated image by ID.
    Args:
        image_id (str): The ID of the image to retrieve.
    Returns:
        str: The URL of the image.
    """
    # For demonstration purposes, we'll just return a mock URL
    return {"image_url": f"{SERVER_URL}/images/{image_id}"}


@mcp.tool()
def store_image_metadata(prompt: str, image_url: str, embedding: list[float]) -> str:
    """Store image generation metadata including prompt, image URL, and vector embedding in the database."""
    conn = None
    print(f"Storing metadata for image: {image_url}")

    try:
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
            """, (prompt, image_url, np.array(embedding, dtype=np.float32).tolist()))
            conn.commit()

        return f"✅ Metadata stored for: {image_url}"

    except Exception as e:
        return f"❌ Error storing metadata: {e}"

    finally:
        if conn:
            conn.close()


@mcp.tool()
def generate_image(model_type: str, dto_model: str, dto_data: Dict[str, Any]) -> dict[str, str]:
    """
    Generate an image based on the provided prompt and model.
    supported models are:
    - "recipe"
    - "profile"
    supported model_types are:
    - "stable-diffusion"
    - "openai-dalle"
    - "mock"

    Args:
        model_type (str): The type of model to use for generation.
        dto_model (str): The dto model to use for generation.
        dto_data (Dict[str, Any]): The data to use for generation.
    Returns:
        str: The URL of the generated image.
    """

    # check if the model_type is supported
    if model_type not in MODEL_TYPES:
        raise ValueError(f"Unsupported type '{model_type}'")
    if dto_model not in MODEL_MAP:
        raise ValueError(f"Unsupported model '{dto_model}'")
    model_class = MODEL_MAP[dto_model]

    try:
        model_instance = model_class(**dto_data)
    except Exception as e:
        raise ValueError(e)

    try:
        prompt = create_prompt(model_type, model_instance)
        publisher.publish(prompt, model_type)
    except RuntimeError:
        raise ValueError("Failed to create and p")
    return {"status": "queued"}


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
