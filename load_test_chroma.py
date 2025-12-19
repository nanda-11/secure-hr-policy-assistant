import time
import statistics
import concurrent.futures

from langchain_huggingface import HuggingFaceEmbeddings
from chromadb import Client
from chromadb.config import Settings

# ---------------- SETUP ----------------
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
)

client = Client(Settings(anonymized_telemetry=False))
collection = client.get_or_create_collection(name="hr_plaintext")

ROLE_ACCESS = {
    "Intern": ["public"],
    "Employee": ["public", "employee"],
    "Manager": ["public", "employee", "manager"],
    "HR": ["public", "employee", "manager", "confidential"],
}

QUERIES = [
    "What are the office working hours?",
    "What is the leave policy?",
    "How are performance reviews conducted?",
    "What salary bands apply to engineers?",
]

# ---------------- PRE-EMBED ----------------
print("🔧 Precomputing embeddings...")
VECTORS = [embeddings.embed_query(q) for q in QUERIES]

# ---------------- QUERY ----------------
def timed_query(vector):
    start = time.perf_counter()

    collection.query(
        query_embeddings=[vector],
        n_results=4,
    )

    return time.perf_counter() - start


def run():
    latencies = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for v in VECTORS:
            for _ in range(10):
                futures.append(executor.submit(timed_query, v))

        for f in concurrent.futures.as_completed(futures):
            latencies.append(f.result())

    return latencies


def summarize(latencies):
    p50 = statistics.quantiles(latencies, n=100)[49]
    p95 = statistics.quantiles(latencies, n=100)[94]
    p99 = statistics.quantiles(latencies, n=100)[98]

    print("\n📊 PLAINTEXT (Chroma) RESULTS")
    print(f"p50: {p50:.3f}s")
    print(f"p95: {p95:.3f}s")
    print(f"p99: {p99:.3f}s")


if __name__ == "__main__":
    results = run()
    summarize(results)
