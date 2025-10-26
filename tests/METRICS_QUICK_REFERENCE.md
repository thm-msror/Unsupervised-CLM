# 📊 Quick Metrics Reference

## 🚀 How to Read Your Performance Dashboard

### ✅ What Good Numbers Look Like
```
📈 Success Rate: >90% (Excellent: >95%)
⏱️  Processing Time: <5s per document  
🔍 Extraction Accuracy: >80%
❌ Error Rate: <10%
```

### 🔧 Quick Commands
```bash
# Run analysis with metrics
python src/analysis.py

# Test system health
python tests/test_enhanced_analysis.py
```

### 📋 Metrics Cheat Sheet

| Metric | Formula | Good Range | What It Means |
|--------|---------|------------|---------------|
| Success Rate | `successful/total × 100` | >90% | Documents processed without fallback |
| Throughput | `successful_docs/session_minutes` | >10 docs/min | Processing speed |
| Error Rate | `failed/total × 100` | <10% | System reliability |
| Extraction Accuracy | `key_info_found/expected × 100` | >80% | AI understanding quality |
| Complexity Score | `length + terminology + structure` | 1-5 scale | Document difficulty |

### 🔄 Retry System Status
- ✅ **"No failed analyses found"** = All good!
- 🔄 **"Retrying X analyses"** = System auto-fixing issues
- 📊 **"Retry Success Rate: X%"** = Recovery effectiveness

### 💡 Quick Fixes
- **Low Success Rate** → Check API key & network
- **Slow Processing** → Use shorter prompts or smaller docs
- **Poor Extraction** → Review/improve analysis prompts
- **High Error Rate** → Monitor API quotas

---
*📖 For detailed explanations, see PERFORMANCE_METRICS_README.md*