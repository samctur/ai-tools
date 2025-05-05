# Ai Support Tools

## Architecture Overview
Client
↓ POST /generate
FastAPI App (Publisher)
→ sends prompt to RabbitMQ queue
↓
RabbitMQ
↓
Worker (Consumer)
→ calls Stability API and handles image generation


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

## Docker Setup
```
# Build the image
docker build -t image-api .

# Run the container
docker run -d -p 8000:8000 --name api image-api

# Run container for local development
docker-compose up --build

# Clean up
docker-compose down --volumes --remove-orphans
```

## Start Server
### With Docker
```
docker-compose up --build
```

### without Docker
```
uvicorn app.main:app --reload
```

## Curl Test
```
curl -X POST "http://localhost:8000/generate?model_type=profile" \
  -H "Content-Type: application/json" \
  -d '{
        "title": "Vegan Pancakes",
        "ingredients": ["flour", "almond milk", "banana"],
        "steps": ["Mix ingredients", "Cook on skillet", "Serve hot"]
      }'
```
