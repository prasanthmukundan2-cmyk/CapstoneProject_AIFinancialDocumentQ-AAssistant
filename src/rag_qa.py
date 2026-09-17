import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.rag_pipeline import get_retriever


load_dotenv()


def ask_question(question: str):
    print("Loading retriever...")
    retriever = get_retriever()

    print("Retrieving relevant documents...")
    documents = retriever.invoke(question)

    context = "\n\n".join(
        document.page_content for document in documents
    )

    prompt = ChatPromptTemplate.from_template(
        """
You are a financial analysis assistant.

Answer the question using only the provided financial documents.
If the answer is not available in the documents, say:
"I could not find that information in the provided documents."

Do not invent numbers or facts.

Financial documents:
{context}

Question:
{question}

Answer:
"""
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        temperature=0
    )

    chain = prompt | llm | StrOutputParser()

    answer = chain.invoke({
        "context": context,
        "question": question
    })

    return answer


if __name__ == "__main__":
    question = input("Enter your financial question: ")

    answer = ask_question(question)

    print("\nAnswer:")
    print(answer)