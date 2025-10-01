"""
OpenAI API Usage Tracker for Sudan Humanitarian Platform
Track usage, costs, and remaining credits for your humanitarian operations
"""

import os
import requests
from datetime import datetime, timedelta
import json

class OpenAIUsageTracker:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # Current OpenAI pricing (as of 2024)
        self.pricing = {
            'gpt-4o': {
                'input': 0.005,   # per 1K tokens
                'output': 0.015   # per 1K tokens
            },
            'gpt-4-turbo': {
                'input': 0.01,
                'output': 0.03
            },
            'gpt-3.5-turbo': {
                'input': 0.001,
                'output': 0.002
            },
            'whisper-1': 0.006,  # per minute
            'gpt-4-vision-preview': {
                'input': 0.01,
                'output': 0.03
            }
        }

    def load_env_file(self):
        """Load environment variables from .env file"""
        env_path = ".env"
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            return True
        return False

    def get_usage_data(self, days_back=30):
        """Get usage data from OpenAI API"""
        print("="*60)
        print("OPENAI API USAGE TRACKER")
        print("="*60)

        # Load .env if exists
        self.load_env_file()

        try:
            # Get current date and past date
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            print(f"[INFO] Checking usage from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

            # OpenAI doesn't have a direct usage API, but we can check billing
            url = "https://api.openai.com/v1/usage"
            params = {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            }

            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                usage_data = response.json()
                return usage_data
            else:
                print(f"[WARNING] Usage API returned status {response.status_code}")
                print(f"Response: {response.text}")
                return None

        except Exception as e:
            print(f"[ERROR] Failed to get usage data: {str(e)}")
            return None

    def check_account_info(self):
        """Check account information and limits"""
        try:
            # Try to get account information
            url = "https://api.openai.com/v1/models"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                models = response.json()
                available_models = [model['id'] for model in models['data']]

                print("[SUCCESS] API Key is active and working")
                print(f"[INFO] {len(available_models)} models available")

                # Check for key models we need
                key_models = {
                    'gpt-4o': 'Emergency processing',
                    'gpt-4': 'Standard processing',
                    'gpt-3.5-turbo': 'Bulk processing',
                    'whisper-1': 'Voice transcription'
                }

                print("\n[MODELS] Available models for humanitarian operations:")
                for model, purpose in key_models.items():
                    if any(model in available for available in available_models):
                        print(f"  [AVAILABLE] {model} - {purpose}")
                    else:
                        print(f"  [MISSING] {model} - {purpose}")

                return True

            elif response.status_code == 401:
                print("[ERROR] Invalid API key - Please check your OPENAI_API_KEY")
                return False
            elif response.status_code == 429:
                print("[ERROR] Rate limit exceeded or quota reached")
                return False
            else:
                print(f"[ERROR] API returned status {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"[ERROR] Failed to check account info: {str(e)}")
            return False

    def estimate_costs(self, usage_data=None):
        """Estimate costs for humanitarian operations"""
        print("\n" + "="*60)
        print("COST ESTIMATION FOR HUMANITARIAN OPERATIONS")
        print("="*60)

        # Sample usage scenarios for Sudan humanitarian platform
        scenarios = {
            "Daily Light Usage": {
                "text_requests": 100,      # 100 assessment reports per day
                "voice_minutes": 30,       # 30 minutes of voice data
                "image_requests": 20,      # 20 situation photos
                "description": "Small NGO or single site monitoring"
            },
            "Daily Medium Usage": {
                "text_requests": 500,      # 500 reports per day
                "voice_minutes": 120,      # 2 hours of voice data
                "image_requests": 100,     # 100 situation photos
                "description": "Medium NGO or multiple sites"
            },
            "Daily Heavy Usage": {
                "text_requests": 2000,     # 2000 reports per day
                "voice_minutes": 300,      # 5 hours of voice data
                "image_requests": 500,     # 500 situation photos
                "description": "Large operation or crisis response"
            }
        }

        print("[ESTIMATES] Daily cost projections:")
        for scenario_name, scenario in scenarios.items():

            # Estimate tokens (roughly 4 chars = 1 token for Arabic)
            avg_tokens_per_request = 200  # Conservative estimate for reports

            text_cost = (scenario["text_requests"] * avg_tokens_per_request / 1000) * self.pricing['gpt-4o']['input']
            voice_cost = scenario["voice_minutes"] * self.pricing['whisper-1']
            image_cost = (scenario["image_requests"] * 100 / 1000) * self.pricing['gpt-4-vision-preview']['input']

            daily_cost = text_cost + voice_cost + image_cost
            monthly_cost = daily_cost * 30

            print(f"\n  {scenario_name}:")
            print(f"    {scenario['description']}")
            print(f"    Text processing: ${text_cost:.3f}/day")
            print(f"    Voice processing: ${voice_cost:.3f}/day")
            print(f"    Image analysis: ${image_cost:.3f}/day")
            print(f"    TOTAL: ${daily_cost:.2f}/day (${monthly_cost:.2f}/month)")

    def monitor_usage_realtime(self):
        """Monitor usage in real-time during operations"""
        print("\n" + "="*60)
        print("REAL-TIME USAGE MONITORING")
        print("="*60)

        print("[INFO] To monitor usage in real-time:")
        print("1. Visit OpenAI Dashboard: https://platform.openai.com/usage")
        print("2. Check current usage and billing")
        print("3. Set up usage alerts in OpenAI dashboard")

        print("\n[RECOMMENDATIONS] For Sudan humanitarian operations:")
        print("- Set daily usage alerts at $10, $25, $50")
        print("- Monitor during crisis periods when usage spikes")
        print("- Use GPT-3.5-turbo for bulk processing to reduce costs")
        print("- Implement caching for repeated queries")

        # Simple usage tracking file
        usage_log = {
            "date": datetime.now().isoformat(),
            "api_key_status": "active",
            "last_check": datetime.now().isoformat(),
            "recommendations": [
                "Monitor daily usage during crisis response",
                "Use tiered model approach to optimize costs",
                "Cache frequent translations and analyses"
            ]
        }

        try:
            with open("api_usage_log.json", "w") as f:
                json.dump(usage_log, f, indent=2)
            print("\n[SAVED] Usage log saved to api_usage_log.json")
        except Exception as e:
            print(f"[WARNING] Could not save usage log: {str(e)}")

    def check_rate_limits(self):
        """Check current rate limits"""
        print("\n" + "="*60)
        print("RATE LIMITS AND QUOTAS")
        print("="*60)

        print("[INFO] OpenAI Rate Limits (Free Tier):")
        print("- GPT-3.5-turbo: 3 requests/minute, 200 requests/day")
        print("- GPT-4: Limited requests per day based on usage tier")
        print("- Whisper: 50 requests/day")

        print("\n[INFO] OpenAI Rate Limits (Paid Tier):")
        print("- GPT-3.5-turbo: 3,500 requests/minute")
        print("- GPT-4: Higher limits based on usage tier")
        print("- Whisper: Higher limits based on usage tier")

        print("\n[HUMANITARIAN NEEDS] For crisis response:")
        print("- Consider upgrading to paid tier for higher limits")
        print("- Implement request queuing for high-volume periods")
        print("- Use async processing to handle multiple requests")

def main():
    print("OpenAI Usage Tracker for Sudan Humanitarian Platform")
    print("This tool helps monitor your API usage and costs\n")

    try:
        tracker = OpenAIUsageTracker()

        # Check account status
        account_ok = tracker.check_account_info()

        if account_ok:
            # Get usage data
            usage_data = tracker.get_usage_data()

            # Show cost estimates
            tracker.estimate_costs(usage_data)

            # Show monitoring info
            tracker.monitor_usage_realtime()

            # Show rate limits
            tracker.check_rate_limits()

        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        print("1. Visit OpenAI Dashboard: https://platform.openai.com/usage")
        print("2. Check your current usage and billing")
        print("3. Set up usage alerts")
        print("4. Consider upgrading for humanitarian operations")
        print("5. Run this script regularly to monitor usage")

    except Exception as e:
        print(f"[ERROR] Failed to initialize tracker: {str(e)}")
        print("Make sure OPENAI_API_KEY is set in your .env file")

if __name__ == "__main__":
    main()