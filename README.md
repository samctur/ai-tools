# Ai Support Tools

Fast API client receives POST requests. Piblishes  request to RabbitMQ.  Wroker consumes prompt and handles image generation. Logging server logs all messages and results are stored in postgres with embedings. Workers use MCP Server to communicate internally and externally.

Dockerized for ease of use with 2 workers by default.

## Dependency Setup

Skip to step 3 if you are using Docker.

### Remote Setup with api.stability.ai
1. Create and activate virtual environment
```
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

2. Install dependencies
```
pip install -r requirements.txt
```

3. Setup api keys
```
cp .env.mock .env
```

4. Fill in the .env file with your API keys from stability.ai
https://platform.stability.ai/account/keys

### Optional: For local generation (Not yet supported)
```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install diffusers transformers accelerate safetensors
```

## Start Servers
```
docker-compose up --build
```

## Cleanup Server
```
docker-compose down --volumes --remove-orphans
```

## FastApi Curl Test
```
curl -X POST "http://localhost:8000/generate?model_type=recipe" \
  -H "Content-Type: application/json" \
  -d '{
        "title": "Vegan Pancakes",
        "ingredients": ["flour", "almond milk", "banana"],
        "steps": ["Mix ingredients", "Cook on skillet", "Serve hot"]
      }'
```

## MCPServer Curl Test
```
curl -X POST http://localhost:8080/mcp/ \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"action":"list_tools"}'
```
