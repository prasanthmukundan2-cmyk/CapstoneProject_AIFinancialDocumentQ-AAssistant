import time
import os
import json
from pathlib import Path
from datetime import datetime

import streamlit as st
from langchain_core.messages import HumanMessage
from pypdf import PdfReader

from src.workflow_optimized import create_optimized_workflow
from src.cache_manager import get_cached_response, cache_response, clear_cache
from src.simple_investment import detect_investment_question, get_investment_response
from src.document_processor import process_upload
from src.document_creator import (
    detect_document_creation_request,
    get_document_creation_response,
    create_document_approval_message,
    save_approved_document,
    detect_approval_response,
)
from src.retry_utils import invoke_with_retry
from src.agents_fixed import get_llm, _extract_text
from src.rag_pipeline import rebuild_vectorstore
from src.conversation_manager import (
    create_conversation,
    create_conversation_id,
    generate_title_from_question,
    update_conversation_timestamp,
)


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

    /* Chat input styling - ensure it stays at bottom */
    .stChatInputContainer {
        background-color: #0e1117 !important;
        border-top: 1px solid #444 !important;
        border-radius: 8px;
        padding: 1rem !important;
        margin: 1rem 0 0 0 !important;
    }

    .stChatInputContainer input {
        border-radius: 8px !important;
        border: 1px solid #444 !important;
        background-color: #161b22 !important;
        color: #c9d1d9 !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

if "workflow" not in st.session_state:
    st.session_state.workflow = create_optimized_workflow()

# Document state (shared across all conversations)
if "uploaded_documents" not in st.session_state:
    st.session_state.uploaded_documents = {}

if "current_document" not in st.session_state:
    st.session_state.current_document = None

if "comparison_docs" not in st.session_state:
    st.session_state.comparison_docs = []

# Conversation state (one conversation at a time)
if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "current_conversation_id" not in st.session_state:
    # Create initial conversation
    initial_conv = create_conversation("Conversation 1")
    st.session_state.conversations[initial_conv["id"]] = initial_conv
    st.session_state.current_conversation_id = initial_conv["id"]

# API key state
if "api_key_set" not in st.session_state:
    st.session_state.api_key_set = bool(os.getenv("GOOGLE_API_KEY"))

# Document creation/approval state
if "pending_document" not in st.session_state:
    st.session_state.pending_document = None

if "pending_document_question" not in st.session_state:
    st.session_state.pending_document_question = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("⚙️ Settings & Conversations")

    # ========== CONVERSATION MANAGEMENT ==========
    st.subheader("💬 Conversations")

    # New Chat Button
    if st.button("➕ New Chat", use_container_width=True, key="new_chat_sidebar"):
        # Create new conversation
        new_conv = create_conversation("Conversation " + str(len(st.session_state.conversations) + 1))
        st.session_state.conversations[new_conv["id"]] = new_conv
        st.session_state.current_conversation_id = new_conv["id"]

        # Clear all document state
        st.session_state.uploaded_documents = {}
        st.session_state.current_document = None
        st.session_state.comparison_docs = []
        st.session_state.show_comparison = False

        # Reset file uploader widget key to clear its cache
        if "uploader_key" not in st.session_state:
            st.session_state.uploader_key = 0
        st.session_state.uploader_key += 1

        # Clean up uploaded files from disk
        import shutil
        uploaded_dir = Path("data/uploaded")
        if uploaded_dir.exists():
            try:
                shutil.rmtree(uploaded_dir)
                uploaded_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Error clearing uploaded directory: {e}")

        st.rerun()

    st.divider()

    # List conversations
    if st.session_state.conversations:
        st.markdown("**Your Conversations:**")

        for conv_id, conv in sorted(
            st.session_state.conversations.items(),
            key=lambda x: x[1].get("updated_at", ""),
            reverse=True
        ):
            is_active = conv_id == st.session_state.current_conversation_id

            # Create a clickable conversation item
            col1, col2 = st.columns([4, 1])

            with col1:
                title_display = conv.get("title", "Untitled")
                msg_count = len(conv.get("messages", []))
                display_text = f"{title_display}"
                if msg_count > 0:
                    display_text += f" ({msg_count})"

                if st.button(
                    display_text,
                    use_container_width=True,
                    key=f"conv_{conv_id}",
                    help=f"Switch to this conversation"
                ):
                    st.session_state.current_conversation_id = conv_id
                    st.rerun()

    st.divider()

    # ========== API KEY STATUS ==========
    st.subheader("🔑 API Configuration")
    if os.getenv("GOOGLE_API_KEY"):
        st.success("✅ API key configured from .env file")
        st.session_state.api_key_set = True
    else:
        st.error("❌ No API key found. Please set GOOGLE_API_KEY in your .env file")
        st.session_state.api_key_set = False

    st.divider()

    # ========== CACHE MANAGEMENT ==========
    st.subheader("💾 Cache Management")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear Cache"):
            clear_cache()
            st.success("Cache cleared!")

    current_conv = st.session_state.conversations.get(st.session_state.current_conversation_id, {})
    msg_count = len(current_conv.get("messages", []))
    with col2:
        st.caption(f"Messages: {msg_count}")

    st.divider()

    # ========== INFO ==========
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
            # Initialize uploader key if not exists
            if "uploader_key" not in st.session_state:
                st.session_state.uploader_key = 0

            uploaded_file = st.file_uploader(
                "Choose document(s) (PDF, TXT, Excel, or CSV)",
                type=["pdf", "txt", "xlsx", "xls", "csv"],
                key=f"chat_uploader_{st.session_state.uploader_key}",
                help="Upload financial documents (PDF, TXT, Excel, or CSV files) to ask questions about them"
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

    # Check if using fallback files
    uploaded_dir = Path("data/uploaded")
    is_using_fallback = not (uploaded_dir.exists() and len(list(uploaded_dir.glob("*"))) > 0)

    if is_using_fallback and not st.session_state.uploaded_documents:
        st.info("📚 **Using sample files from data/ folder** | Upload your own files to analyze your documents", icon="ℹ️")

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
        col_actions = st.columns([1, 1])

        with col_actions[0]:
            if st.button("📤 New Document", use_container_width=True, help="Upload another document"):
                st.session_state.uploaded_documents = {}
                st.session_state.current_document = None
                st.session_state.comparison_docs = []
                st.session_state.show_comparison = False

                # Clean up uploaded files from disk
                import shutil
                uploaded_dir = Path("data/uploaded")
                if uploaded_dir.exists():
                    try:
                        shutil.rmtree(uploaded_dir)
                        uploaded_dir.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        print(f"Error clearing uploaded directory: {e}")

                st.rerun()

        with col_actions[1]:
            if st.button("🗑️ Clear All", use_container_width=True, help="Remove all documents"):
                st.session_state.uploaded_documents = {}
                st.session_state.current_document = None
                st.session_state.comparison_docs = []
                st.session_state.show_comparison = False

                # Clean up uploaded files from disk
                import shutil
                uploaded_dir = Path("data/uploaded")
                if uploaded_dir.exists():
                    try:
                        shutil.rmtree(uploaded_dir)
                        uploaded_dir.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        print(f"Error clearing uploaded directory: {e}")

                st.rerun()

    # Get current conversation
    current_conv = st.session_state.conversations[st.session_state.current_conversation_id]

    # Messages display area
    st.markdown("---")

    if not current_conv["messages"] and not st.session_state.uploaded_documents:
        st.info("💡 Upload a financial document to get started!")
    else:
        # Display existing messages
        for message in current_conv["messages"]:
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

    # Chat input (appears at bottom of page)
    if st.session_state.current_document:
        question = st.chat_input(placeholder=f"Ask about {st.session_state.current_document}...")
    else:
        question = st.chat_input(placeholder="Ask a financial question...")

    if "demo_query" in st.session_state and not question:
        question = st.session_state.demo_query
        del st.session_state.demo_query

    # Process question
    if question:
        # Get current conversation reference
        current_conv = st.session_state.conversations[st.session_state.current_conversation_id]

        # Generate title from first question if not set
        if not current_conv["messages"] and current_conv["title"].startswith("Conversation"):
            current_conv["title"] = generate_title_from_question(question)

        # Add user message
        current_conv["messages"].append({"role": "user", "content": question})
        update_conversation_timestamp(current_conv)

        with st.chat_message("user"):
            st.markdown(question)

        # Check if it's a document creation request
        if detect_document_creation_request(question):
            with st.chat_message("assistant"):
                # Generate the document
                document_content = ""

                if st.session_state.current_document and st.session_state.uploaded_documents:
                    with st.spinner("📝 Generating document..."):
                        try:
                            doc_data = st.session_state.uploaded_documents[st.session_state.current_document]
                            doc_text = doc_data["text"]
                            doc_name = doc_data["metadata"]["file_name"]

                            # Get LLM to generate document
                            llm = get_llm()
                            from src.context import build_context

                            # Build context for document creation
                            context = build_context(question, doc_text)

                            # Generate document using LLM
                            from src.document_creator import get_document_creation_prompt
                            prompt = get_document_creation_prompt(question, context)

                            response = llm.invoke(prompt)
                            document_content = response.content if hasattr(response, 'content') else str(response)

                        except Exception as e:
                            document_content = f"Error generating document: {str(e)[:200]}"

                if document_content:
                    # Display the generated document
                    st.markdown("### 📄 Generated Document")
                    st.markdown("---")
                    st.markdown(document_content)
                    st.markdown("---")

                    # Store in session for approval
                    st.session_state.pending_document = document_content
                    st.session_state.pending_document_question = question

                    # Display approval message
                    approval_response = get_document_creation_response(question)
                    st.markdown("""
### 🔐 DOCUMENT APPROVAL REQUIRED

A financial document has been generated based on your KPI data and company analysis.

**Please Review:**
- Does the content accurately reflect your data?
- Are the metrics and insights correct?
- Is the formatting professional?

**Next Steps:**
1. Review the document above
2. To approve: Reply with "Approve" or "Yes"
3. To reject/revise: Reply with "Reject" or describe changes

The document will be saved only after your approval.
                    """)

                    current_conv["messages"].append({
                        "role": "assistant",
                        "content": document_content + "\n\n[AWAITING DOCUMENT APPROVAL]",
                        "metadata": {
                            "agent": "document_creator",
                            "requires_approval": True,
                            "document_content": document_content,
                        }
                    })
                    update_conversation_timestamp(current_conv)
                else:
                    st.error("❌ No document loaded. Please upload a document first.")

        # Check if user is responding to document approval
        elif st.session_state.get("pending_document"):
            approval_status = detect_approval_response(question)

            if approval_status == "approve":
                with st.chat_message("assistant"):
                    # Save the approved document
                    doc_name = st.session_state.current_document.replace(".pdf", "").replace(".txt", "").replace(".csv", "").replace(".xlsx", "").replace(".xls", "")
                    filename = f"{doc_name}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

                    success, path = save_approved_document(filename, st.session_state.pending_document)

                    if success:
                        st.success(f"✅ Document approved and saved!")
                        st.info(f"📁 Saved to: `{path}`")

                        current_conv["messages"].append({
                            "role": "assistant",
                            "content": f"✅ Document approved and saved to {path}",
                            "metadata": {
                                "agent": "document_creator",
                                "action": "document_saved",
                                "file_path": path,
                            }
                        })
                    else:
                        st.error(f"❌ Error saving document: {path}")

                    # Clear pending document
                    st.session_state.pending_document = None
                    st.session_state.pending_document_question = None
                    update_conversation_timestamp(current_conv)

            elif approval_status == "reject":
                with st.chat_message("assistant"):
                    st.warning("❌ Document rejected. Please provide details on what to change:")
                    current_conv["messages"].append({
                        "role": "assistant",
                        "content": "Document rejected. Please specify what changes are needed.",
                        "metadata": {
                            "agent": "document_creator",
                            "action": "document_rejected",
                        }
                    })
                    st.session_state.pending_document = None
                    update_conversation_timestamp(current_conv)

        # Check if it's an investment question
        elif detect_investment_question(question):
            with st.chat_message("assistant"):
                # First, analyze the document if available
                analysis = ""
                suggestion = ""

                if st.session_state.current_document and st.session_state.uploaded_documents:
                    with st.spinner("📊 Analyzing company for investment assessment..."):
                        try:
                            doc_data = st.session_state.uploaded_documents[st.session_state.current_document]
                            doc_text = doc_data["text"]
                            doc_name = doc_data["metadata"]["file_name"]

                            # Get company analysis
                            result = st.session_state.workflow.invoke(
                                {
                                    "messages": [HumanMessage(content=f"Based on {doc_name}, provide a brief investment analysis. Include: 1) Company overview, 2) Financial health, 3) Key risks, 4) Investment potential")],
                                    "question": question,
                                    "document_context": doc_text[:5000],
                                },
                                config={"configurable": {"thread_id": f"investment_{doc_name}"}},
                            )

                            analysis = result.get("answer", "Unable to generate analysis")

                        except Exception as e:
                            analysis = f"Could not analyze document: {str(e)[:100]}"

                # Display analysis if available
                if analysis:
                    st.markdown("### 📊 Company Analysis")
                    st.markdown(analysis)
                    st.markdown("---")

                # Display human approval message
                approval_message = """
### 🔐 HUMAN APPROVAL REQUIRED

This is an **investment-related question** that requires human review.

**⚠️ Important:** This system cannot provide direct investment advice. The analysis above is for informational purposes only.

**What Happens Next:**
1. Your question and analysis have been flagged for review
2. A qualified financial analyst will examine this request
3. You will receive guidance within 24 hours
4. You will be notified when the review is complete

**Disclaimer:** Always consult with a qualified financial advisor before making investment decisions.
                """
                st.markdown(approval_message)

                current_conv["messages"].append({
                    "role": "assistant",
                    "content": (analysis + "\n\n" + approval_message) if analysis else approval_message,
                    "metadata": {
                        "agent": "investment_analysis",
                        "requires_approval": True,
                        "analysis_provided": bool(analysis),
                    }
                })
                update_conversation_timestamp(current_conv)

        elif not st.session_state.api_key_set:
            st.error("❌ API key not configured. Please set GOOGLE_API_KEY in your .env file")

        else:
            with st.chat_message("assistant"):
                # Check if comparing multiple documents
                comparing = st.session_state.get("compare_mode", False) and len(st.session_state.comparison_docs) > 1

                # If document is uploaded, use simple document Q&A
                if st.session_state.current_document and st.session_state.uploaded_documents:
                    if comparing:
                        status_text = "📊 Comparing documents..."
                    else:
                        status_text = "🔍 Analyzing document..."

                    with st.spinner(status_text):
                        try:
                            start_time = time.perf_counter()

                            doc_data = st.session_state.uploaded_documents[st.session_state.current_document]
                            doc_text = doc_data["text"]
                            doc_name = doc_data["metadata"]["file_name"]

                            # Check cache first
                            cache_key = f"{doc_name}:{question}"
                            cached = get_cached_response(cache_key)

                            if cached:
                                st.markdown(cached["answer"])
                                st.info("✅ Cached result")

                                current_conv["messages"].append({
                                    "role": "assistant",
                                    "content": cached["answer"],
                                    "metadata": {
                                        "agent": cached.get("agent", "cached"),
                                        "time": 0.1,
                                        "cached": True,
                                        "sources": [doc_name],
                                    }
                                })
                                update_conversation_timestamp(current_conv)
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
                                    current_conv["messages"].append({
                                        "role": "assistant",
                                        "content": answer,
                                        "metadata": {
                                            "agent": agent,
                                            "time": execution_time,
                                            "cached": False,
                                            "sources": sources,
                                        }
                                    })
                                    update_conversation_timestamp(current_conv)

                                except Exception as workflow_error:
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

                        current_conv["messages"].append({
                            "role": "assistant",
                            "content": cached["answer"],
                            "metadata": {
                                "agent": cached.get("agent", "cached"),
                                "time": 0.1,
                                "cached": True,
                                "sources": cached.get("sources", []),
                            }
                        })
                        update_conversation_timestamp(current_conv)
                    else:
                        with st.spinner("⏳ Analyzing... (may take 10-30 seconds)"):
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

                                # Store in conversation
                                current_conv["messages"].append({
                                    "role": "assistant",
                                    "content": answer,
                                    "metadata": {
                                        "agent": agent,
                                        "time": execution_time,
                                        "cached": False,
                                        "sources": sources,
                                    }
                                })
                                update_conversation_timestamp(current_conv)

                            except Exception as e:
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
