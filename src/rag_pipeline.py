import os
from functools import lru_cache

from dotenv import load_dotenv

from langchain_community.document_loaders import (
    PyPDFLoader,
    CSVLoader,
)
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters.character import RecursiveCharacterTextSplitter


load_dotenv()


VECTOR_DB_DIR = "data/vector_db"
UPLOADED_DIR = "data/uploaded"
FALLBACK_PDF = "data/annual_report.pdf"
FALLBACK_CSV = "data/balance_sheet.csv"


def get_latest_uploaded_file():
    """Get the most recently uploaded PDF or TXT file"""
    if not os.path.exists(UPLOADED_DIR):
        return None

    files = [
        os.path.join(UPLOADED_DIR, f)
        for f in os.listdir(UPLOADED_DIR)
        if f.lower().endswith(('.pdf', '.txt'))
    ]

    if not files:
        return None

    # Return most recently modified file
    return max(files, key=os.path.getmtime)


@lru_cache(maxsize=1)
def get_embeddings():
    """
    Create the embedding model once and reuse it.
    """

    return GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001"
    )


def build_vector_store():
    """
    Load ALL documents (uploaded + fallback) for multi-document comparison!
    """

    documents = []

    # Load ALL uploaded files (enables comparison!)
    if os.path.exists(UPLOADED_DIR):
        uploaded_files = [
            os.path.join(UPLOADED_DIR, f)
            for f in os.listdir(UPLOADED_DIR)
            if f.lower().endswith(('.pdf', '.txt'))
        ]

        for file_path in uploaded_files:
            try:
                if file_path.lower().endswith('.pdf'):
                    docs = PyPDFLoader(file_path).load()
                    for doc in docs:
                        doc.metadata["source_file"] = os.path.basename(file_path)
                    documents.extend(docs)
                    print(f"✓ Loaded: {os.path.basename(file_path)}")
                elif file_path.lower().endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        from langchain_core.documents import Document
                        doc = Document(
                            page_content=f.read(),
                            metadata={"source_file": os.path.basename(file_path)}
                        )
                        documents.append(doc)
                        print(f"✓ Loaded: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

    # Fallback to sample files if no uploads
    if not documents:
        print("No uploaded files, using fallback...")
        if os.path.exists(FALLBACK_PDF):
            docs = PyPDFLoader(FALLBACK_PDF).load()
            for doc in docs:
                doc.metadata["source_file"] = os.path.basename(FALLBACK_PDF)
            documents.extend(docs)

        if os.path.exists(FALLBACK_CSV):
            docs = CSVLoader(FALLBACK_CSV).load()
            for doc in docs:
                doc.metadata["source_file"] = os.path.basename(FALLBACK_CSV)
            documents.extend(docs)

    if not documents:
        raise FileNotFoundError(
            "No documents found. Please upload a file or ensure sample files exist."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = splitter.split_documents(documents)

    if not chunks:
        raise ValueError("Document splitting produced no chunks.")

    embeddings = get_embeddings()

    vectorstore = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings,
    )

    os.makedirs(VECTOR_DB_DIR, exist_ok=True)

    vectorstore.save_local(VECTOR_DB_DIR)

    return vectorstore


@lru_cache(maxsize=1)
def get_vectorstore():
    """
    Load the FAISS vector database once.
    """

    if not os.path.exists(VECTOR_DB_DIR):
        # Build if doesn't exist
        return build_vector_store()

    return FAISS.load_local(
        VECTOR_DB_DIR,
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )


def rebuild_vectorstore():
    """
    Rebuild the vector database from uploaded files.
    Call this when a new file is uploaded.
    """
    # Clear cache
    get_vectorstore.cache_clear()

    # Delete old vector DB
    if os.path.exists(VECTOR_DB_DIR):
        import shutil
        shutil.rmtree(VECTOR_DB_DIR)

    # Build new one
    build_vector_store()

    print("✅ Vector database rebuilt successfully!")


def get_retriever():
    """
    Return the document retriever.
    """

    vectorstore = get_vectorstore()

    return vectorstore.as_retriever(
        search_kwargs={"k": 3}
    )


if __name__ == "__main__":
    build_vector_store()
    print("Vector database created successfully.")