# OpenAI API Usage Monitoring for Sudan Humanitarian Platform

## 📊 Overview

This guide shows you how to track your OpenAI API usage, monitor costs, and ensure you don't exceed your budget while running humanitarian operations.

## 🚀 Quick Start

### 1. Check Your Current Usage

```bash
# Run the usage tracker
python check_api_usage.py

# Run the interactive dashboard
python usage_dashboard.py
```

### 2. View Web Dashboard

Open `usage_monitor.html` in your browser for a visual dashboard.

## 💰 Understanding OpenAI Costs

### Current Pricing (2024)

| Model | Input (per 1K tokens) | Output (per 1K tokens) | Use Case |
|-------|----------------------|------------------------|----------|
| GPT-4o | $0.005 | $0.015 | 🚨 Emergency responses |
| GPT-4 Turbo | $0.010 | $0.030 | 📋 Standard processing |
| GPT-3.5 Turbo | $0.001 | $0.002 | 📊 Bulk operations |
| Whisper-1 | $0.006/minute | - | 🎤 Voice transcription |

### Token Calculation

- **1 token ≈ 4 characters** in English
- **Arabic text**: Similar ratio, but varies by dialect
- **Average humanitarian report**: ~200 tokens
- **Image analysis**: ~100-500 tokens depending on detail

## 📈 Usage Scenarios for Sudan Operations

### Light Operations (Small NGO)
- **100 requests/day** ≈ $0.15/month
- Single site monitoring
- Basic text processing

### Medium Operations (Multi-site NGO)
- **500 requests/day** ≈ $0.73/month
- Multiple gathering sites
- Voice + text processing

### Heavy Operations (Large NGO/UN)
- **2,000 requests/day** ≈ $2.94/month
- Comprehensive operations
- Multi-modal processing

### Crisis Response
- **5,000 requests/day** ≈ $7.35/month
- Emergency situations
- Real-time processing needs

## 🔍 How to Check Your Usage

### Method 1: OpenAI Dashboard (Recommended)

1. Visit [OpenAI Usage Dashboard](https://platform.openai.com/usage)
2. Login with your OpenAI account
3. View real-time usage and billing

**What you'll see:**
- Current usage this month
- Spending by model
- Request counts
- Rate limit status

### Method 2: Local Tracking Scripts

#### Basic Usage Check
```bash
python check_api_usage.py
```
**Shows:**
- API key status
- Available models
- Cost estimates
- Usage recommendations

#### Interactive Dashboard
```bash
python usage_dashboard.py
```
**Features:**
- Live usage tracking
- Cost calculations
- Local data storage
- Daily/monthly projections

### Method 3: Web Interface

Open `usage_monitor.html` in your browser for:
- Visual dashboard
- Real-time updates
- Export capabilities
- Mobile-friendly interface

## 📱 Setting Up Usage Alerts

### In OpenAI Dashboard

1. Go to [OpenAI Settings](https://platform.openai.com/account/billing)
2. Set up **Usage Alerts**:
   - **$5/month**: Light operations warning
   - **$25/month**: Medium operations warning
   - **$50/month**: Heavy operations warning
3. Enable email notifications

### Custom Alerts in Our Scripts

The monitoring scripts include automatic warnings:

```python
# Automatic alerts trigger when:
if daily_requests > 100:
    print("⚠️ High usage detected")

if daily_cost > 5.0:
    print("💰 Daily cost elevated")

if requests_remaining < 50:
    print("🚨 Approaching rate limit")
```

## 🎯 Cost Optimization Strategies

### 1. Tiered Model Usage

```python
# Use appropriate models for each task
emergency_model = "gpt-4o"        # Critical alerts
standard_model = "gpt-4-turbo"    # Normal analysis
bulk_model = "gpt-3.5-turbo"      # Large datasets
```

### 2. Smart Caching

```python
# Cache frequent translations
common_phrases = {
    "الوضع صعب": "Situation is difficult",
    "نحتاج مساعدة": "We need help",
    "مياه وغذاء": "Water and food"
}
```

### 3. Batch Processing

```python
# Process multiple items together
batch_size = 10
for batch in chunks(reports, batch_size):
    process_batch(batch)  # More efficient than individual calls
```

### 4. Token Optimization

```python
# Optimize prompts to reduce tokens
short_prompt = "Translate to English:"  # 4 tokens
long_prompt = "Please translate the following Arabic text to English language:"  # 12 tokens
```

## 📊 Monitoring Best Practices

### Daily Monitoring

1. **Check usage every morning**
   ```bash
   python usage_dashboard.py
   ```

2. **Review cost trends**
   - Daily spending patterns
   - Model usage distribution
   - Peak usage times

3. **Monitor during crises**
   - Usage often spikes 10-50x during emergencies
   - Set higher alerts for crisis periods

### Weekly Review

1. **Analyze efficiency**
   - Cost per processed report
   - Model selection effectiveness
   - Rate limit incidents

2. **Plan for next week**
   - Adjust model selection
   - Update usage alerts
   - Review budget allocation

### Monthly Planning

1. **Budget review**
   - Compare actual vs projected costs
   - Adjust operational models
   - Plan for seasonal variations

2. **Optimization review**
   - Identify cost-saving opportunities
   - Update caching strategies
   - Review model performance

## 🚨 Crisis Response Monitoring

During humanitarian emergencies:

### Pre-Crisis Setup
```bash
# Increase monitoring frequency
python usage_dashboard.py --monitor-interval 300  # Check every 5 minutes
```

### Crisis Mode Adjustments
- **Increase daily alerts** to $50-100
- **Use emergency tier models** (GPT-4o) liberally
- **Monitor rate limits** closely
- **Have backup plans** for quota exhaustion

### Post-Crisis Review
- Analyze usage patterns
- Document lessons learned
- Adjust future crisis protocols

## 💡 Troubleshooting Common Issues

### High Costs

**Symptoms:**
- Unexpected bills
- Rapid token consumption

**Solutions:**
```bash
# Check for runaway processes
python check_api_usage.py --detailed

# Review recent requests
grep "API_CALL" logs/humanitarian.log | tail -100
```

### Rate Limits

**Symptoms:**
- "Rate limit exceeded" errors
- Slow response times

**Solutions:**
- Upgrade to paid tier
- Implement request queuing
- Use exponential backoff

### Quota Exhaustion

**Symptoms:**
- "Insufficient quota" errors
- API calls failing

**Solutions:**
- Add payment method
- Increase spending limits
- Contact OpenAI support

## 📁 Files in This Monitoring System

| File | Purpose | Usage |
|------|---------|-------|
| `check_api_usage.py` | Basic usage checker | `python check_api_usage.py` |
| `usage_dashboard.py` | Interactive monitoring | `python usage_dashboard.py` |
| `usage_monitor.html` | Web dashboard | Open in browser |
| `local_usage_tracking.json` | Usage data storage | Auto-generated |
| `.env` | API key storage | Contains `OPENAI_API_KEY` |

## 🔗 Important Links

- [OpenAI Usage Dashboard](https://platform.openai.com/usage)
- [OpenAI Pricing](https://openai.com/api/pricing/)
- [OpenAI Rate Limits](https://platform.openai.com/docs/guides/rate-limits)
- [Account Billing](https://platform.openai.com/account/billing)

## 📞 Support

### For Technical Issues
1. Check logs: `logs/humanitarian.log`
2. Run diagnostics: `python test_api_key.py`
3. Review usage: `python usage_dashboard.py`

### For Billing Questions
- Contact OpenAI support through their dashboard
- Review usage in OpenAI platform
- Check payment methods and limits

## 🎯 Next Steps

1. **Set up daily monitoring**
   ```bash
   # Add to crontab for daily checks
   0 9 * * * cd /path/to/humanitarian && python usage_dashboard.py
   ```

2. **Configure alerts**
   - OpenAI dashboard alerts
   - Custom script notifications
   - Email/SMS integration

3. **Optimize operations**
   - Review model selection
   - Implement caching
   - Monitor effectiveness

---

*Last updated: September 2024*
*For Sudan Humanitarian AI Platform*