import time
import os
import json
from pathlib import Path

import streamlit as st
from langchain_core.messages import HumanMessage
from pypdf import PdfReader

from src.workflow_optimized import create_optimized_workflow
from src.cache_manager import get_cached_response, cache_response, clear_cache
from src.simple_investment import detect_investment_question, get_investment_response
from src.document_processor import process_upload
from src.retry_utils import invoke_with_retry
from src.agents_fixed import get_llm, _extract_text
from src.rag_pipeline import rebuild_vectorstore


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Financial RAG Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* Simple, clean styling for dark mode */
    .main {
        padding: 2rem;
    }

    h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #fff !important;
    }

    h2 {
        font-size: 1.5rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        color: #fff !important;
    }

    h3 {
        font-size: 1.2rem;
        font-weight: 600;
        margin-top: 1rem;
        color: #fff !important;
    }

    p {
        color: #ccc !important;
    }

    /* Chat message styling */
    .stChatMessage {
        padding: 16px;
        border-radius: 10px;
        margin: 10px 0;
    }

    /* Message boxes with clear colors */
    .success-box {
        padding: 15px;
        border-radius: 8px;
        background-color: #1e3d1f;
        color: #90ee90;
        border-left: 4px solid #28a745;
        margin: 10px 0;
        font-weight: 500;
    }

    .error-box {
        padding: 15px;
        border-radius: 8px;
        background-color: #3d1e1e;
        color: #ff6b6b;
        border-left: 4px solid #dc3545;
        margin: 10px 0;
        font-weight: 500;
    }

    .info-box {
        padding: 15px;
        border-radius: 8px;
        background-color: #1e2d3d;
        color: #87ceeb;
        border-left: 4px solid #17a2b8;
        margin: 10px 0;
        font-weight: 500;
    }

    .warning-box {
        padding: 15px;
        border-radius: 8px;
        background-color: #3d3d1e;
        color: #ffeb99;
        border-left: 4px solid #ffc107;
        margin: 10px 0;
        font-weight: 500;
    }

    /* File uploader */
    .stFileUploader {
        border: 2px dashed #555;
        border-radius: 8px;
        padding: 20px;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 6px;
        font-weight: 600;
        padding: 0.5rem 1rem;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        padding: 10px 0;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 10px 15px;
        font-weight: 600;
    }

    /* Clean divider */
    hr {
        margin: 1.5rem 0;
        border: none;
        height: 1px;
        background: #444;
    }

    /* Expander styling */
    .stExpander {
        border-radius: 8px;
        border: 1px solid #444;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

if "workflow" not in st.session_state:
    st.session_state.workflow = create_optimized_workflow()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_key_set" not in st.session_state:
    st.session_state.api_key_set = bool(os.getenv("GOOGLE_API_KEY"))

if "uploaded_documents" not in st.session_state:
    st.session_state.uploaded_documents = {}

if "current_document" not in st.session_state:
    st.session_state.current_document = None

if "comparison_docs" not in st.session_state:
    st.session_state.comparison_docs = []


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("⚙️ Settings & Info")

    # API Key Configuration
    st.subheader("🔑 API Configuration")
    api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        help="Enter your API key from console.cloud.google.com"
    )

    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        st.session_state.api_key_set = True
        st.success("✅ API key configured")
    elif os.getenv("GOOGLE_API_KEY"):
        st.success("✅ API key from .env file")
        st.session_state.api_key_set = True
    else:
        st.warning("⚠️ No API key set. Enter one above or set GOOGLE_API_KEY in .env")

    st.divider()

    # Cache Management
    st.subheader("💾 Cache Management")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear Cache"):
            clear_cache()
            st.success("Cache cleared!")
    with col2:
        st.caption(f"Messages: {len(st.session_state.messages)}")

    # Clear Chat History
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # Info
    st.subheader("ℹ️ Info")
    st.markdown("""
    **Financial RAG Assistant v1.0**

    Multi-agent system for financial Q&A

    - 6 specialized agents
    - Vector search (RAG)
    - Parallel execution
    - Document comparison
    - Rate limit handling
    """)


# ============================================================
# MAIN INTERFACE - TABS
# ============================================================

tab1, tab2, tab3 = st.tabs(["💬 Chat", "📄 Documents", "❓ Help"])


# ============================================================
# TAB 1: CHAT WITH DOCUMENT SUPPORT
# ============================================================

with tab1:
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 15px 0;'>
        <h1 style='margin: 0;'>📊 Financial Document Q&A</h1>
    </div>
    """, unsafe_allow_html=True)

    # Upload section in expander (collapsed by default if docs loaded)
    upload_expanded = len(st.session_state.uploaded_documents) == 0
    with st.expander("📤 Upload Documents", expanded=upload_expanded):
        col_main, col_side = st.columns([3, 1])

        with col_main:
            uploaded_file = st.file_uploader(
                "Choose document(s) (PDF or TXT)",
                type=["pdf", "txt"],
                key="chat_uploader",
                help="Upload financial documents to ask questions about them"
            )

        with col_side:
            st.markdown("**Actions:**")
            if len(st.session_state.uploaded_documents) > 1:
                if st.button("📊 Compare", use_container_width=True):
                    st.session_state.show_comparison = True

            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state.uploaded_documents = {}
                st.session_state.current_document = None
                st.session_state.comparison_docs = []
                st.rerun()

        # Process uploaded file
        if uploaded_file is not None:
            with st.spinner("📄 Processing document..."):
                try:
                    file_path, text_content, metadata = process_upload(uploaded_file)

                    doc_id = uploaded_file.name
                    st.session_state.uploaded_documents[doc_id] = {
                        "path": file_path,
                        "text": text_content,
                        "metadata": metadata,
                    }
                    st.session_state.current_document = doc_id

                    st.success(f"✅ Loaded: {uploaded_file.name}")
                    st.info(f"📄 File size: {metadata['file_size']/1024:.1f} KB | Words: ~{len(text_content.split())}")

                    # Rebuild vector store with new file
                    with st.spinner("🔄 Indexing document for search..."):
                        rebuild_vectorstore()
                    st.success("✅ Document indexed successfully!")

                    # Show current loaded documents
                    st.info(f"📁 **Total documents loaded:** {len(st.session_state.uploaded_documents)}")

                except Exception as e:
                    error_msg = str(e)
                    if "rate" in error_msg.lower():
                        st.error("""
                        ⚠️ **API Rate Limit Exceeded**

                        The Google Gemini API rate limit has been reached.

                        **Solutions:**
                        1. Wait 2-3 minutes and try uploading again
                        2. Check your API quota at console.cloud.google.com
                        3. If this persists, you may need to:
                           - Upgrade your API plan
                           - Use a different API key
                           - Wait for quota reset

                        **Note:** This shouldn't happen during upload.
                        Try reloading the page (F5) if it persists.
                        """)
                    else:
                        st.error(f"""
                        ❌ **Error Processing Document**

                        {error_msg}

                        **Try:**
                        - Reload the page (F5)
                        - Ensure PDF/TXT file is valid
                        - Try a smaller file
                        - Check file isn't corrupted
                        """)

    # Display uploaded documents (outside expander)
    if st.session_state.uploaded_documents:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**📁 {len(st.session_state.uploaded_documents)} Document(s) Loaded**")

        doc_names = list(st.session_state.uploaded_documents.keys())
        with col2:
            selected_doc = st.selectbox(
                "Select",
                doc_names,
                index=doc_names.index(st.session_state.current_document) if st.session_state.current_document in doc_names else 0,
                key="doc_selector",
                label_visibility="collapsed"
            )
            st.session_state.current_document = selected_doc

        with col3:
            if len(doc_names) > 1:
                if st.checkbox("Compare", key="compare_mode", label_visibility="collapsed"):
                    st.session_state.comparison_docs = st.multiselect(
                        "Docs",
                        doc_names,
                        default=st.session_state.comparison_docs,
                        key="comparison_selector",
                        label_visibility="collapsed"
                    )

    # Action buttons
    if st.session_state.uploaded_documents:
        col_actions = st.columns([1, 1, 1])

        with col_actions[0]:
            if st.button("🔄 New Chat", use_container_width=True, help="Clear chat and start fresh"):
                st.session_state.messages = []
                st.rerun()

        with col_actions[1]:
            if st.button("📤 New Document", use_container_width=True, help="Upload another document"):
                st.session_state.uploaded_documents = {}
                st.session_state.current_document = None
                st.session_state.messages = []
                st.rerun()

        with col_actions[2]:
            if st.button("🗑️ Clear All", use_container_width=True, help="Remove all documents"):
                st.session_state.uploaded_documents = {}
                st.session_state.current_document = None
                st.session_state.messages = []
                st.session_state.comparison_docs = []
                st.rerun()

    # Chat messages container
    st.markdown("---")
    messages_container = st.container()

    with messages_container:
        if not st.session_state.messages and not st.session_state.uploaded_documents:
            st.info("💡 Upload a financial document to get started!")
        else:
            # Display existing messages
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

                    if message["role"] == "assistant" and "metadata" in message:
                        with st.expander("📋 Details"):
                            meta = message["metadata"]
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Agent", meta.get("agent", "N/A"))
                            with col2:
                                st.metric("Time", f"{meta.get('time', 0):.1f}s")
                            with col3:
                                st.metric("Cached", "✅ Yes" if meta.get("cached") else "No")

                            if meta.get("sources"):
                                st.markdown("**Sources:**")
                                for src in meta["sources"]:
                                    st.caption(f"📄 {src}")

    # Show helpful tips for multi-document comparison
    if len(st.session_state.uploaded_documents) > 1:
        st.info(
            "💡 **Tip:** Try asking: *'Compare the revenue'* for automatic comparison!"
        )

    # Chat input
    if st.session_state.current_document:
        question = st.chat_input(placeholder=f"Ask about {st.session_state.current_document}...")
    else:
        question = st.chat_input(placeholder="Ask a financial question...")

    if "demo_query" in st.session_state and not question:
        question = st.session_state.demo_query
        del st.session_state.demo_query

    # Process question
    if question:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": question})

        with st.chat_message("user"):
            st.markdown(question)

        # Check if it's an investment question
        if detect_investment_question(question):
            with st.chat_message("assistant"):
                investment_response = get_investment_response(question)
                st.markdown(investment_response["answer"])

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": investment_response["answer"],
                    "metadata": {
                        "agent": "human_approval",
                        "requires_approval": True,
                    }
                })

        elif not st.session_state.api_key_set:
            st.error("❌ API key not configured. Set it in the sidebar first!")

        else:
            with st.chat_message("assistant"):
                # Check if comparing multiple documents
                comparing = st.session_state.get("compare_mode", False) and len(st.session_state.comparison_docs) > 1

                # If document is uploaded, use simple document Q&A
                if st.session_state.current_document and st.session_state.uploaded_documents:
                    placeholder = st.empty()
                    with placeholder.container():
                        if comparing:
                            st.spinner("📊 Comparing documents...")
                        else:
                            st.spinner("🔍 Analyzing document...")

                    try:
                        start_time = time.perf_counter()

                        doc_data = st.session_state.uploaded_documents[st.session_state.current_document]
                        doc_text = doc_data["text"]
                        doc_name = doc_data["metadata"]["file_name"]

                        # Check cache first
                        cache_key = f"{doc_name}:{question}"
                        cached = get_cached_response(cache_key)

                        if cached:
                            placeholder.empty()
                            st.markdown(cached["answer"])
                            st.info("✅ Cached result")

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": cached["answer"],
                                "metadata": {
                                    "agent": cached.get("agent", "cached"),
                                    "time": 0.1,
                                    "cached": True,
                                    "sources": [doc_name],
                                }
                            })
                        else:
                            # Use parallel agents workflow with document context
                            try:
                                result = st.session_state.workflow.invoke(
                                    {
                                        "messages": [HumanMessage(content=f"Based on {doc_name}: {question}")],
                                        "question": question,
                                        "document_context": doc_text[:5000],
                                    },
                                    config={"configurable": {"thread_id": f"doc_chat_{doc_name}"}},
                                )

                                execution_time = time.perf_counter() - start_time

                                answer = result.get("answer", "No answer generated.")
                                agent = result.get("agent", "retrieval_agent")
                                sources = [doc_name] + result.get("sources", [])

                                # Cache the response
                                cache_response(cache_key, {
                                    "answer": answer,
                                    "agent": agent,
                                    "sources": sources,
                                })

                                placeholder.empty()
                                st.markdown(answer)

                                with st.expander("📋 Details"):
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Agent", agent)
                                    with col2:
                                        st.metric("Time", f"{execution_time:.1f}s")
                                    with col3:
                                        st.metric("Sources", len(sources))

                                    if sources:
                                        st.markdown("**Retrieved from:**")
                                        for src in sources:
                                            st.caption(f"📄 {src}")

                                # Cache and store response
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": answer,
                                    "metadata": {
                                        "agent": agent,
                                        "time": execution_time,
                                        "cached": False,
                                        "sources": sources,
                                    }
                                })

                            except Exception as workflow_error:
                                placeholder.empty()
                                error_msg = str(workflow_error)

                                if "rate" in error_msg.lower():
                                    st.error("""
                                    🚫 **API Rate Limit Exceeded**

                                    The parallel agent workflow hit the API rate limit.

                                    **Why this happens:**
                                    - Free tier has low limits (~60 req/min)
                                    - 6 parallel agents = 6 API calls at once
                                    - Even fresh API key hits limit quickly

                                    **Solutions:**
                                    1. ⏳ **Wait 30 seconds and retry** (quota recovers)
                                    2. 💳 **Upgrade to Paid API** (~$5-20):
                                       - Go to console.cloud.google.com
                                       - Add billing
                                       - Get 600+ requests/minute
                                       - Parallel agents work perfectly
                                    3. 🔑 **Create new API key** (temporary):
                                       - Creates new project with fresh quota
                                       - Works for a few hours

                                    **For Capstone Demo:**
                                    Upgrading to paid tier is recommended to show
                                    parallel execution working as designed.
                                    """)
                                else:
                                    st.error(f"Error: {error_msg[:100]}")

                    except Exception as e:
                        placeholder.empty()
                        error_msg = str(e)
                        if "rate" in error_msg.lower():
                            st.error("⚠️ API rate limit. Please wait a moment and try again.")
                        else:
                            st.error(f"Error: {error_msg[:100]}")

                # Or use regular workflow for general questions
                else:
                    cached = get_cached_response(question)

                    if cached:
                        st.markdown(cached["answer"])
                        st.info("✅ Cached response (faster)")

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": cached["answer"],
                            "metadata": {
                                "agent": cached.get("agent", "cached"),
                                "time": 0.1,
                                "cached": True,
                                "sources": cached.get("sources", []),
                            }
                        })
                    else:
                        placeholder = st.empty()
                        with placeholder.container():
                            st.spinner("⏳ Analyzing... (may take 10-30 seconds)")

                        try:
                            start_time = time.perf_counter()

                            result = st.session_state.workflow.invoke(
                                {
                                    "messages": [HumanMessage(content=question)],
                                    "question": question,
                                },
                                config={"configurable": {"thread_id": "financial_chat"}},
                            )

                            execution_time = time.perf_counter() - start_time

                            answer = result.get("answer", "No answer generated.")
                            agent = result.get("agent", "unknown")
                            sources = result.get("sources", [])

                            # Cache the response
                            cache_response(question, {
                                "answer": answer,
                                "agent": agent,
                                "sources": sources,
                            })

                            # Display answer
                            placeholder.empty()
                            st.markdown(answer)

                            # Show details
                            with st.expander("📋 Details"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Agent", agent)
                                with col2:
                                    st.metric("Time", f"{execution_time:.1f}s")
                                with col3:
                                    st.metric("Sources", len(sources))

                                if sources:
                                    st.markdown("**Retrieved from:**")
                                    for src in sources:
                                        st.caption(f"📄 {src}")

                            # Store in session
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": answer,
                                "metadata": {
                                    "agent": agent,
                                    "time": execution_time,
                                    "cached": False,
                                    "sources": sources,
                                }
                            })

                        except Exception as e:
                            placeholder.empty()
                            error_msg = str(e)

                            if "rate" in error_msg.lower():
                                st.error("""
                                ⚠️ **API Rate Limit Exceeded**

                                The Google Gemini API rate limit has been reached.

                                **Solutions:**
                                1. Wait a few minutes and try again
                                2. Check your API quota at console.cloud.google.com
                                3. Use cached responses (available for previous queries)
                                4. Try simpler questions

                                Try asking about cached information or come back in a few minutes.
                                """)
                            else:
                                st.error(f"""
                                ❌ **Error Processing Question**

                                {error_msg}

                                **Try:**
                                - Rephrasing your question
                                - Waiting a moment and retrying
                                - Checking your API key
                                """)


# ============================================================
# TAB 2: DOCUMENTS
# ============================================================

with tab2:
    st.header("📄 Document Management")

    st.subheader("Sample Documents")

    data_dir = Path("data")
    documents = []

    for ext in ["*.pdf", "*.txt"]:
        documents.extend(data_dir.glob(f"**/{ext}"))

    if documents:
        st.write(f"Found {len(documents)} document(s)")

        for doc_path in sorted(documents):
            with st.expander(f"📄 {doc_path.name}"):
                try:
                    file_size = doc_path.stat().st_size / 1024
                    st.caption(f"Size: {file_size:.1f} KB")

                    if doc_path.suffix.lower() == ".pdf":
                        try:
                            reader = PdfReader(doc_path)
                            st.info(f"📑 {len(reader.pages)} pages")

                            page_num = st.slider(
                                "Select page",
                                1,
                                len(reader.pages),
                                1,
                                key=f"pdf_{doc_path.name}"
                            )

                            page = reader.pages[page_num - 1]
                            text = page.extract_text()

                            if text:
                                st.text_area("Content", text, height=300, disabled=True)
                            else:
                                st.warning("Could not extract text from this page")
                        except Exception as e:
                            st.error(f"Error reading PDF: {str(e)[:100]}")

                    elif doc_path.suffix.lower() == ".txt":
                        with open(doc_path, "r") as f:
                            content = f.read()

                        if len(content) > 2000:
                            st.text_area("Preview (first 2000 chars)", content[:2000], height=300, disabled=True)
                        else:
                            st.text_area("Content", content, height=300, disabled=True)

                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        st.info("No documents found in data/ folder")


# ============================================================
# TAB 3: HELP
# ============================================================

with tab3:
    st.header("❓ Help & Documentation")

    with st.expander("🎯 How to Use", expanded=True):
        st.markdown("""
        ### Using with Financial Documents:
        1. **Upload Documents**: Use the file uploader at the top of Chat tab
        2. **Select Document**: Choose which document to analyze
        3. **Ask Questions**: Type questions about the document
        4. **View Results**: Get AI-generated answers with source attribution
        5. **Compare Documents**: Upload multiple documents and use Compare feature

        ### For General Financial Q&A:
        1. **Set API Key**: Enter your Google Gemini API key in the sidebar
        2. **Ask Questions**: Type a financial question in the chat
        3. **View Results**: Get instant answers with sources
        4. **Use Cache**: Previously answered questions load instantly

        **Supported Formats:**
        - PDF files (.pdf)
        - Text files (.txt)

        **Example Questions:**
        - "What are the main financial metrics?" (about uploaded document)
        - "What was the revenue growth?" (general financial Q&A)
        - "What are the key risks?"
        - "Compare these two reports"
        """)

    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        **Rate Limit Error:**
        - Wait a few minutes
        - Check API quota at console.cloud.google.com
        - Try simpler questions

        **Document Won't Load:**
        - Ensure PDF/TXT format
        - Try a smaller file
        - Check file isn't corrupted

        **No Response:**
        - Check API key is set correctly
        - Check internet connection
        - Try a cached question first

        **Agent Errors:**
        - Reload the page
        - Clear cache in sidebar
        - Try rephrasing your question
        """)

    with st.expander("📚 About This System"):
        st.markdown("""
        **Financial RAG Assistant**

        A multi-agent AI system for intelligent Q&A over financial documents.

        **Key Features:**
        - 6 specialized agents working in parallel
        - Retrieval-Augmented Generation (RAG) for accuracy
        - Document upload & analysis
        - Multi-document comparison
        - Response caching for speed
        - Rate limit handling
        - Investment question flagging

        **Technology Stack:**
        - LangGraph (orchestration)
        - Google Gemini (LLM)
        - FAISS (vector search)
        - Streamlit (UI)
        - Python (backend)
        """)
