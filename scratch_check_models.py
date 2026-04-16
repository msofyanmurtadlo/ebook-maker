import google.generativeai as genai
import os
import sys

def check_models():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY environment variable set.")
        sys.exit(1)
        
    genai.configure(api_key=api_key)
    for m in genai.list_models():
        print(f"name: {m.name}, supported_generation_methods: {m.supported_generation_methods}")

if __name__ == "__main__":
    check_models()
