import time
import statistics
import requests

from rag_backend import HRPolicyAssistant, ROLE_ACCESS

# IMPORTANT: disable LLM
assistant = HRPolicyAssistant(enable_llm=False)

QUERIES = [
    "What are the office working hours?",
    "What is the leave policy?",
    "How are performance reviews conducted?",
    "What salary bands apply to engineers?",
]

# ---------------- PRECOMPUTE EMBEDDINGS ----------------
print("🔧 Precomputing embeddings...")
VECTORS = [
    list(map(float, assistant.embeddings.embed_query(q)))
    for q in QUERIES
]

REQUESTS_PER_QUERY = 5   # keep small
TIMEOUT = 30             # safe for local Docker

# ---------------- QUERY ----------------
def timed_query(vector):
    start = time.perf_counter()

    payload = {
        "index_name": assistant.index_name,
        "index_key": assistant.index_key,
        "query_vectors": vector,
        "top_k": 4,
        "filters": {
            "access_level": {"$in": ROLE_ACCESS["HR"]}
        },
        "include": ["metadata"],
    }

    resp = requests.post(
        f"{assistant.base_url}/v1/vectors/query",
        headers=assistant.headers,
        json=payload,
        timeout=TIMEOUT,
    )

    if resp.status_code != 200:
        raise RuntimeError(resp.text)

    return time.perf_counter() - start


# ---------------- RUN ----------------
def run():
    latencies = []
    print("\n🚀 Running encrypted CyborgDB benchmark (DB-only)...\n")

    for vector in VECTORS:
        for _ in range(REQUESTS_PER_QUERY):
            latencies.append(timed_query(vector))

    return latencies


def summarize(latencies):
    p50 = statistics.quantiles(latencies, n=100)[49]
    p95 = statistics.quantiles(latencies, n=100)[94]
    p99 = statistics.quantiles(latencies, n=100)[98]

    print("📊 ENCRYPTED (CyborgDB) RESULTS")
    print(f"Requests: {len(latencies)}")
    print(f"p50: {p50:.3f}s")
    print(f"p95: {p95:.3f}s")
    print(f"p99: {p99:.3f}s")


if __name__ == "__main__":
    results = run()
    summarize(results)
