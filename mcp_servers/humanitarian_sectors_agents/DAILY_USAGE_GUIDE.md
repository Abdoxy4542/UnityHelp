# 🎯 How to Run Daily OpenAI Usage Monitoring

## ✅ WORKING SOLUTION

The issue was that you need to use the **virtual environment Python** that has the OpenAI package installed.

### **Method 1: Quick Daily Check (Recommended)**

**Double-click:** `run_with_venv.bat`

This will:
- Use the correct Python from your virtual environment
- Run the usage monitoring
- Show your current usage data
- Display cost projections

### **Method 2: Command Line (Manual)**

```bash
cd "C:\Users\Lenovo\Desktop\unityaid_platform\mcp_servers\humanitarian_sectors_agents"

# Use the virtual environment Python directly:
"C:\Users\Lenovo\Desktop\unityaid_platform\venv\Scripts\python.exe" usage_dashboard.py
```

### **Method 3: Activate Virtual Environment First**

```bash
cd "C:\Users\Lenovo\Desktop\unityaid_platform"

# Activate virtual environment (Windows)
venv\Scripts\activate

# Navigate to scripts folder
cd mcp_servers\humanitarian_sectors_agents

# Run the dashboard
python usage_dashboard.py
```

## 📊 Your Current Usage (Working!)

I just tested it and your system is working perfectly:

```
============================================================
HUMANITARIAN OPERATIONS USAGE DASHBOARD
============================================================
[OVERVIEW] Total requests tracked: 2
[OVERVIEW] Total estimated cost: $0.0001
[OVERVIEW] Average daily cost: $0.0001

[RECENT USAGE] Last 7 days:
  2025-09-24: 2 requests, $0.0001

[CURRENT AVERAGE] $0.000049 per request

[PROJECTIONS] Based on current usage patterns:
  Light Operations: $0.00/day ($0.15/month)
  Medium Operations: $0.02/day ($0.73/month)
  Heavy Operations: $0.10/day ($2.94/month)
  Crisis Response: $0.24/day ($7.35/month)
```

## ✅ Your Usage Data File (`local_usage_tracking.json`)

```json
{
  "daily_usage": {
    "2025-09-24": {
      "requests": 2,               ← 2 successful API calls today
      "input_tokens": 66,          ← Total input tokens used
      "output_tokens": 16,         ← Total output tokens received
      "estimated_cost": 0.000098,  ← Cost: $0.0001 (very cheap!)
      "models_used": {
        "gpt-3.5-turbo": 2         ← Used efficient model
      }
    }
  },
  "total_requests": 2,
  "total_cost_estimate": 0.000098
}
```

**This shows your Arabic processing is working perfectly and very cost-effective!**

## 🚀 Set Up Daily Automation

### Option A: Windows Task Scheduler

1. **Right-click** `schedule_daily_monitor.ps1`
2. Select **"Run with PowerShell"**
3. Choose time (9 AM recommended)
4. It will use `run_with_venv.bat` automatically

### Option B: Create Desktop Shortcut

1. **Right-click** `run_with_venv.bat`
2. Select **"Create shortcut"**
3. **Move shortcut to Desktop**
4. **Double-click daily** to check usage

### Option C: Set Daily Reminder

Set a phone/computer reminder to run:
**Double-click `run_with_venv.bat`** every morning at 9 AM

## 🔍 What You'll See Daily

```
================================================
Sudan Humanitarian AI - Usage Monitor (with venv)
================================================
[SUCCESS] Virtual environment Python found
[INFO] Running usage monitoring...

API USAGE TEST WITH TRACKING
Translation: The situation is difficult in the camp.
Tokens used: 41 (input: 33, output: 8)
Estimated cost: $0.000049

USAGE DASHBOARD
Total requests tracked: X
Total estimated cost: $X.XXXX
Average daily cost: $X.XXXX

RECENT USAGE Last 7 days:
  2025-09-24: X requests, $X.XXXX

COST PROJECTIONS
Light Operations: $X.XX/day ($X.XX/month)
Medium Operations: $X.XX/day ($X.XX/month)
Heavy Operations: $X.XX/day ($X.XX/month)
```

## 📈 Understanding Your Costs

Based on your current usage:

**Per Request Cost:** $0.000049
- This is **extremely cost-effective** for humanitarian operations
- Arabic text processing working perfectly
- Much cheaper than manual translation

**Monthly Projections:**
- **100 requests/day:** ~$0.15/month
- **500 requests/day:** ~$0.73/month
- **2000 requests/day:** ~$2.94/month

**Your humanitarian operations are very affordable!**

## 🎯 Daily Monitoring Routine

### Every Morning:
1. **Double-click** `run_with_venv.bat`
2. **Review** yesterday's usage
3. **Check** any warnings or alerts
4. **Plan** today's data processing needs

### What to Monitor:
- **Total requests** - Are you within daily limits?
- **Daily costs** - Within your budget?
- **API errors** - Any connection issues?
- **Model usage** - Using optimal models?

## 🚨 Setting Up Alerts

### OpenAI Dashboard Alerts:
1. Visit: https://platform.openai.com/usage
2. Go to **Account → Billing**
3. Set alerts at:
   - **$5/month** (Light usage warning)
   - **$25/month** (Medium usage warning)
   - **$50/month** (Heavy usage warning)

### Local Script Alerts:
The script automatically warns you if:
- Daily requests > 100
- Daily cost > $1.00
- Approaching rate limits

## ✅ Success Checklist

- [x] **OpenAI API key working** ✓
- [x] **Virtual environment configured** ✓
- [x] **Arabic processing working** ✓
- [x] **Usage tracking active** ✓
- [x] **Cost monitoring setup** ✓
- [x] **Daily batch file ready** ✓

## 🎉 You're All Set!

Your Sudan humanitarian platform now has:
- ✅ **Working OpenAI integration**
- ✅ **Arabic text processing**
- ✅ **Automatic usage tracking**
- ✅ **Cost monitoring**
- ✅ **Daily monitoring system**

**Just double-click `run_with_venv.bat` daily to monitor your usage!**