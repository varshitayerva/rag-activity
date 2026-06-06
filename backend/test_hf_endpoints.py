#!/usr/bin/env python3
"""
Test HF Inference Providers endpoints
Run this to verify both embeddings and generation work
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN", "")
if not HF_TOKEN:
    print("ERROR: HF_TOKEN not set in .env")
    sys.exit(1)

print(f"HF_TOKEN found: {HF_TOKEN[:20]}...")

# Test 1: Embeddings using InferenceClient
print("\n" + "="*60)
print("TEST 1: Embeddings (HF InferenceClient)")
print("="*60)

try:
    from huggingface_hub import InferenceClient

    client = InferenceClient(
        model="sentence-transformers/all-MiniLM-L6-v2",
        token=HF_TOKEN
    )

    embedding = client.feature_extraction("This is a test text for embeddings")

    if isinstance(embedding, list):
        if len(embedding) > 0 and isinstance(embedding[0], list):
            embedding = embedding[0]

    print("SUCCESS: Embeddings working!")
    print(f"   - Embedding dimension: {len(embedding)}")
    print(f"   - First 5 values: {embedding[:5]}")

except Exception as e:
    print(f"ERROR: Embeddings failed: {e}")

# Test 2: Generation (DeepSeek via HF Router)
print("\n" + "="*60)
print("TEST 2: Generation Endpoint (DeepSeek)")
print("="*60)

try:
    from openai import OpenAI

    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=HF_TOKEN,
    )

    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V4-Pro:novita",
        messages=[
            {"role": "user", "content": "What is the capital of France? Answer in one word."}
        ],
        max_tokens=20,
        temperature=0.7,
    )

    answer = response.choices[0].message.content
    print("SUCCESS: Generation working!")
    print(f"   - Model: deepseek-ai/DeepSeek-V4-Pro:novita")
    print(f"   - Response: {answer}")

except Exception as e:
    print(f"ERROR: Generation failed: {e}")

# Test 3: Full embeddings batch
print("\n" + "="*60)
print("TEST 3: Batch Embeddings")
print("="*60)

try:
    from huggingface_hub import InferenceClient

    client = InferenceClient(
        model="sentence-transformers/all-MiniLM-L6-v2",
        token=HF_TOKEN
    )

    texts = [
        "First test document",
        "Second test document",
        "Third test document"
    ]

    embeddings = []
    for text in texts:
        embedding = client.feature_extraction(text)

        if isinstance(embedding, list):
            if len(embedding) > 0 and isinstance(embedding[0], list):
                embeddings.append(embedding[0])
            else:
                embeddings.append(embedding)

    print("SUCCESS: Batch embeddings working!")
    print(f"   - Texts processed: {len(embeddings)}")
    print(f"   - Embedding dimension: {len(embeddings[0])}")

except Exception as e:
    print(f"ERROR: Batch embeddings failed: {e}")

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print("""
If all tests passed:
SUCCESS: HF Inference Providers are working
SUCCESS: You can now upload documents and chat
SUCCESS: System is ready for production

Next steps:
1. Restart backend: python -m uvicorn app.main:app --host 127.0.0.1 --port 8081
2. Start frontend: npm run dev
3. Go to http://localhost:3000
4. Upload a document
5. Ask questions and chat!
""")
