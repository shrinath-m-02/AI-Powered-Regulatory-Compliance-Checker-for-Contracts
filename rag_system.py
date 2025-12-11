# ---------- 1️⃣ Imports ----------
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from groq import Groq   # ✅ Use Groq for LLM

# ---------- 2️⃣ Load environment ----------
load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ---------- 3️⃣ Load Compliance Dataset ----------
def load_compliance_data(pdf_path):
    print("📄 Loading compliance dataset from PDF...")
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    print(f"✅ Loaded {len(documents)} pages from {pdf_path}")
    return documents

# ---------- 4️⃣ Split into Chunks ----------
def split_documents(documents):
    print("✂️ Splitting documents into smaller chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    print(f"✅ Split into {len(chunks)} chunks")
    return chunks

# ---------- 5️⃣ Create or Load FAISS Vector Store ----------
def create_vector_store(chunks, db_path="faiss_index"):
    if os.path.exists(db_path):
        print(f"📂 Loading existing FAISS index from '{db_path}'...")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        return FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
    
    print("⚙️ Creating embeddings and FAISS vector store...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(db_path)
    print(f"✅ Vector store saved at '{db_path}'")
    return vectorstore

# ---------- 6️⃣ Load the Contract ----------
def load_contract(contract_path):
    print("📑 Loading contract file...")
    if contract_path.lower().endswith(".pdf"):
        loader = PyPDFLoader(contract_path)
        docs = loader.load()
        contract_text = " ".join([doc.page_content for doc in docs])
    else:
        loader = TextLoader(contract_path)
        docs = loader.load()
        contract_text = " ".join([doc.page_content for doc in docs])
    print("✅ Contract loaded successfully.")
    return contract_text

# ---------- 7️⃣ Analyze Contract with Groq ----------
def analyze_contract(client, vectorstore, contract_text):
    print("🔍 Analyzing contract against compliance standards...")

    # Step 1: Retrieve most relevant compliance info
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    relevant_docs = retriever.invoke(contract_text)
    context = "\n\n".join([doc.page_content for doc in relevant_docs])

    # Step 2: Build the prompt for Groq LLM
    prompt = f"""
You are a compliance analyst specializing in HR and legal contracts.

Use the following HR compliance standards and the provided contract to:
1. Extract key clauses present in the contract.
2. Identify missing, weak, or non-compliant clauses as potential compliance issues.
3. Assign a risk level (Low, Medium, or High) and give a short reason for each issue.

--- Compliance Reference ---
{context}

--- Contract Text ---
{contract_text}

Return your answer in this exact structure:

KEY CLAUSES:
- ...

POTENTIAL COMPLIANCE ISSUES:
- ... (Risk Level: ...)
Reason:
"""

    # Step 3: Ask the Groq LLM
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.3,
        top_p=1
    )

    print("\n💬 Analysis Result:\n")
    print(response.choices[0].message.content)

# ---------- 8️⃣ Main Entry ----------
if __name__ == "__main__":
    pdf_path = "scraped_data.pdf"     # compliance dataset
    contract_path = "data/contracts/Contract_v1.pdf"    # your contract

    # 1. Load and process compliance dataset
    documents = load_compliance_data(pdf_path)
    chunks = split_documents(documents)
    vectorstore = create_vector_store(chunks)

    # 2. Load contract file
    contract_text = load_contract(contract_path)

    # 3. Analyze using Groq
    analyze_contract(client, vectorstore, contract_text)
