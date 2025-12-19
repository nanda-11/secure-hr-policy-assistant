import os
import requests
from dotenv import load_dotenv
from functools import lru_cache

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

# ---------------- ROLE → ACCESS MAP ----------------
ROLE_ACCESS = {
    "Intern": ["public"],
    "Employee": ["public", "employee"],
    "Manager": ["public", "employee", "manager"],
    "HR": ["public", "employee", "manager", "confidential"],
}

# ---------------- EMBEDDINGS ----------------
@lru_cache(maxsize=1)
def load_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": False},
    )

class HRPolicyAssistant:
    def __init__(self, enable_llm: bool = True):
        self.base_url = os.getenv("CYBORGDB_URL", "http://localhost:8000").rstrip("/")
        self.api_key = os.getenv("CYBORGDB_API_KEY")
        self.index_key = os.getenv("CYBORGDB_INDEX_KEY")
        self.index_name = "hr_policies"

        if not self.api_key or not self.index_key:
            raise RuntimeError("Missing CyborgDB configuration")

        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

        print("🔧 Loading embeddings (cached, CPU)...")
        self.embeddings = load_embeddings()

        self.chain = None
        if enable_llm:
            print("🔧 Connecting to Groq...")
            groq_key = os.getenv("GROQ_API_KEY")
            if not groq_key:
                raise RuntimeError("Missing GROQ_API_KEY")

            llm = ChatGroq(
                groq_api_key=groq_key,
                model_name="llama-3.3-70b-versatile",
                temperature=0,
            )

            prompt = ChatPromptTemplate.from_template(
                """You are a secure HR assistant.

RULES:
1. Answer ONLY from the provided context.
2. If the answer is not explicitly present, respond exactly:
"I cannot answer this based on your access level."
3. Do NOT infer or guess.

Context:
{context}

Question: {input}

Answer:"""
            )

            self.chain = prompt | llm | StrOutputParser()

        print("✅ Backend ready\n")

    # ---------------- INGEST ----------------
    def ingest_text(self, text: str, access_level: str, source: str = "manual"):
        vector = list(map(float, self.embeddings.embed_query(text)))

        payload = {
            "index_name": self.index_name,
            "index_key": self.index_key,
            "items": [
                {
                    "id": f"{source}-{abs(hash(text))}",
                    "vector": vector,
                    "metadata": {
                        "access_level": access_level,
                        "text": text,
                        "source": source,
                    },
                }
            ],
        }

        resp = requests.post(
            f"{self.base_url}/v1/vectors/upsert",
            headers=self.headers,
            json=payload,
            timeout=30,
        )

        if resp.status_code != 200:
            raise RuntimeError(resp.text)

    # ---------------- QUERY (RBAC FIXED) ----------------
    def ask(self, question: str, role: str) -> str:
        allowed_levels = ROLE_ACCESS[role]
        query_vector = list(map(float, self.embeddings.embed_query(question)))

        # 🔑 NO FILTERS HERE (important)
        payload = {
            "index_name": self.index_name,
            "index_key": self.index_key,
            "query_vectors": query_vector,
            "top_k": 8,  # over-fetch, then filter safely
            "include": ["metadata"],
        }

        resp = requests.post(
            f"{self.base_url}/v1/vectors/query",
            headers=self.headers,
            json=payload,
            timeout=30,
        )

        if resp.status_code != 200:
            return f"❌ DB Error: {resp.text}"

        results = resp.json().get("results", [])

        # 🔒 ENFORCE RBAC IN APPLICATION LAYER
        authorized_texts = []
        for r in results:
            meta = r.get("metadata", {})
            if meta.get("access_level") in allowed_levels:
                authorized_texts.append(meta.get("text", ""))

        if not authorized_texts:
            return "I cannot answer this based on your access level."

        context = "\n\n".join(authorized_texts)

        return self.chain.invoke({
            "context": context,
            "input": question,
        })
