# 🚀 Quick Setup Guide

## ⚡ 5-Minute Setup

### Step 1: Set API Key
```bash
# Option A: Create .env file
copy .env.example .env

# Edit .env and add your Google Gemini API key:
# GOOGLE_API_KEY=your_key_here

# Option B: Use UI Later
# You can set it in the application sidebar under "Settings"
```

### Step 2: Verify Installation
```bash
python test_system.py
```

Expected output: **✅ All checks passed!**

### Step 3: Run the Application
```bash
streamlit run app.py
```

The app will open at: `http://localhost:8501`

---

## 🎯 First Time Usage

### What You'll See
1. **Chat Tab** - Ask questions about financial documents
2. **Analytics Tab** - View query statistics
3. **Documents Tab** - Manage uploaded files
4. **Help Tab** - Learn how to use the system

### Try These Example Queries

#### Query 1: KPI Extraction
```
What was the revenue growth from 2023 to 2024?
```
Expected: Shows 20% growth with calculation details

#### Query 2: Financial Summarization
```
Summarize the financial performance
```
Expected: Key highlights and metrics summary

#### Query 3: Risk Analysis
```
What are the main financial risks?
```
Expected: Risk factors analysis with detailed explanations

#### Query 4: Recommendation (Triggers Approval)
```
Should I invest in this company?
```
Expected: Human approval required message

---

## 📄 Upload Documents (Advanced)

### Manual Upload
1. Click "Upload Documents" in sidebar
2. Select PDF or TXT files
3. Click "Process & Index Documents"
4. Wait for confirmation

### Test with Included Document
The system includes a sample financial report:
```
data/sample_financial_report.txt
```

This document contains:
- Revenue analysis (2024: $150M)
- Profitability metrics
- Balance sheet data
- Cash flow information
- Risk analysis
- Growth opportunities

Try questions like:
- "What was the total revenue in 2024?"
- "What is the debt-to-equity ratio?"
- "What are the growth opportunities?"

---

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key

# Optional - adjust if needed
GEMINI_MODEL=gemini-3.6-flash
EMBEDDING_MODEL=gemini-embedding-001
LOG_LEVEL=INFO
CHUNK_SIZE=500
CHUNK_OVERLAP=50
VECTOR_DB_DIR=vector_db
```

### API Key Alternatives
- **Option 1** (Recommended): `.env` file
- **Option 2**: Environment variable
  ```bash
  set GOOGLE_API_KEY=your_key
  ```
- **Option 3**: App sidebar → Settings

---

## ✅ Verification Steps

### 1. Check System Status
```bash
python test_system.py
```

All tests should show ✅

### 2. Test Workflow (Optional)
```bash
python test_integration.py
```

Runs 5 end-to-end tests with different query types

### 3. Check Logs
```bash
# View recent logs
type logs\app.log | tail -20
```

---

## 🎬 Demo Walkthrough

### Timeline: 10 minutes

**0:00-1:00** - Show Problem
- Open sample financial report
- Highlight complexity
- Explain the challenge

**1:00-2:00** - Show Architecture
- Point to system diagram in README
- Explain the 6 agents
- Highlight parallel execution

**2:00-5:00** - Live Demo
Ask these queries in order:
1. "What was the revenue growth?" → Shows KPI Agent
2. "Summarize financials" → Shows Summary Agent
3. "What are risks?" → Shows Risk Analysis + KPI (Parallel)
4. "Should I invest?" → Shows Human Approval

**5:00-8:00** - Show Features
- Explain workflow details (click expander)
- Show sources retrieved
- Demonstrate upload feature

**8:00-10:00** - Analytics & Close
- Show Analytics dashboard
- Explain agent usage breakdown
- Summary of capabilities

---

## 🐛 Troubleshooting

### Issue: "API Key Error"
```
Solution: Set GOOGLE_API_KEY in .env file or sidebar
```

### Issue: "Vector store not loaded"
```
Solution: The vector store loads automatically on first run
Wait 2-3 seconds for initialization
```

### Issue: "Slow responses"
```
Solution 1: Check internet connection
Solution 2: Reduce CHUNK_SIZE in .env (default 500)
Solution 3: Use smaller documents
```

### Issue: "Streamlit not found"
```
Solution: pip install streamlit
Or: pip install -r requirements.txt
```

### Issue: "Port 8501 already in use"
```
Solution: streamlit run app.py --server.port 8502
```

---

## 📊 Expected Performance

| Query Type | Time | Agent |
|-----------|------|-------|
| KPI Extraction | 2-3s | kpi_node |
| Summarization | 2-4s | summary_node |
| General Q&A | 3-5s | retrieval_node |
| Risk Analysis | 4-6s | financial_analysis (parallel) |
| Approval | <1s | human_approval |

---

## 🎓 Understanding the System

### Agent Roles

**Router Agent**
- Classifies your question
- Routes to appropriate agent
- Detects investment questions

**Retrieval Agent**
- General Q&A over documents
- Returns relevant excerpts
- Shows sources

**KPI Agent**
- Extracts financial metrics
- Calculates growth rates, margins, ratios
- Provides numerical answers

**Summary Agent**
- Summarizes documents
- Highlights key points
- Bullet-point format

**Risk Analysis Agent**
- Identifies financial risks
- Explains implications
- Parallel with KPI for performance

**Human Approval Agent**
- Flags investment questions
- Requires manual review
- Prevents unsupported recommendations

### Workflow Flow

```
Your Question
    ↓
Router (Classifies)
    ↓
    ├→ KPI → Returns metrics
    ├→ Summary → Returns summary
    ├→ Retrieval → Returns answer
    ├→ Financial Analysis → Runs KPI + Risk (parallel) → Combines results
    └→ Human Approval → Flags for review
```

---

## 💡 Tips & Tricks

### Best Practices
1. **Be Specific**: "Revenue in Q4 2024?" better than "financial data"
2. **Use Context**: "Based on 2024 data, what are risks?" is better
3. **Check Sources**: Always review documents used (click expander)
4. **Export Results**: Download important responses as JSON

### Advanced
- Upload your own financial documents
- Ask follow-up questions (memory is maintained)
- Bulk upload multiple documents
- Track queries in Analytics tab

---

## 📚 Documentation

- **README.md** - Comprehensive project documentation
- **SETUP_GUIDE.md** - This file
- **test_system.py** - System verification
- **test_integration.py** - End-to-end testing
- **logs/app.log** - Application logs

---

## 🆘 Getting Help

1. **Check Logs**
   ```bash
   type logs\app.log
   ```

2. **Run Verification**
   ```bash
   python test_system.py
   ```

3. **Review README**
   - Architecture section
   - Troubleshooting section

4. **Check Documentation**
   - LangGraph: https://langchain-ai.github.io/langgraph/
   - Streamlit: https://docs.streamlit.io/
   - LangChain: https://python.langchain.com/

---

## ✨ You're All Set!

Your Financial RAG Assistant is ready to use. Start with:

```bash
streamlit run app.py
```

Then ask your first question! 🚀

---

**Questions?** Check the Help tab in the application.
