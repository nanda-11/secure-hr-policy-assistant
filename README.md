🔐 Secure HR Policy Assistant

Encrypted, Role-Aware Retrieval-Augmented Generation using CyborgDB

📌 Overview

This project demonstrates a secure internal HR policy assistant that allows employees to query HR policies in natural language without exposing sensitive information such as salary bands, performance calibration details, or workforce reduction plans.

Unlike traditional RAG systems that store embeddings in plaintext vector databases (which are vulnerable to inversion attacks), this system uses CyborgDB’s encrypted vector search combined with role-based access control (RBAC) to ensure that:

Sensitive policy data is never stored or queried in plaintext

Users can only retrieve content they are authorized to see

The language model never receives unauthorized context

This project was built as a realistic enterprise prototype suitable for HR, legal, healthcare, and finance use cases.

🎯 Problem Statement

Most enterprise AI assistants today rely on plaintext vector databases. If these databases are compromised, embeddings can be reverse-engineered to recover sensitive internal documents.

Security and compliance teams therefore block many RAG deployments.

Our goal was to prove that:

Encrypted vector search

Combined with role-aware retrieval

Can enable secure RAG without sacrificing usability or performance

✅ Solution Highlights

🔐 Encrypted vector storage and search using CyborgDB

👥 Role-based access control enforced at the application layer

🧠 Retrieval-Augmented Generation (RAG) using LangChain

⚡ Fast, local embeddings using Hugging Face models

🤖 LLM responses via Groq, with graceful fallback on rate limits

📄 Document ingestion via PDF and DOCX uploads

📊 Benchmarking against a plaintext vector store (Chroma)

🧱 Architecture
User (Streamlit UI)
        ↓
Role Selection (RBAC)
        ↓
LangChain Orchestration
        ↓
CyborgDB (Encrypted Vector Search)
        ↓
Authorized Context Only
        ↓
Groq LLM (or fallback)
        ↓
Final Answer


Key design choice:
Authorization is enforced before the LLM is invoked. The model never sees data it shouldn’t.

🧑‍💼 Supported Roles & Access Levels
Role	Accessible Policy Levels
Intern	Public
Employee	Public, Employee
Manager	Public, Employee, Manager
HR	Public, Employee, Manager, Confidential
📄 Policy Types

The system supports realistic HR handbook content, including:

Public: office hours, dress code, safety guidelines

Employee: leave policies, performance reviews, remote work

Manager: salary recommendations, calibration processes

Confidential: executive compensation, layoffs, severance plans

Each policy is chunked, embedded locally, encrypted, and stored in CyborgDB.

🛠️ Tech Stack
Layer	Technology
Frontend	Streamlit
Orchestration	LangChain
Vector DB	CyborgDB (encrypted)
Embeddings	sentence-transformers/all-MiniLM-L6-v2
LLM	Groq (llama-3.3-70b)
Document Parsing	pdfplumber, python-docx
Benchmarking	Python + ThreadPoolExecutor
🚀 Getting Started
1️⃣ Clone the repository
git clone <repo-url>
cd CyborgDB

2️⃣ Create and activate virtual environment
python -m venv venv
source venv/bin/activate

3️⃣ Install dependencies
pip install -r requirements.txt

4️⃣ Configure environment variables

Create a .env file:

CYBORGDB_URL=http://localhost:8000
CYBORGDB_API_KEY=your_api_key
CYBORGDB_INDEX_KEY=your_32_byte_hex_key
GROQ_API_KEY=your_groq_key

🐳 Running CyborgDB (Local)
docker run -d \
  --name cyborgdb \
  -p 8000:8000 \
  -e CYBORGDB_API_KEY=your_api_key \
  cyborginc/cyborgdb-service:latest


Create the encrypted index:

curl -X POST http://localhost:8000/v1/indexes/create \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "hr_policies",
    "index_key": "your_32_byte_hex_key",
    "index_config": {
      "type": "ivfflat",
      "dimension": 384,
      "metric": "cosine",
      "nlist": 1
    }
  }'

▶️ Run the App
streamlit run app.py

📊 Performance Evaluation

We benchmarked encrypted retrieval against a plaintext vector store.

Plaintext (Chroma)
p50: 0.001s
p95: 0.002s
p99: 0.002s

Encrypted (CyborgDB)
p50: 1.36s
p95: 2.24s
p99: 2.83s


Result:
Encrypted search adds latency but remains well within acceptable bounds for enterprise HR workflows.

🔐 Security Guarantees

Embeddings are encrypted at rest and during search

No plaintext vectors stored in the database

RBAC enforced before LLM invocation

Graceful degradation if LLM rate limits are reached

No sensitive data leakage to unauthorized users

🧪 Demo Scenarios

Ask the same question under different roles:

“How is workforce reduction planning handled?”

Intern → ❌ Access denied

Employee → ❌ Access denied

Manager → ❌ Access denied

HR → ✅ Answered

This visibly demonstrates secure, role-aware retrieval.

🌍 Broader Applications

While demonstrated for HR, this pattern applies to:

Legal & Compliance — contracts, NDAs, privileged clauses

Healthcare — role-restricted clinical documentation

Finance — multi-tenant, confidential financial data

Enterprise SaaS — encrypted, role-aware AI assistants

🔮 Future Work

OAuth-based authentication instead of manual role selection

Tenant-level cryptographic isolation

Hybrid local LLM fallback (Ollama)

Audit logging and compliance reporting

Answer caching to reduce token usage

🏁 Final Note

This project shows that secure, encrypted RAG is practical today — and that CyborgDB enables AI use cases that are otherwise blocked by security and compliance concerns.