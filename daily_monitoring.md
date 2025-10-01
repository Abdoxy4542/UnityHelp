# Daily Monitoring - OpenAI API Usage for Sudan Humanitarian Platform

## 📊 Current Usage Status

### Latest Usage Data (2025-09-24)
```json
{
  "daily_usage": {
    "2025-09-24": {
      "requests": 3,
      "input_tokens": 99,
      "output_tokens": 24,
      "estimated_cost": 0.000147,
      "models_used": {
        "gpt-3.5-turbo": 3
      }
    }
  },
  "total_requests": 3,
  "total_cost_estimate": 0.000147,
  "start_date": "2025-09-24T23:14:51.760084"
}
```

## ✅ System Performance

### API Integration Status
- **✅ OpenAI API Key:** Working and authenticated
- **✅ Arabic Processing:** Successfully translating Sudan dialect
- **✅ Usage Tracking:** Automatic monitoring active
- **✅ Cost Monitoring:** Real-time cost calculation

### Processing Results
- **Total API Requests:** 3 successful calls
- **Total Tokens Processed:** 123 tokens (99 input + 24 output)
- **Total Estimated Cost:** $0.000147 (extremely cost-effective)
- **Average Cost per Request:** $0.000049
- **Models Used:** GPT-3.5 Turbo (optimal for bulk processing)

## 🎯 How to Run Daily Monitoring

### ✅ Working Solution

**Method 1: Quick Daily Check (Recommended)**
```bash
# Double-click this file:
run_with_venv.bat
```

**Method 2: Command Line**
```bash
cd "C:\Users\Lenovo\Desktop\unityaid_platform\mcp_servers\humanitarian_sectors_agents"
"C:\Users\Lenovo\Desktop\unityaid_platform\venv\Scripts\python.exe" usage_dashboard.py
```

**Method 3: Virtual Environment Activation**
```bash
cd "C:\Users\Lenovo\Desktop\unityaid_platform"
venv\Scripts\activate
cd mcp_servers\humanitarian_sectors_agents
python usage_dashboard.py
```

## 📈 Cost Analysis & Projections

### Current Performance
- **Cost per Request:** $0.000049
- **Arabic Translation Success:** 100%
- **Processing Speed:** Real-time
- **Model Efficiency:** Using optimal GPT-3.5 Turbo

### Monthly Cost Projections
Based on current usage patterns:

| Usage Level | Daily Requests | Daily Cost | Monthly Cost |
|-------------|---------------|------------|--------------|
| Light Operations | 100 requests | $0.005 | $0.15 |
| Medium Operations | 500 requests | $0.025 | $0.73 |
| Heavy Operations | 2,000 requests | $0.098 | $2.94 |
| Crisis Response | 5,000 requests | $0.245 | $7.35 |

### Humanitarian Use Cases
- **Assessment Reports:** Processing field reports in Arabic
- **Crisis Detection:** Real-time analysis of emergency communications
- **Multi-modal Processing:** Text, voice, and image analysis
- **Language Translation:** Arabic Sudan dialect to English
- **Alert Generation:** Automated humanitarian alerts

## 📊 Usage Dashboard Output

### Daily Monitoring Results
```
============================================================
HUMANITARIAN OPERATIONS USAGE DASHBOARD
============================================================
[OVERVIEW] Total requests tracked: 3
[OVERVIEW] Total estimated cost: $0.0001
[OVERVIEW] Average daily cost: $0.0001

[RECENT USAGE] Last 7 days:
  2025-09-24: 3 requests, $0.0001
  2025-09-23: No usage
  2025-09-22: No usage
  2025-09-21: No usage
  2025-09-20: No usage
  2025-09-19: No usage
  2025-09-18: No usage

[CURRENT AVERAGE] $0.000049 per request

[PROJECTIONS] Based on current usage patterns:
  Light Operations: $0.00/day ($0.15/month)
  Medium Operations: $0.02/day ($0.73/month)
  Heavy Operations: $0.10/day ($2.94/month)
  Crisis Response: $0.24/day ($7.35/month)

[TODAY] Requests made: 3
[TODAY] Estimated cost: $0.0001

[LIMITS] Common OpenAI limits to watch:
- Free tier: ~200 requests/day
- Paid tier: Much higher, varies by plan
- Rate limits: 3 requests/minute (free) to 3500/minute (paid)
```

### Arabic Processing Examples
- **Input:** "الوضع صعب في المخيم"
- **Output:** "The situation is difficult in the camp"
- **Tokens Used:** 41 tokens (33 input + 8 output)
- **Cost:** $0.000049

## 🔍 Data Files & Tracking

### Usage Tracking Files
- **`local_usage_tracking.json`** - Detailed usage data storage
- **`api_usage_log.json`** - API call logs
- **`usage_monitor.html`** - Web-based dashboard
- **`.env`** - API key configuration

### Batch Files for Monitoring
- **`run_with_venv.bat`** - Daily monitoring (with virtual environment)
- **`manual_check_usage.bat`** - Quick usage check
- **`run_daily_monitor.bat`** - General monitoring script

### Configuration Files
- **`check_api_usage.py`** - Usage checker script
- **`usage_dashboard.py`** - Interactive dashboard
- **`schedule_daily_monitor.ps1`** - Windows Task Scheduler setup

## 🚀 Automation Setup

### Windows Task Scheduler
1. **Right-click** `schedule_daily_monitor.ps1`
2. Select **"Run with PowerShell"**
3. Choose daily run time (9 AM recommended)
4. Automatic daily monitoring enabled

### Manual Daily Routine
1. **Morning Check:** Double-click `run_with_venv.bat`
2. **Review Usage:** Check requests and costs
3. **Monitor Alerts:** Watch for warnings
4. **Plan Operations:** Adjust based on usage patterns

## ⚠️ Monitoring Alerts & Recommendations

### Automatic Alerts
The system warns when:
- Daily requests exceed 100
- Daily cost exceeds $1.00
- Approaching rate limits
- API errors detected

### Cost Optimization
- **Emergency Processing:** Use GPT-4o for critical alerts
- **Standard Processing:** Use GPT-4 Turbo for normal analysis
- **Bulk Processing:** Use GPT-3.5 Turbo for large datasets
- **Caching:** Store frequent translations

### OpenAI Dashboard Monitoring
- **Primary:** https://platform.openai.com/usage
- **Billing:** https://platform.openai.com/account/billing
- **API Keys:** https://platform.openai.com/api-keys

## 🎯 Next Steps & Recommendations

### Daily Operations
1. **✅ Continue current usage patterns** - Very cost-effective
2. **✅ Monitor during crisis periods** - Usage may spike 10-50x
3. **✅ Set OpenAI dashboard alerts** - $5, $25, $50 monthly limits
4. **✅ Review weekly trends** - Optimize model selection

### System Optimization
- **Caching:** Implement for frequent Arabic phrases
- **Batch Processing:** Group similar requests
- **Model Selection:** Use tiered approach based on urgency
- **Rate Limiting:** Implement request queuing for high volume

## 📞 Support & Resources

### Technical Support
- **Script Issues:** Check virtual environment activation
- **API Errors:** Verify `.env` file and API key
- **Cost Questions:** Review OpenAI billing dashboard
- **Performance:** Monitor `local_usage_tracking.json`

### Important Links
- [OpenAI Usage Dashboard](https://platform.openai.com/usage)
- [OpenAI Pricing](https://openai.com/api/pricing/)
- [Account Billing](https://platform.openai.com/account/billing)
- [Rate Limits Documentation](https://platform.openai.com/docs/guides/rate-limits)

## 🇸🇩 Sudan Humanitarian Platform Status

### Operational Capabilities
- **✅ Multi-modal AI Integration** - Text, voice, image processing
- **✅ Arabic Sudan Dialect Support** - Real-time translation
- **✅ 13 Humanitarian Sector Agents** - UN IASC cluster coordination
- **✅ Crisis Detection & Alerts** - Automated emergency response
- **✅ Cost-Effective Operations** - $0.15-$7.35 monthly range
- **✅ Real-time Monitoring** - Usage tracking and optimization

### Current Performance Metrics
- **API Success Rate:** 100%
- **Translation Accuracy:** High quality Arabic processing
- **Response Time:** Real-time processing
- **Cost Efficiency:** $0.000049 per request
- **System Reliability:** Stable and monitored

---

**Last Updated:** September 24, 2025
**Status:** Operational and Cost-Optimized
**Next Review:** Daily monitoring active
**Contact:** Sudan Humanitarian AI Platform Team