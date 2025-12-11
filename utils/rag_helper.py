"""
RAG System Helper - Integrates the RAG analysis with Streamlit
"""
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from groq import Groq
import json
import time
import hashlib
from typing import Dict, List, Optional
import sqlite3

load_dotenv()

class ResponseCache:
    """Simple cache for API responses using SQLite"""
    def __init__(self, db_path="response_cache.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize cache database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    response TEXT,
                    timestamp INTEGER,
                    token_count INTEGER
                )''')
                conn.commit()
        except Exception as e:
            print(f"Cache initialization error: {e}")
    
    def _hash_query(self, query: str) -> str:
        """Hash a query for cache key"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def get(self, query: str) -> Optional[str]:
        """Get cached response"""
        try:
            key = self._hash_query(query)
            with sqlite3.connect(self.db_path) as conn:
                result = conn.execute('SELECT response FROM cache WHERE key = ?', (key,)).fetchone()
                return result[0] if result else None
        except Exception:
            return None
    
    def set(self, query: str, response: str, token_count: int = 0):
        """Cache a response"""
        try:
            key = self._hash_query(query)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('INSERT OR REPLACE INTO cache (key, response, timestamp, token_count) VALUES (?, ?, ?, ?)',
                            (key, response, int(time.time()), token_count))
                conn.commit()
        except Exception as e:
            print(f"Cache set error: {e}")

class RAGAnalyzer:
    def __init__(self, compliance_pdf="scraped_data.pdf", vector_db_path="faiss_index"):
        """Initialize RAG analyzer with compliance standards"""
        self.compliance_pdf = compliance_pdf
        self.vector_db_path = vector_db_path
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.vectorstore = None
        self.embeddings = None
        self.cache = ResponseCache()
        self.rate_limit_retry_count = 2  # Reduced from 3 to 2
        self.rate_limit_backoff = 10  # Increased from 5 to 10 seconds
        
    def _estimate_tokens(self, text: str) -> int:
        """Rough estimate of tokens (1 token ≈ 4 characters)"""
        return len(text) // 4
    
    def _call_groq_with_fallback(self, prompt: str, max_tokens: int = 400, model: str = "llama-3.1-8b-instant") -> str:
        """Call Groq with automatic fallback and retry logic - optimized for speed"""
        
        # Estimate tokens to avoid hitting limits
        estimated_prompt_tokens = self._estimate_tokens(prompt)
        if estimated_prompt_tokens + max_tokens > 3000:  # Safety threshold
            # Reduce context if needed
            prompt = self._reduce_prompt_size(prompt)
        
        # Use fast model by default for quicker responses
        models_to_try = [model, "llama-3.1-8b-instant"]
        
        for attempt_model in models_to_try:
            for retry in range(self.rate_limit_retry_count):
                try:
                    response = self.client.chat.completions.create(
                        model=attempt_model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens,
                        temperature=0.3,
                        top_p=1
                    )
                    return response.choices[0].message.content
                    
                except Exception as e:
                    error_str = str(e)
                    
                    # Handle rate limit (429)
                    if "429" in error_str or "rate_limit" in error_str.lower():
                        # If second attempt fails, don't retry - switch to fallback
                        if retry >= 1:
                            print(f"⚠️ Rate limit persists. Trying fallback model...")
                            break
                        
                        wait_time = 10  # Fixed 10 second wait
                        print(f"⚠️ Rate limit hit. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise e
        
        # Final fallback response
        return "❌ Unable to process due to API rate limits. Please try again in a few minutes."
    
    def _reduce_prompt_size(self, prompt: str) -> str:
        """Reduce prompt size by truncating context"""
        lines = prompt.split('\n')
        
        # Find sections and truncate
        new_prompt = []
        for line in lines:
            if 'Context' in line or 'Contract' in line or 'Compliance' in line:
                # Keep headers but reduce content
                new_prompt.append(line)
            elif len('\n'.join(new_prompt)) < 2000:  # Keep under 2000 chars
                new_prompt.append(line)
        
        return '\n'.join(new_prompt)
        
    def load_compliance_data(self):
        """Load compliance dataset"""
        if not os.path.exists(self.compliance_pdf):
            raise FileNotFoundError(f"Compliance PDF not found: {self.compliance_pdf}")
        
        loader = PyPDFLoader(self.compliance_pdf)
        documents = loader.load()
        return documents
    
    def split_documents(self, documents):
        """Split documents into chunks"""
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
        chunks = splitter.split_documents(documents)
        return chunks
    
    def create_vector_store(self, chunks):
        """Create or load FAISS vector store"""
        if os.path.exists(self.vector_db_path):
            self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            self.vectorstore = FAISS.load_local(self.vector_db_path, self.embeddings, allow_dangerous_deserialization=True)
        else:
            self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
            self.vectorstore.save_local(self.vector_db_path)
        
        return self.vectorstore
    
    def setup(self):
        """Complete setup: load compliance, create chunks, and vector store"""
        documents = self.load_compliance_data()
        chunks = self.split_documents(documents)
        self.create_vector_store(chunks)
    
    def load_contract(self, contract_path):
        """Load contract from PDF or text file"""
        if contract_path.lower().endswith(".pdf"):
            loader = PyPDFLoader(contract_path)
            docs = loader.load()
            contract_text = " ".join([doc.page_content for doc in docs])
        else:
            loader = TextLoader(contract_path)
            docs = loader.load()
            contract_text = " ".join([doc.page_content for doc in docs])
        
        return contract_text
    
    def analyze_contract(self, contract_text):
        """Analyze contract for compliance issues - optimized for rate limits"""
        import re
        
        # Use ONLY FIRST 6000 chars to minimize API calls (single request)
        contract_text = contract_text[:6000]
        
        try:
            # Retrieve relevant compliance info
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 2})
            relevant_docs = retriever.invoke(contract_text[:1000])
            context = "\n".join([doc.page_content[:200] for doc in relevant_docs])
            
            # Single, focused prompt
            prompt = f"""Analyze this contract for compliance issues ONLY.

Compliance Standards:
{context}

Contract Text:
{contract_text}

Return ONLY valid JSON (no markdown, no extra text):
{{"key_clauses": ["clause1", "clause2"], "compliance_issues": [{{"title": "Issue Title", "risk_level": "High/Medium/Low", "reason": "Brief reason"}}]}}"""
            
            # Single API call with careful error handling
            result_text = self._call_groq_with_fallback(prompt, max_tokens=500)
            
            # Parse JSON from response
            all_issues = []
            all_clauses = []
            
            try:
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    all_clauses = result.get("key_clauses", [])[:10]  # Limit to 10
                    all_issues = result.get("compliance_issues", [])[:8]  # Limit to 8
            except json.JSONDecodeError:
                pass
            
            analysis_result = {
                "key_clauses": all_clauses,
                "compliance_issues": all_issues
            }
            
            return analysis_result
            
        except Exception as e:
            print(f"Error analyzing contract: {str(e)}")
            return {"key_clauses": [], "compliance_issues": []}
    
    def get_chatbot_response(self, contract_text, user_question):
        """Get chatbot response about contract - with caching"""
        import hashlib
        
        # Check cache first
        cache_key = f"chat:{hashlib.md5((contract_text[:200] + user_question).encode()).hexdigest()}"
        cached_response = self.cache.get(cache_key)
        
        if cached_response:
            return f"(cached) {cached_response}"
        
        # Retrieve relevant parts of the contract
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 2})  # Reduced from 3 to 2
        relevant_docs = retriever.invoke(user_question)
        context = "\n".join([doc.page_content[:200] for doc in relevant_docs])  # Truncate
        
        # MINIMAL prompt for chatbot
        prompt = f"""You are a compliance advisor. Answer briefly:
Question: {user_question}
Contract: {contract_text[:1000]}
Standards: {context}
Answer:"""
        
        # Get response with fallback
        response = self._call_groq_with_fallback(prompt, max_tokens=300)
        
        # Cache the response
        self.cache.set(cache_key, response)
        
        return response
