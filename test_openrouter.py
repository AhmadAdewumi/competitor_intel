# test_openrouter.py
# Test OpenRouter integration

import os
from src.llm.client import LLMClient, LLMProvider

print("=" * 60)
print("Testing OpenRouter")
print("=" * 60)

# Check if API key is set
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("❌ OPENROUTER_API_KEY not found in .env")
    print("   Please add it to your .env file:")
    print("   OPENROUTER_API_KEY=sk-or-v1-...")
    exit(1)

print("✅ OpenRouter API key found")

# Create client
client = LLMClient(provider=LLMProvider.OPENROUTER)
print(f"\n✅ Client initialized with provider: {client.provider}")
print(f"   Default model: {client.default_model}")

# Test 1: Basic chat
print("\n--- Test 1: Basic Chat ---")
try:
    response = client.chat_with_system(
        system_prompt="You are a helpful assistant. Keep responses VERY short (1-2 words).",
        user_prompt="What is 2+2?"
    )
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Longer response
print("\n--- Test 2: Longer Response ---")
try:
    response = client.chat_with_system(
        system_prompt="You are a helpful assistant. Be concise.",
        user_prompt="Explain what an AI agent is in ONE sentence."
    )
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Different model
print("\n--- Test 3: Using different model ---")
try:
    # Try a cheaper model for testing
    response = client.chat_with_system(
        system_prompt="You are a helpful assistant.",
        user_prompt="What is the capital of France?",
        model="meta-llama/llama-3.3-70b-instruct:free"  # Cheaper model
    )
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("OpenRouter test complete!")