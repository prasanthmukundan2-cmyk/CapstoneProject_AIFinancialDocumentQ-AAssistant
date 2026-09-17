# System Architecture - AI Financial Document Q&A Assistant

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Agent Orchestration](#agent-orchestration)
6. [RAG Pipeline](#rag-pipeline)
7. [Workflow Execution](#workflow-execution)
8. [Error Handling & Reliability](#error-handling--reliability)
9. [Performance Optimizations](#performance-optimizations)

---

## System Overview

### Purpose
The AI Financial Document Q&A Assistant helps financial analysts and investors understand complex financial documents through intelligent document analysis, KPI extraction, risk assessment, and comparative analysis.

### Problem Solved
- **Dense Financial Reports**: Users struggle to understand annual reports, balance sheets, and financial statements
- **Manual Analysis**: Analysis is time-consuming and error-prone
- **Information Extraction**: Hard to identify key metrics and trends
- **Document Comparison**: Difficult to compare financial metrics across multiple documents

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | LangGraph | Multi-agent orchestration |
| **LLM** | Google Gemini 3.6 Flash | Natural language understanding & generation |
| **Embeddings** | Google Generative AI | Document vectorization |
| **Vector DB** | FAISS | Fast similarity search & retrieval |
| **Text Splitting** | LangChain RecursiveCharacterTextSplitter | Document chunking |
| **UI** | Streamlit | Interactive web interface |
| **Cache** | Custom cache_manager.py | Response caching |
| **Retry Logic** | retry_utils.py | Rate-limit tolerance |

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     USER INTERFACE (Streamlit)                    │
│  - Document Upload  - Chat Interface  - Agent Metrics Display    │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────────┐
        │   Document Processing Pipeline         │
        │  - PDF/TXT Extraction                  │
        │  - Chunking & Metadata Tagging         │
        └────────────┬─────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────────┐
        │   Vector Database (FAISS)              │
        │  - Multi-document Index                │
        │  - Semantic Search Retrieval           │
        │  - Source File Metadata                │
        └────────────┬─────────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────────────────┐
    │          Multi-Agent Workflow (LangGraph)          │
    │                                                    │
    │  1️⃣  ROUTER NODE (Sequential)                      │
    │      ├─ Regex Pattern Matching                    │
    │      ├─ LLM Fallback (if uncertain)               │
    │      └─ Decides which agents to run               │
    │                        │                          │
    │                        ▼                          │
    │  2️⃣  PARALLEL AGENTS (Conditional Execution)      │
    │      ├─ Retrieval Agent (general Q&A)            │
    │      ├─ KPI Agent (metrics + tools)              │
    │      ├─ Summary Agent (document overview)         │
    │      ├─ Risk Agent (financial risks)             │
    │      └─ Health Agent (financial health tools)     │
    │      ├─ Comparison Agent (multi-doc compare)      │
    │                        │                          │
    │                        ▼                          │
    │  3️⃣  COMBINE NODE (Python Logic - No LLM Call)     │
    │      ├─ Collect results from active agents        │
    │      ├─ Intelligent formatting & ordering         │
    │      └─ Return combined response                  │
    └────────────┬──────────────────────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────────────┐
    │    Response Post-Processing              │
    │  - Cache management                      │
    │  - Investment approval detection         │
    │  - Error handling & formatting           │
    └──────────────────────────────────────────┘
                 │
                 ▼
        ┌─────────────────────────────┐
        │  Display to User (Streamlit) │
        │  - Answer text               │
        │  - Agent used info           │
        │  - Execution time            │
        │  - Cache status              │
        └─────────────────────────────┘
```

---

## Component Details

### 1. Document Processor (`document_processor.py`)
**Responsibility**: Handle file uploads and text extraction

```
Input: PDF/TXT file
  ├─ PDF: PyPDFLoader extracts text + metadata
  ├─ TXT: Read file directly
  └─ Return: (file_path, extracted_text, metadata)

Output: Processed document ready for vectorization
```

**Key Features:**
- Handles PDF and TXT formats
- Extracts text while preserving structure
- Tags documents with source file metadata
- Saves uploads to `data/uploaded/` directory

---

### 2. RAG Pipeline (`rag_pipeline.py`)
**Responsibility**: Build and maintain vector database

```
Build Process:
  1. Load all files from data/uploaded/
  2. Fall back to sample files if no uploads
  3. Split into chunks (500 chars, 50 overlap)
  4. Generate embeddings (Google Generative AI)
  5. Index in FAISS vector store
  6. Save to data/vector_db/

Retrieval Process:
  1. User query → Generate embedding
  2. Search FAISS for k=3 similar chunks
  3. Return chunks with source_file metadata
  4. Use for agent context
```

**Key Features:**
- Multi-document support (all documents indexed together)
- Source file tracking (enables comparison)
- Automatic rebuilding when files uploaded
- Cached vector database

---

### 3. Router Node (`workflow_optimized.py`)
**Responsibility**: Decide which agents to invoke

**Hybrid Routing Strategy:**

```
Input: User question

Step 1: REGEX MATCHING (Fast, Free)
  ├─ KPI patterns: revenue, profit, earnings, margin, growth
  ├─ Summary patterns: summarize, overview, brief, recap
  ├─ Risk patterns: risks, challenges, threats, concerns
  ├─ Comparison patterns: compare, vs, difference, between
  └─ Confidence score based on matches

Step 2: CONFIDENCE CHECK
  ├─ High confidence (2+ patterns): Use regex result
  └─ Low confidence (0-1 patterns): Use LLM fallback

Step 3: LLM FALLBACK (If needed)
  ├─ Send question to Gemini for classification
  ├─ Parse response for agent names
  └─ Select top agents

Output: Route string (e.g., "kpi,summary" or "comparison")
```

**Example Decisions:**
- "What's the revenue?" → "kpi"
- "Summarize the report" → "summary"
- "What are the risks?" → "risk"
- "Compare 2024 vs 2023" → "comparison"
- "Give full analysis" → "retrieval,kpi,summary,risk"

---

### 4. Agent Nodes (`agents_fixed.py`)

#### Retrieval Agent
**Purpose**: General Q&A from documents
```
Process:
  1. Retrieve 3 most relevant chunks
  2. Create prompt with context
  3. LLM generates answer
  4. Return with sources

Use Case: "How many employees?"
```

#### KPI Agent (Tool-Using)
**Purpose**: Extract and calculate financial metrics
```
Process:
  1. Retrieve financial metrics from docs
  2. Extract raw numbers (revenue, profit, etc)
  3. Use financial calculation tools
  4. Return formatted metrics

Tools Used:
  - Profit Margin Calculator
  - ROI Calculator
  - Growth Rate Calculator
  - Debt-to-Equity Ratio
  - Current Ratio
  - Earnings Per Share

Use Case: "What's the profit margin?"
```

#### Summary Agent
**Purpose**: Provide document overview
```
Process:
  1. Retrieve key chunks from document
  2. Generate concise summary
  3. Focus on main points
  4. Return bullet-point format

Use Case: "Summarize the annual report"
```

#### Risk Agent
**Purpose**: Identify and explain financial risks
```
Process:
  1. Retrieve risk-related information
  2. Analyze financial challenges
  3. Explain potential impacts
  4. Return risk assessment

Use Case: "What are the major risks?"
```

#### Financial Health Agent (Tool-Using)
**Purpose**: Analyze overall financial health
```
Process:
  1. Retrieve financial metrics
  2. Use calculation tools to derive ratios
  3. Analyze financial health score
  4. Identify risks and recommendations

Tools Used:
  - Profit Margin, Debt-to-Equity, Current Ratio
  - Financial health analyzer

Use Case: "Is the company financially healthy?"
```

#### Comparison Agent
**Purpose**: Compare metrics across documents
```
Process:
  1. Retrieve relevant chunks from all docs
  2. Group by source_file metadata
  3. Compare metrics
  4. Show differences and trends

Use Case: "Compare revenue between 2023 and 2024"
```

---

### 5. Combine Node (`workflow_optimized.py`)
**Responsibility**: Merge agent results (NO LLM CALL)

**Strategy:**
```python
if single_agent_ran:
    return agent_result_directly
else:
    combine_in_smart_order()
    # Order: Comparison → Summary → KPI → Risk → Retrieval
    return formatted_response
```

**Optimization**: This Python-based combining saves 1 API call per question!

---

### 6. Cache Manager (`cache_manager.py`)
**Responsibility**: Store and retrieve cached responses

```
Cache Key: hash(question, document_set)
Cache Value: (response, timestamp, agent_used)
Cache Duration: 1 hour (configurable)

Benefits:
- Identical questions return instant answers
- Reduces API calls
- Improves performance
```

---

### 7. Retry Utility (`retry_utils.py`)
**Responsibility**: Handle rate limits and network failures

```
Retry Strategy:
  1. Try request
  2. If rate limit → Wait and retry
  3. If timeout → Exponential backoff
  4. Max retries: 3 with delays
  
Optimization:
- Fast-fails on non-recoverable errors
- Detects rate limits immediately
- Adapts to free tier limits (60 req/min)
```

---

## Data Flow

### Example: "What's the profit margin?"

```
1. User Input (app.py)
   └─ Question: "What's the profit margin?"

2. Router (workflow_optimized.py)
   └─ Regex matches "profit margin"
   └─ Decision: "kpi" agent

3. KPI Agent (agents_fixed.py)
   ├─ Retrieval: Query vector DB for "profit margin"
   │  └─ Gets 3 chunks with source metadata
   ├─ Tool Usage: Calculate profit margin
   │  └─ ratio = (profit / revenue) * 100
   └─ Return: "Profit Margin: 15.3%"

4. Combine Node (workflow_optimized.py)
   └─ Single agent → Return result directly

5. Post-Process (app.py)
   ├─ Check for investment recommendation
   ├─ Add to cache
   └─ Display with metadata

6. User Display (Streamlit)
   ├─ Answer: "Profit Margin: 15.3%"
   ├─ Agent: "kpi"
   └─ Time: 2.1 seconds
```

### Example: "Compare revenue between documents"

```
1. User Input
   └─ Question: "Compare revenue between documents"

2. Router
   └─ Regex matches "compare"
   └─ Decision: "comparison" agent (overrides others)

3. Comparison Agent
   ├─ Retrieval: Query for "revenue"
   ├─ Group by source_file metadata
   ├─ Extract: Doc1: $150M, Doc2: $120M
   └─ Return: "Doc1 is 25% higher than Doc2"

4. Combine Node
   └─ Single agent → Return directly

5. Display
   ├─ Answer: Comparison analysis
   ├─ Agent: "comparison"
   └─ Time: 3.2 seconds
```

---

## Agent Orchestration

### Execution Model: Sequential + Parallel

```
Timeline:

T0: Question arrives
├─ Router starts (sequential)
│
T1: Router decides agents
├─ All selected agents start simultaneously (parallel)
├─ Retrieval Agent
├─ KPI Agent
├─ Summary Agent
├─ Risk Agent
├─ Health Agent
└─ Comparison Agent

T2: All agents complete (or timeout at 15s)
├─ Combine node processes results
│
T3: Response ready
└─ Display to user
```

**Example Timing:**
- Router: 0.5s
- Parallel Agents: 2-3s
- Combine: 0.1s
- Total: 2.6-3.6s ✅

---

## RAG Pipeline

### Indexing Flow

```
Files in data/uploaded/
      │
      ├─ document1.pdf ──┐
      ├─ document2.pdf ──┤
      └─ document3.txt ──┤
                        ▼
            Document Loader (PyPDFLoader)
                        │
                        ▼
            RecursiveCharacterTextSplitter
            (chunks: 500 chars, overlap: 50)
                        │
                        ▼
            Add Source Metadata
            (source_file: "document1.pdf")
                        │
                        ▼
            Generate Embeddings
            (Google Generative AI Embeddings)
                        │
                        ▼
            FAISS Vector Store
                        │
                        ▼
            Persistent Storage
            (data/vector_db/)
```

### Retrieval Flow

```
User Question
      │
      ├─ Generate embedding (same model as indexing)
      │
      ├─ Search FAISS (k=3)
      │  └─ Returns: 3 most similar chunks
      │
      ├─ Extract metadata
      │  └─ source_file = "document1.pdf"
      │
      └─ Pass to agents as context
```

### Multi-Document Support

```
Index contains:
├─ Chunks from doc1 (source_file: doc1.pdf)
├─ Chunks from doc2 (source_file: doc2.pdf)
└─ Chunks from doc3 (source_file: doc3.pdf)

Comparison Agent can:
├─ Search for "revenue"
├─ Get chunks from ALL documents
├─ Group by source_file
└─ Compare metrics across documents
```

---

## Workflow Execution

### LangGraph State Machine

```
State Variables:
├─ messages: List[BaseMessage]        # Chat history
├─ question: str                       # Current question
├─ route: str                          # Router decision
├─ retrieval_result: str               # From retrieval agent
├─ kpi_result: str                     # From KPI agent
├─ summary_result: str                 # From summary agent
├─ risk_result: str                    # From risk agent
├─ health_result: str                  # From health agent
├─ comparison_result: str              # From comparison agent
├─ answer: str                         # Final answer
├─ agent: str                          # Agent(s) used
└─ sources: list[str]                  # Document sources

Execution Graph:
START
  │
  ├─→ ROUTER NODE
  │    └─→ Decide: retrieval, kpi, summary, risk, health, comparison
  │
  ├─→ RETRIEVAL NODE (conditional)
  ├─→ KPI NODE (conditional + tool-using)
  ├─→ SUMMARY NODE (conditional)
  ├─→ RISK NODE (conditional)
  ├─→ HEALTH NODE (conditional + tool-using)
  ├─→ COMPARISON NODE (conditional)
  │
  ├─→ COMBINE NODE
  │    └─→ Merge results (Python only, no LLM)
  │
  └─→ END
```

---

## Error Handling & Reliability

### Layer 1: API Level
```python
# retry_utils.py
├─ Detect rate limits immediately
├─ Exponential backoff (0.5s, 1s, 2s)
├─ Max 3 retries
└─ Fast-fail on non-recoverable errors
```

### Layer 2: Agent Level
```python
# agents_fixed.py
├─ Try-except in every agent
├─ Graceful fallback responses
├─ Detailed error logging
└─ Return partial results if possible
```

### Layer 3: Workflow Level
```python
# workflow_optimized.py
├─ Conditional node execution
├─ Skip failed agents gracefully
├─ Combine whatever results available
└─ Always return an answer
```

### Layer 4: Application Level
```python
# app.py
├─ Catch workflow exceptions
├─ Show user-friendly error messages
├─ Log for debugging
└─ Offer retry option
```

---

## Performance Optimizations

### 1. Smart Routing
**Problem**: Running all 6 agents for every question wastes API calls
**Solution**: Router selects only needed agents
**Impact**: Reduced from 6 API calls/question → 1-3 API calls/question

Example:
- "What's the revenue?" → KPI agent only (1 API call)
- "Risks and profit?" → Risk + KPI agents (2 API calls)

### 2. Python-Based Combining
**Problem**: Combining agent results required another LLM call
**Solution**: Python logic formats and merges results
**Impact**: Saves 1 API call per question (20% reduction)

### 3. Response Caching
**Problem**: Identical questions repeat API calls
**Solution**: Cache responses for 1 hour
**Impact**: Instant answers for repeated questions

### 4. Parallel Agent Execution
**Problem**: Sequential agents wait for each other
**Solution**: All agents run simultaneously
**Impact**: 3-4s response time instead of 6-8s

### 5. Multi-Document Indexing
**Problem**: Re-indexing when new document uploaded
**Solution**: Rebuild entire FAISS index
**Impact**: Enables document comparison, clean state

---

## Session Management

### Streamlit Session State

```python
st.session_state:
├─ workflow              # LangGraph workflow instance
├─ messages              # Chat history
├─ uploaded_documents    # {filename: {size, chunks, path}}
├─ current_document      # Selected document
├─ comparison_docs       # Documents to compare
├─ api_key_set           # API availability
└─ show_comparison       # UI mode flag
```

### Memory Management

```
Chat History:
├─ Kept in session state (RAM)
├─ Passed to workflow as context
├─ Enables multi-turn conversations
└─ Cleared on "Clear Chat"

Vector Database:
├─ Loaded into FAISS (RAM)
├─ Rebuilt when documents uploaded
├─ Persistent storage: data/vector_db/
└─ Cleared with "Clear All Documents"

Cache:
├─ In-memory dictionary
├─ ~100MB for typical usage
└─ Cleared on demand
```

---

## Scalability Considerations

### Current Limits
- **Vector Store**: FAISS in-memory (suitable for <100MB documents)
- **Chat History**: Session RAM (suitable for <1000 messages)
- **Concurrent Users**: Single user (Streamlit default)

### Scaling Strategy for Production

```
For 10+ users:
├─ Vector DB: Move to Pinecone/Weaviate (cloud)
├─ Chat History: Use database (PostgreSQL)
├─ Session State: Use Redis
├─ Deployment: Docker + Kubernetes
└─ LLM: Consider batch API for cost

For 100+ concurrent:
├─ Add load balancer
├─ Horizontal scaling
├─ Database replication
├─ CDN for static assets
└─ Rate limiting per user
```

---

## API Call Optimization Summary

### Before Optimization
```
Per question: 6 API calls (all agents parallel)
  ├─ 1 Router call
  ├─ 6 Agent calls (parallel)
  └─ 1 Combine call
= 8 API calls/question
```

### After Optimization
```
Per question: 1-3 API calls (smart routing)
  ├─ 1 Router call (sometimes regex, no API)
  ├─ 1-3 Agent calls (only needed agents)
  └─ 0 Combine calls (Python only)
= 1-3 API calls/question (75% reduction!)
```

### Free Tier Impact
- Before: 60 req/min ÷ 8 calls/q = 7 questions max
- After: 60 req/min ÷ 2 calls/q = 30 questions max
- **Result**: 4x more questions on free tier! 🚀

---

## Conclusion

This architecture demonstrates:
- ✅ Professional multi-agent design
- ✅ Sophisticated orchestration
- ✅ Production-ready error handling
- ✅ Smart API optimization
- ✅ Scalable foundation

The system prioritizes **clarity, reliability, and efficiency** over unnecessary complexity.

