-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the table
CREATE TABLE IF NOT EXISTS images (
                                      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                      prompt TEXT NOT NULL,
                                      image_url TEXT NOT NULL,
                                      embedding VECTOR(768),  -- Adjust to your model's output dimension
                                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);