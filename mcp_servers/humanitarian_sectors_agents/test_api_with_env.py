"""
OpenAI API key test with .env file support
"""

import os
from openai import OpenAI

def load_env_file():
    """Load environment variables from .env file"""
    env_path = ".env"
    if os.path.exists(env_path):
        print(f"[FOUND] Loading .env file from: {env_path}")
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
                    print(f"[LOADED] {key.strip()}")
        return True
    else:
        print("[NOT FOUND] .env file not found")
        return False

def test_api_key():
    print("="*60)
    print("OPENAI API KEY TEST WITH .ENV SUPPORT")
    print("="*60)

    # Try to load .env file first
    load_env_file()

    # Check if API key is set
    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        print("[FAIL] OPENAI_API_KEY not found")
        return False

    print(f"[FOUND] API Key: {api_key[:7]}...{api_key[-4:]} (masked)")

    # Test API connection
    try:
        print("\n[TESTING] API connection...")

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'API test successful for Sudan humanitarian system'"}
            ],
            max_tokens=20
        )

        print("[SUCCESS] API connection working!")
        print(f"Response: {response.choices[0].message.content}")
        print(f"Model: {response.model}")
        print(f"Tokens used: {response.usage.total_tokens}")
        return True

    except Exception as e:
        print(f"[FAIL] API test failed: {str(e)}")

        error_str = str(e).lower()
        if "invalid api key" in error_str or "unauthorized" in error_str:
            print("Fix: Your API key may be invalid or expired")
        elif "quota" in error_str or "billing" in error_str:
            print("Fix: Add payment method to your OpenAI account")
        elif "rate limit" in error_str:
            print("Fix: Rate limit reached, wait and try again")
        else:
            print("Fix: Check internet connection and OpenAI service status")

        return False

def test_sudan_functionality():
    """Test Sudan-specific humanitarian functionality"""
    print("\n" + "="*60)
    print("SUDAN HUMANITARIAN FUNCTIONALITY TEST")
    print("="*60)

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("[SKIP] API key not configured")
        return False

    try:
        client = OpenAI(api_key=api_key)

        # Test with Arabic humanitarian content
        arabic_text = "الوضع في مخيم النيالة صعب جداً. نحتاج مياه وغذاء عاجل."

        print("[TESTING] Arabic humanitarian text processing...")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a humanitarian AI for Sudan. Analyze Arabic field reports and respond in English."
                },
                {
                    "role": "user",
                    "content": f"Analyze this Sudan field report: {arabic_text}"
                }
            ],
            max_tokens=100
        )

        print("[SUCCESS] Arabic processing working!")
        print(f"Analysis: {response.choices[0].message.content}")
        print(f"Tokens used: {response.usage.total_tokens}")

        return True

    except Exception as e:
        error_str = str(e).lower()
        if "model" in error_str and "not found" in error_str:
            print("[WARNING] GPT-4o not available, trying GPT-3.5-turbo...")
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": f"Translate and analyze: {arabic_text}"}
                    ],
                    max_tokens=100
                )
                print("[SUCCESS] Arabic processing with GPT-3.5-turbo!")
                print(f"Analysis: {response.choices[0].message.content}")
                return True
            except:
                print(f"[FAIL] Arabic processing failed: {str(e)}")
                return False
        else:
            print(f"[FAIL] Arabic processing failed: {str(e)}")
            return False

def test_cost_estimation():
    """Test and show cost estimation"""
    print("\n" + "="*60)
    print("COST ESTIMATION")
    print("="*60)

    # Simple cost calculation based on test usage
    test_tokens = 50  # Approximate tokens used in tests

    costs = {
        "gpt-3.5-turbo": test_tokens / 1000 * 0.002,  # $0.002 per 1K tokens
        "gpt-4o": test_tokens / 1000 * 0.030,        # $0.030 per 1K tokens
        "whisper-1": 0.006                           # $0.006 per minute
    }

    print("[ESTIMATE] API costs for this test:")
    for model, cost in costs.items():
        print(f"  {model}: ${cost:.6f}")

    print(f"\n[MONTHLY] Estimated costs for active humanitarian operations:")
    print(f"  Light usage (1K requests/month): $50-100")
    print(f"  Medium usage (10K requests/month): $200-500")
    print(f"  Heavy usage (50K requests/month): $500-1000")

if __name__ == "__main__":
    print("Sudan Humanitarian AI System - OpenAI API Test")
    print("Testing your configuration...")

    # Run all tests
    basic_test = test_api_key()
    sudan_test = test_sudan_functionality() if basic_test else False

    # Show cost info
    test_cost_estimation()

    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)

    if basic_test and sudan_test:
        print("[READY] Your OpenAI API is fully ready!")
        print("- Basic API: Working")
        print("- Arabic processing: Working")
        print("- Sudan humanitarian context: Working")
        print("\nYou can now use the complete multimodal system!")

    elif basic_test:
        print("[PARTIAL] Basic API working, some limitations")
        print("- Basic API: Working")
        print("- Advanced models: May be limited")
        print("\nBasic functionality available.")

    else:
        print("[FAILED] API configuration issues")
        print("Please check:")
        print("1. API key is correct")
        print("2. Payment method added to OpenAI account")
        print("3. Internet connection working")

    print(f"\nNext steps:")
    if basic_test:
        print("- Run the full humanitarian system demos")
        print("- Test with real Sudan field data")
        print("- Monitor usage and costs")
    else:
        print("- Fix API configuration issues")
        print("- Add payment method to OpenAI account")
        print("- Try the test again")