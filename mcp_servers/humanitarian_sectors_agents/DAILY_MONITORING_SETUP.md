# 📅 Daily OpenAI Usage Monitoring Setup Guide

## 🚀 Quick Setup (Automatic)

### Option 1: Set Up Automated Daily Monitoring

1. **Right-click** on `schedule_daily_monitor.ps1`
2. Select **"Run with PowerShell"**
3. Choose your preferred time:
   - **9:00 AM** (recommended for morning review)
   - **6:00 PM** (end of day review)
   - **Custom time** (your choice)

This creates a Windows scheduled task that runs automatically every day!

### Option 2: Manual Daily Checks

**Double-click** `manual_check_usage.bat` anytime to:
- Check current usage summary
- View tracking data
- Test API status
- Get quick actions menu

## 📊 What You'll See Daily

### Automatic Report Includes:
```
============================================================
HUMANITARIAN OPERATIONS USAGE DASHBOARD
============================================================
[OVERVIEW] Total requests tracked: 5
[OVERVIEW] Total estimated cost: $0.0002
[OVERVIEW] Average daily cost: $0.0001

[RECENT USAGE] Last 7 days:
  2025-09-24: 1 requests, $0.0000
  2025-09-23: No usage
  ...

[PROJECTIONS] Based on current usage patterns:
  Light Operations: $0.00/day ($0.15/month)
  Medium Operations: $0.02/day ($0.73/month)
  Heavy Operations: $0.10/day ($2.94/month)
```

### Local Data Storage
Check `local_usage_tracking.json` for detailed data:
```json
{
  "daily_usage": {
    "2025-09-24": {
      "requests": 1,
      "input_tokens": 33,
      "output_tokens": 8,
      "estimated_cost": 0.000049,
      "models_used": {
        "gpt-3.5-turbo": 1
      }
    }
  },
  "total_requests": 1,
  "total_cost_estimate": 0.000049
}
```

## 🔧 Manual Methods

### Method 1: Command Line
```bash
# Navigate to the folder
cd "C:\Users\Lenovo\Desktop\unityaid_platform\mcp_servers\humanitarian_sectors_agents"

# Run the dashboard
python usage_dashboard.py
```

### Method 2: Batch File
Double-click `run_daily_monitor.bat` for automated monitoring

### Method 3: PowerShell
```powershell
# Run in PowerShell
cd "C:\Users\Lenovo\Desktop\unityaid_platform\mcp_servers\humanitarian_sectors_agents"
python usage_dashboard.py
```

## 📱 Multiple Ways to Check Usage

### 1. **Scheduled Automatic** (Set once, runs forever)
- Runs daily at your chosen time
- No manual intervention needed
- Results saved to log files

### 2. **Quick Manual Check**
Double-click: `manual_check_usage.bat`

### 3. **Full Dashboard**
```bash
python usage_dashboard.py
```

### 4. **Web Interface**
Open `usage_monitor.html` in browser

### 5. **Official OpenAI Dashboard**
Visit: https://platform.openai.com/usage

## 📈 Understanding Your Tracking Data

### Daily Usage File: `local_usage_tracking.json`

**Key Fields:**
- `total_requests`: Total API calls made
- `total_cost_estimate`: Estimated total cost in USD
- `daily_usage`: Breakdown by date
- `input_tokens`/`output_tokens`: Token usage
- `models_used`: Which AI models you used

### Example Usage Interpretation:

```json
"2025-09-24": {
  "requests": 15,           // 15 API calls today
  "estimated_cost": 0.0075, // Cost: $0.0075 (very reasonable!)
  "models_used": {
    "gpt-3.5-turbo": 10,    // 10 bulk processing calls
    "gpt-4o": 5             // 5 emergency processing calls
  }
}
```

## ⏰ Scheduling Options

### Option A: Windows Task Scheduler (Recommended)
- **Setup**: Run `schedule_daily_monitor.ps1`
- **Frequency**: Daily
- **Time**: Your choice (9 AM recommended)
- **Benefits**: Fully automatic, runs even when you're not using computer

### Option B: Manual Daily Habit
- **Setup**: Bookmark `manual_check_usage.bat`
- **Frequency**: When you remember
- **Time**: Anytime
- **Benefits**: You control when it runs

### Option C: Batch File Shortcut
1. Right-click `run_daily_monitor.bat`
2. Create shortcut
3. Move shortcut to Desktop
4. Double-click daily

## 🚨 What to Watch For

### Daily Alerts
The system will warn you about:

**High Usage:**
```
[WARNING] High request volume today - monitor for rate limits
Requests made: 150 (limit: 200)
```

**High Costs:**
```
[WARNING] Daily cost is high - consider optimizing usage
Today's cost: $2.50
```

**Rate Limits:**
```
[WARNING] Approaching daily rate limit
Requests remaining: 25
```

## 📋 Daily Monitoring Checklist

### Every Morning (Recommended):
- [ ] Check overnight usage
- [ ] Review any alerts
- [ ] Confirm API status
- [ ] Plan day's operations

### What to Look For:
1. **Total requests** - Are you within limits?
2. **Daily cost** - Within budget?
3. **Model usage** - Using optimal models?
4. **Error rates** - Any API issues?

### Weekly Review:
- [ ] Analyze usage trends
- [ ] Review cost efficiency
- [ ] Adjust alerts if needed
- [ ] Plan for next week

## 🔍 Troubleshooting

### If Scheduled Task Doesn't Work:
1. **Check Task Scheduler**:
   - Press `Win + R`, type `taskschd.msc`
   - Look for "Sudan_Humanitarian_AI_Monitor"
   - Right-click → Run to test

2. **Check Permissions**:
   - Task might need administrator rights
   - Re-run `schedule_daily_monitor.ps1` as administrator

3. **Manual Fallback**:
   - Use `manual_check_usage.bat` instead
   - Set phone reminder to run daily

### If Python Doesn't Run:
```bash
# Check if Python is in PATH
python --version

# If not working, use full path:
C:\Python311\python.exe usage_dashboard.py
```

### If No Data Shows:
- First run `python usage_dashboard.py` to generate initial data
- Make API calls to have something to track
- Check that `.env` file contains your API key

## 📞 Support

### For Technical Issues:
1. Run `python test_api_key.py` to verify setup
2. Check `local_usage_tracking.json` exists
3. Verify `.env` file has `OPENAI_API_KEY`

### For Usage Questions:
- Check [OpenAI Usage Dashboard](https://platform.openai.com/usage)
- Review monthly billing in OpenAI account
- Contact OpenAI support if needed

---

## 🎯 Next Steps After Setup

1. **✅ Set up automatic monitoring** (run `schedule_daily_monitor.ps1`)
2. **📊 Check data daily** for first week to understand patterns
3. **⚠️ Set alerts** in OpenAI dashboard ($5, $25, $50)
4. **📈 Monitor during operations** especially during crisis response
5. **🔧 Optimize** based on usage patterns

**Your humanitarian operations are now fully monitored and cost-optimized!** 🇸🇩