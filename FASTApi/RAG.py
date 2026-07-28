import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_text_splitters import CharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

# ── vehicle knowledge base ─────────────────────
VEHICLE_DATA = """
Vehicle: Car
Type: car
Wheels: 4
Seats: 5
Fuel: petrol
Best for: groups, long distance, family trips
Price: moderate

Vehicle: Bike
Type: bike
Wheels: 2
Seats: 2
Fuel: petrol
Best for: short distance, budget travel, city commute
Price: cheap

Vehicle: Truck
Type: truck
Wheels: 6
Seats: 2
Fuel: diesel
Best for: heavy loads, moving furniture, large cargo
Price: expensive

Vehicle: Electric Car
Type: electriccar
Wheels: 4
Seats: 5
Fuel: electric
Best for: eco friendly travel, green, environment conscious
Price: moderate

Vehicle: Scooter
Type: scooter
Wheels: 2
Seats: 1
Fuel: electric
Best for: solo city rides, cheapest option, short distance
Price: very cheap
"""

# ── build vector store ─────────────────────────
def build_vector_store():
    splitter = CharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=20
    )
    chunks = splitter.split_text(VEHICLE_DATA)

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    vector_store = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    return vector_store

# ── build RAG chain ────────────────────────────
def build_rag_chain():
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile"
    )

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    vector_store = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )

    retriever = vector_store.as_retriever(
        search_kwargs={"k": 5}
    )

    prompt = ChatPromptTemplate.from_template("""
    You are a vehicle rental assistant.
    Answer the question based on the context below.
    If you don't know, say you don't know.

    Context: {context}
    Question: {question}

    Answer:
    """)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain

# ── initialize ─────────────────────────────────
print("building vector store...")
build_vector_store()
print("vector store ready ✓")

rag_chain = build_rag_chain()
print("RAG chain ready ✓")

# ── test ───────────────────────────────────────
if __name__ == "__main__":
    questions = [
        "Which vehicle is cheapest?",
        "What is best for moving furniture?",
        "Which vehicle is eco friendly?",
        "How many seats does truck have?",
    ]

    for q in questions:
        print(f"\nQ: {q}")
        answer = rag_chain.invoke(q)
        print(f"A: {answer}")