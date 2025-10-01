"""
Simple usage dashboard to monitor OpenAI API consumption
Shows real-time usage tracking for humanitarian operations
"""

import os
import json
from datetime import datetime, timedelta
from openai import OpenAI

class HumanitarianUsageDashboard:
    def __init__(self):
        # Load .env file
        self.load_env_file()

        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found")

        self.client = OpenAI(api_key=self.api_key)

        # Local usage tracking
        self.usage_file = "local_usage_tracking.json"
        self.load_local_usage()

        # Cost per 1K tokens (USD)
        self.token_costs = {
            'gpt-4o': {'input': 0.005, 'output': 0.015},
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002},
            'whisper-1': 0.006  # per minute
        }

    def load_env_file(self):
        """Load .env file"""
        env_path = ".env"
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()

    def load_local_usage(self):
        """Load local usage tracking data"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    self.usage_data = json.load(f)
            else:
                self.usage_data = {
                    'daily_usage': {},
                    'total_requests': 0,
                    'total_cost_estimate': 0.0,
                    'start_date': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"[WARNING] Could not load usage data: {e}")
            self.usage_data = {
                'daily_usage': {},
                'total_requests': 0,
                'total_cost_estimate': 0.0,
                'start_date': datetime.now().isoformat()
            }

    def save_local_usage(self):
        """Save usage data locally"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            print(f"[WARNING] Could not save usage data: {e}")

    def track_request(self, model, input_tokens, output_tokens, cost=None):
        """Track a request locally"""
        today = datetime.now().strftime('%Y-%m-%d')

        if today not in self.usage_data['daily_usage']:
            self.usage_data['daily_usage'][today] = {
                'requests': 0,
                'input_tokens': 0,
                'output_tokens': 0,
                'estimated_cost': 0.0,
                'models_used': {}
            }

        day_data = self.usage_data['daily_usage'][today]
        day_data['requests'] += 1
        day_data['input_tokens'] += input_tokens
        day_data['output_tokens'] += output_tokens

        if model not in day_data['models_used']:
            day_data['models_used'][model] = 0
        day_data['models_used'][model] += 1

        # Calculate cost if not provided
        if cost is None and model in self.token_costs:
            if isinstance(self.token_costs[model], dict):
                cost = (input_tokens/1000 * self.token_costs[model]['input'] +
                       output_tokens/1000 * self.token_costs[model]['output'])
            else:
                cost = self.token_costs[model]  # For whisper (per minute)

        if cost:
            day_data['estimated_cost'] += cost
            self.usage_data['total_cost_estimate'] += cost

        self.usage_data['total_requests'] += 1
        self.save_local_usage()

    def test_with_tracking(self):
        """Test API and track the usage"""
        print("="*60)
        print("API USAGE TEST WITH TRACKING")
        print("="*60)

        try:
            # Test with Arabic humanitarian text
            arabic_text = "الوضع صعب في المخيم"

            print("[TESTING] Making API call with usage tracking...")

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Translate Arabic to English for humanitarian reports."},
                    {"role": "user", "content": f"Translate: {arabic_text}"}
                ],
                max_tokens=50
            )

            # Extract usage info
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            # Track this request
            self.track_request("gpt-3.5-turbo", input_tokens, output_tokens)

            print("[SUCCESS] API call completed and tracked!")
            print(f"Translation: {response.choices[0].message.content}")
            print(f"Tokens used: {total_tokens} (input: {input_tokens}, output: {output_tokens})")

            # Calculate cost
            cost = (input_tokens/1000 * self.token_costs['gpt-3.5-turbo']['input'] +
                   output_tokens/1000 * self.token_costs['gpt-3.5-turbo']['output'])
            print(f"Estimated cost: ${cost:.6f}")

            return True

        except Exception as e:
            print(f"[ERROR] API test failed: {str(e)}")
            return False

    def show_usage_dashboard(self):
        """Display usage dashboard"""
        print("\n" + "="*60)
        print("HUMANITARIAN OPERATIONS USAGE DASHBOARD")
        print("="*60)

        print(f"[OVERVIEW] Total requests tracked: {self.usage_data['total_requests']}")
        print(f"[OVERVIEW] Total estimated cost: ${self.usage_data['total_cost_estimate']:.4f}")

        if 'start_date' in self.usage_data:
            start_date = datetime.fromisoformat(self.usage_data['start_date'].replace('Z', '+00:00') if self.usage_data['start_date'].endswith('Z') else self.usage_data['start_date'])
            days_tracked = (datetime.now() - start_date).days + 1
            avg_cost_per_day = self.usage_data['total_cost_estimate'] / max(days_tracked, 1)
            print(f"[OVERVIEW] Average daily cost: ${avg_cost_per_day:.4f}")

        # Show last 7 days
        print(f"\n[RECENT USAGE] Last 7 days:")
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            if date in self.usage_data['daily_usage']:
                day_data = self.usage_data['daily_usage'][date]
                print(f"  {date}: {day_data['requests']} requests, ${day_data['estimated_cost']:.4f}")
            else:
                print(f"  {date}: No usage")

    def show_cost_projections(self):
        """Show cost projections for different usage scenarios"""
        print("\n" + "="*60)
        print("COST PROJECTIONS FOR HUMANITARIAN OPERATIONS")
        print("="*60)

        # Calculate average cost per request if we have data
        if self.usage_data['total_requests'] > 0:
            avg_cost_per_request = self.usage_data['total_cost_estimate'] / self.usage_data['total_requests']
            print(f"[CURRENT AVERAGE] ${avg_cost_per_request:.6f} per request")
        else:
            avg_cost_per_request = 0.01  # Rough estimate

        scenarios = {
            "Light Operations": 100,    # 100 requests/day
            "Medium Operations": 500,   # 500 requests/day
            "Heavy Operations": 2000,   # 2000 requests/day
            "Crisis Response": 5000     # 5000 requests/day
        }

        print(f"\n[PROJECTIONS] Based on current usage patterns:")
        for scenario, daily_requests in scenarios.items():
            daily_cost = daily_requests * avg_cost_per_request
            monthly_cost = daily_cost * 30
            print(f"  {scenario}: ${daily_cost:.2f}/day (${monthly_cost:.2f}/month)")

    def check_quota_status(self):
        """Check approximate quota status"""
        print("\n" + "="*60)
        print("QUOTA AND LIMITS MONITORING")
        print("="*60)

        # Get today's usage
        today = datetime.now().strftime('%Y-%m-%d')
        today_usage = self.usage_data['daily_usage'].get(today, {'requests': 0, 'estimated_cost': 0.0})

        print(f"[TODAY] Requests made: {today_usage['requests']}")
        print(f"[TODAY] Estimated cost: ${today_usage['estimated_cost']:.4f}")

        # Warnings based on typical limits
        if today_usage['requests'] > 100:
            print("[WARNING] High request volume today - monitor for rate limits")
        if today_usage['estimated_cost'] > 5.0:
            print("[WARNING] Daily cost is high - consider optimizing usage")

        print(f"\n[LIMITS] Common OpenAI limits to watch:")
        print(f"- Free tier: ~200 requests/day")
        print(f"- Paid tier: Much higher, varies by plan")
        print(f"- Rate limits: 3 requests/minute (free) to 3500/minute (paid)")

def main():
    print("Humanitarian Operations - OpenAI Usage Dashboard")
    print("Track and monitor your API consumption for Sudan operations\n")

    try:
        dashboard = HumanitarianUsageDashboard()

        # Test API with tracking
        test_success = dashboard.test_with_tracking()

        if test_success:
            # Show dashboard
            dashboard.show_usage_dashboard()

            # Show projections
            dashboard.show_cost_projections()

            # Check quota status
            dashboard.check_quota_status()

        print("\n" + "="*60)
        print("MONITORING RECOMMENDATIONS")
        print("="*60)
        print("1. Run this script daily to track usage")
        print("2. Check OpenAI dashboard: https://platform.openai.com/usage")
        print("3. Set up usage alerts in your OpenAI account")
        print("4. Monitor costs during crisis response periods")
        print("5. Optimize by using appropriate models for each task")

        print(f"\n[INFO] Usage data saved to: {dashboard.usage_file}")

    except Exception as e:
        print(f"[ERROR] Dashboard failed: {str(e)}")
        print("Make sure your .env file contains OPENAI_API_KEY")

if __name__ == "__main__":
    main()