# 🔧 Troubleshooting Guide

## Common Issues & Solutions

### Issue 1: `TypeError: ChatMixin.chat_input() got multiple values for argument 'placeholder'`

**Status**: ✅ **FIXED** in latest version

**What it means**: The `st.chat_input()` function was being called incorrectly.

**Solution**: Already fixed in `app.py`. Just run:
```bash
streamlit run app.py
```

---

## Before Running the App

### Step 1: Verify Installation ✅
```bash
python test_system.py
```

**Expected Output**:
```
============================================================
FINANCIAL RAG ASSISTANT - SYSTEM VERIFICATION
============================================================

✓ TEST 1: Checking Environment Variables
✅ GOOGLE_API_KEY configured

✓ TEST 2: Checking Required Dependencies
✅ UI Framework............................ installed
✅ LangChain Core.......................... installed
[... all 10 dependencies should show ✅ ...]

✓ TEST 15: Testing Logging Setup
✅ Logging configured successfully

============================================================
VERIFICATION COMPLETE
============================================================

✅ All checks passed!

You can now start the application with:
   streamlit run app.py
```

If you see this, you're good to go!

---

## Running the App

### Method 1: Using Command Line (Recommended)
```bash
streamlit run app.py
```

The app will open at: `http://localhost:8501`

### Method 2: Using Batch File (Windows)
```bash
# Just double-click run_app.bat
run_app.bat
```

### Method 3: Using Python Directly
```bash
python -m streamlit run app.py
```

---

## Troubleshooting by Error

### Error: "ModuleNotFoundError: No module named 'streamlit'"

**Solution**:
```bash
pip install streamlit
# OR
pip install -r requirements.txt
```

### Error: "ModuleNotFoundError: No module named 'langchain'"

**Solution**:
```bash
pip install -r requirements.txt
```

### Error: "GOOGLE_API_KEY not configured"

**Solution 1: Using .env file** (Recommended)
```bash
# 1. Copy the example file
copy .env.example .env

# 2. Edit .env and add your key:
GOOGLE_API_KEY=your_actual_key_here

# 3. Save and restart the app
streamlit run app.py
```

**Solution 2: Using sidebar in app**
1. Open the app
2. Look at the sidebar (left side)
3. Find "Settings" section
4. Enter your API key in the text box
5. Refresh the page

**Solution 3: Using environment variable**
```bash
# Windows Command Prompt
set GOOGLE_API_KEY=your_key_here
streamlit run app.py

# Windows PowerShell
$env:GOOGLE_API_KEY="your_key_here"
streamlit run app.py

# Mac/Linux
export GOOGLE_API_KEY=your_key_here
streamlit run app.py
```

### Error: "Port 8501 already in use"

**Solution**:
```bash
# Use a different port
streamlit run app.py --server.port 8502

# OR kill the process using the port
# Windows:
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# Mac/Linux:
lsof -i :8501
kill -9 <PID>
```

### Error: "Vector store not loaded" or "Vector store directory not found"

**Solution**:
The vector store will be created automatically on first run. Just wait 2-3 seconds for initialization.

If it persists:
```bash
# Check if vector_db directory exists
ls vector_db/

# If not, run the system test to initialize everything
python test_system.py
```

### Error: "No documents found"

**Solution**:
1. Documents are in `data/` folder by default
2. You can upload new documents using the sidebar
3. Sample documents are in `data/sample_reports/`

Try uploading `data/sample_financial_report.txt`:
1. Click "Upload Documents" in sidebar
2. Select the file
3. Click "Process & Index Documents"
4. Wait for confirmation

### Error: "LLM response is empty"

**Solution**:
1. Check your API key is valid
2. Check your internet connection
3. Check Google Gemini API quota
4. Try a simpler question first
5. Check logs: `type logs\app.log`

### Error: "Connection timeout"

**Solution**:
1. Check internet connection
2. Check Google Gemini API status
3. Try a different question
4. Wait a moment and try again

---

## If App Won't Start

### Step-by-Step Debugging

**1. Check Python is installed**
```bash
python --version
```
Expected: `Python 3.x.x`

**2. Check dependencies**
```bash
python test_system.py
```
Expected: All tests pass ✅

**3. Check environment**
```bash
# On Windows
set | findstr GOOGLE

# On Mac/Linux
env | grep GOOGLE
```
Should show: `GOOGLE_API_KEY=your_key`

**4. Check logs**
```bash
type logs\app.log
```

**5. Try running without streamlit**
```bash
python app.py
```
(This won't work but will show Python errors)

---

## App Runs But No Response to Questions

### Check These:

1. **API Key is set** ✓
   - Sidebar → Settings → Should show "API key configured"

2. **Documents are indexed** ✓
   - Try: "What is this application?"
   - If no answer, documents may not be loaded

3. **LLM is working** ✓
   - Check logs: `type logs\app.log`
   - Look for error messages

4. **Vector store is loaded** ✓
   - Run: `python test_system.py`
   - Check TEST 5 output

### Debug Query:
Ask: **"What is the revenue?"**

Expected: Should show some answer about financial data

If no answer:
1. Check logs
2. Run verification test
3. Check API key
4. Upload a document

---

## Performance Issues

### App is slow to respond

**Solutions**:
1. Check internet connection
2. Large documents take longer
3. First query is slower (initialization)
4. Try simpler questions
5. Reduce CHUNK_SIZE in .env:
```bash
CHUNK_SIZE=300
CHUNK_OVERLAP=25
```

### App crashes

**Solutions**:
1. Check logs: `type logs\app.log`
2. Run system test: `python test_system.py`
3. Restart the app: Press Ctrl+C and run again
4. Clear cache: Delete `.streamlit/` folder

### API Rate Limit Error

**Solutions**:
1. Wait a few minutes
2. Check Google API quota
3. Reduce query frequency
4. Use smaller documents

---

## Reset Everything

If something goes wrong, reset and start fresh:

```bash
# 1. Stop the app (Ctrl+C)

# 2. Clear cache
rmdir /s /q .streamlit

# 3. Delete vector database
rmdir /s /q vector_db

# 4. Delete logs
del logs\app.log

# 5. Verify system
python test_system.py

# 6. Restart app
streamlit run app.py
```

---

## Getting Help

### Information Sources:

1. **Check this file**: TROUBLESHOOTING.md (you are here)
2. **Check logs**: `type logs\app.log`
3. **Run verification**: `python test_system.py`
4. **Check README**: README.md
5. **Check setup guide**: SETUP_GUIDE.md

### Run These Commands:

```bash
# 1. System verification
python test_system.py

# 2. Integration tests
python test_integration.py

# 3. Check logs
type logs\app.log

# 4. Check environment
echo %GOOGLE_API_KEY%
```

---

## What NOT to Do ❌

- ❌ Don't delete `app.py` or core files
- ❌ Don't modify workflow without understanding
- ❌ Don't share your API key
- ❌ Don't delete `data/` folder (has sample files)
- ❌ Don't run from a path with spaces (may cause issues)

---

## Quick Checklist

Before asking for help, verify:

- [ ] Python 3.8+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `python test_system.py` passes all 15 tests
- [ ] GOOGLE_API_KEY set in .env file
- [ ] `app.py` runs without errors
- [ ] Can open `http://localhost:8501`
- [ ] Can see the chat interface
- [ ] Logs file exists at `logs/app.log`

If all above are ✓, the issue is likely your API key or network connection.

---

## Common Questions (FAQ)

**Q: How do I know the app is running?**
A: You should see:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

**Q: Do I need to keep the terminal open?**
A: Yes, the terminal is the server. If you close it, the app stops.

**Q: Can I run multiple instances?**
A: Yes, on different ports:
```bash
streamlit run app.py --server.port 8501  # Terminal 1
streamlit run app.py --server.port 8502  # Terminal 2
```

**Q: Why is the first query slow?**
A: System initialization (loading LLM, embeddings, etc.). Subsequent queries are faster.

**Q: Can I change the port?**
A: Yes:
```bash
streamlit run app.py --server.port 9999
```

**Q: Where are my documents stored?**
A: In `data/uploaded/` folder after uploading.

**Q: How do I delete uploaded documents?**
A: Delete from `data/uploaded/` folder or use the app sidebar.

---

**Still stuck?** 

1. Run: `python test_system.py`
2. Share the output
3. Share relevant lines from: `type logs\app.log`
4. Share the error message you're seeing

---

*Last Updated: 2026-09-17*
*Status: Complete*
