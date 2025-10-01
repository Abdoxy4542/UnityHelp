"""
Simple OpenAI API key test without Unicode characters
"""

import os
from openai import OpenAI

def test_api_key():
    print("="*60)
    print("OPENAI API KEY TEST")
    print("="*60)

    # Check if API key is set
    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        print("[FAIL] OPENAI_API_KEY environment variable not found")
        print("\nTo fix this:")
        print("1. Create .env file with: OPENAI_API_KEY=your_key_here")
        print("2. Or set environment variable: set OPENAI_API_KEY=your_key_here")
        return False

    print(f"[FOUND] API Key: {api_key[:7]}...{api_key[-4:]} (masked)")

    # Test API connection
    try:
        print("\n[TESTING] API connection...")

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'API test successful'"}
            ],
            max_tokens=10
        )

        print("[SUCCESS] API connection working!")
        print(f"Response: {response.choices[0].message.content}")
        print(f"Tokens used: {response.usage.total_tokens}")
        return True

    except Exception as e:
        print(f"[FAIL] API test failed: {str(e)}")

        error_str = str(e).lower()
        if "invalid api key" in error_str:
            print("Fix: Check if your API key is correct")
        elif "quota" in error_str:
            print("Fix: Add payment method to OpenAI account")
        elif "rate limit" in error_str:
            print("Fix: Wait a moment and try again")

        return False

def test_models_available():
    print("\n" + "="*60)
    print("MODEL AVAILABILITY TEST")
    print("="*60)

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("[SKIP] API key not configured")
        return False

    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()

        available_models = [model.id for model in models.data]

        required_models = {
            "gpt-4o": "Emergency processing",
            "gpt-4-turbo": "Standard processing",
            "gpt-3.5-turbo": "Bulk processing",
            "whisper-1": "Voice transcription",
            "gpt-4-vision-preview": "Image analysis"
        }

        print("[CHECKING] Required models:")
        all_available = True

        for model, purpose in required_models.items():
            if any(model in available for available in available_models):
                print(f"[AVAILABLE] {model} - {purpose}")
            else:
                print(f"[MISSING] {model} - {purpose}")
                all_available = False

        if all_available:
            print("[SUCCESS] All required models available!")
        else:
            print("[WARNING] Some models missing - check OpenAI plan")

        return all_available

    except Exception as e:
        print(f"[FAIL] Model check failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("OpenAI API Key Testing Tool")
    print("Testing your API configuration...")

    # Run tests
    api_test = test_api_key()
    models_test = test_models_available()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    if api_test:
        print("[SUCCESS] API key working")
    else:
        print("[FAIL] API key issues")

    if models_test:
        print("[SUCCESS] All models available")
    else:
        print("[WARNING] Some model limitations")

    if api_test and models_test:
        print("\n[READY] Your OpenAI setup is ready for humanitarian operations!")
    elif api_test:
        print("\n[PARTIAL] Basic functionality works, some features limited")
    else:
        print("\n[SETUP NEEDED] Configure OPENAI_API_KEY first")
        print("Get key from: https://platform.openai.com/api-keys")