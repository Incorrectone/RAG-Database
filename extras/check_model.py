import google.generativeai as genai
import os

# Ensure your API key is set in your environment variables,
# or replace os.environ.get(...) with your actual key in quotes.
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

print("🔍 Checking API Key Access...\n")

print("--- Available Embedding Models ---")
for m in genai.list_models():
    if 'embedContent' in m.supported_generation_methods:
        print(f"- {m.name}")

print("\n--- Available Generative Models (LLMs) ---")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"- {m.name}")