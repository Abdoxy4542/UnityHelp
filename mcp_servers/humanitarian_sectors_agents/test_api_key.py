"""
Quick test to verify OpenAI API key is working
"""

import os
from openai import OpenAI

def test_api_key():
    """Test if OpenAI API key is configured and working"""

    print("="*60)
    print("OPENAI API KEY TEST")
    print("="*60)

    # Check if API key is set
    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        print("❌ FAILED: OPENAI_API_KEY environment variable not found")
        print("\nTo fix this:")
        print("1. Create .env file with: OPENAI_API_KEY=your_key_here")
        print("2. Or set environment variable: export OPENAI_API_KEY=your_key_here")
        return False

    print(f"✓ API Key found: {api_key[:7]}...{api_key[-4:]} (masked for security)")

    # Test API connection
    try:
        print("\n🔄 Testing API connection...")

        client = OpenAI(api_key=api_key)

        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'API test successful' if you can read this."}
            ],
            max_tokens=10
        )

        print("✅ SUCCESS: API connection working!")
        print(f"Response: {response.choices[0].message.content}")
        print(f"Model used: {response.model}")
        print(f"Tokens used: {response.usage.total_tokens}")

        return True

    except Exception as e:
        print(f"❌ FAILED: API test failed")
        print(f"Error: {str(e)}")

        # Provide specific error guidance
        error_str = str(e).lower()
        if "invalid api key" in error_str or "unauthorized" in error_str:
            print("\n🔧 Fix: Your API key is invalid")
            print("- Check if you copied the full key correctly")
            print("- Make sure the key starts with 'sk-'")
            print("- Verify the key is active in OpenAI dashboard")

        elif "insufficient quota" in error_str or "billing" in error_str:
            print("\n🔧 Fix: Billing/quota issue")
            print("- Add payment method to OpenAI account")
            print("- Check your usage limits")
            print("- Verify you have remaining credits")

        elif "rate limit" in error_str:
            print("\n🔧 Fix: Rate limit reached")
            print("- Wait a moment and try again")
            print("- Consider upgrading your OpenAI plan")

        else:
            print("\n🔧 Check:")
            print("- Internet connection")
            print("- OpenAI service status")
            print("- Firewall settings")

        return False

def test_sudan_specific():
    """Test with Sudan-specific humanitarian content"""

    print("\n" + "="*60)
    print("SUDAN HUMANITARIAN CONTEXT TEST")
    print("="*60)

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Skipping - API key not configured")
        return False

    try:
        client = OpenAI(api_key=api_key)

        # Test with Arabic content
        arabic_text = "الوضع في مخيم النيالة صعب جداً. نحتاج مياه وغذاء عاجل."

        print("🔄 Testing Arabic text processing...")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a humanitarian AI assistant for Sudan. Analyze Arabic field reports and respond in English with key findings."
                },
                {
                    "role": "user",
                    "content": f"Analyze this field report from Sudan: {arabic_text}"
                }
            ],
            max_tokens=150
        )

        print("✅ SUCCESS: Arabic processing working!")
        print(f"Analysis: {response.choices[0].message.content}")
        print(f"Tokens used: {response.usage.total_tokens}")

        return True

    except Exception as e:
        print(f"❌ FAILED: Sudan context test failed")
        print(f"Error: {str(e)}")
        return False

def test_whisper_capability():
    """Test if Whisper API is available"""

    print("\n" + "="*60)
    print("WHISPER API CAPABILITY TEST")
    print("="*60)

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Skipping - API key not configured")
        return False

    try:
        client = OpenAI(api_key=api_key)

        # Check if we can access models list
        models = client.models.list()

        whisper_available = any("whisper" in model.id for model in models.data)
        gpt4_available = any("gpt-4" in model.id for model in models.data)
        vision_available = any("vision" in model.id for model in models.data)

        print(f"✓ Whisper API: {'Available' if whisper_available else 'Not available'}")
        print(f"✓ GPT-4 models: {'Available' if gpt4_available else 'Not available'}")
        print(f"✓ Vision models: {'Available' if vision_available else 'Not available'}")

        if whisper_available and gpt4_available:
            print("✅ All required models available for multimodal processing!")
            return True
        else:
            print("⚠️  Some models may not be available - check your OpenAI plan")
            return False

    except Exception as e:
        print(f"❌ Model check failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 OpenAI API Key Testing Tool")
    print("This will test your API key configuration and capabilities\n")

    # Run all tests
    results = []

    results.append(("Basic API Connection", test_api_key()))
    results.append(("Sudan Humanitarian Context", test_sudan_specific()))
    results.append(("Model Availability", test_whisper_capability()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 SUCCESS: Your OpenAI API is ready for humanitarian operations!")
        print("You can now use the full multimodal system.")
    elif passed > 0:
        print("⚠️  PARTIAL: Basic functionality works, some features may be limited")
    else:
        print("❌ SETUP NEEDED: Please configure your OpenAI API key")
        print("\nNext steps:")
        print("1. Get API key from: https://platform.openai.com/api-keys")
        print("2. Set environment variable: OPENAI_API_KEY=your_key_here")
        print("3. Run this test again")