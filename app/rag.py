import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi

from pathlib import Path

from . import config

POLICY_DIR = Path("samples") / "policies"

ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

chroma_client = chromadb.PersistentClient(path="./chroma_db")

collection = chroma_client.get_or_create_collection(
    name="pto_policy",
    embedding_function=ef,
    metadata={
        "hnsw:space": "cosine"
    }
)

def load_documents() -> list[dict]:
    """
    Load every policy document from samples/policies.
    """
    
    documents = []

    for file in POLICY_DIR.glob("*.md"):
        policy_name = file.stem
        content = file.read_text()
        documents.append(
            {
                "policy" : policy_name,
                "content": content,
            }
        )
    
    return documents




def chunk_documents() -> list[dict]:
    """
    Split every policy document into country-level chunks.
    """
    documents = load_documents()
    chunks = []

    chunk_id = 0

    for document in documents:

        policy = document["policy"]
        content = document["content"]
        sections = content.split("## ")

        for section in sections[1:]:

            country, text = section.split("\n", maxsplit=1)
            chunks.append(
                {
                    "id":f"chunk-{chunk_id}",
                    "policy": policy,
                    "country": country.strip(),
                    "text": text.strip(),
                }
            )
            chunk_id += 1

    return chunks




def index_documents():
    """
    Convert policy chunks into embeddings
    and store them in ChromaDB.
    """

    chunks = chunk_documents()

    documents = []
    ids = []
    metadatas = []

    for i, chunk in enumerate(chunks):

        documents.append(chunk["text"])

        ids.append(f"chunk-{i}")

        metadatas.append(
            {
                "policy": chunk["policy"],
                "country": chunk["country"],
            }
        )

    collection.add(
        documents=documents,
        ids=ids,
        metadatas=metadatas,
    )

    return chunks


def semantic_search(query: str, n_results: int = 3) -> list[dict]:

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    retrieved_chunks = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    chunk_ids = results["ids"][0]

    for chunk_id , document, metadata, distance in zip(chunk_ids,documents, metadatas, distances):

        retrieved_chunks.append(
            {   
                "id": chunk_id,
                "policy": metadata["policy"],
                "country": metadata["country"],
                "text": document,
                "distance": distance,
            }
        )

    return retrieved_chunks



def build_bm25_index():
    chunks = chunk_documents()

    tokenized_corpus = []

    for chunk in chunks:
        tokens = chunk["text"].lower().split()
        tokenized_corpus.append(tokens)

    bm25 = BM25Okapi(tokenized_corpus)

    return bm25, chunks



def bm25_search(query: str, top_k: int = 3):
    """
    Search policy chunks using BM25 keyword search.
    """

    bm25, chunks = build_bm25_index()

    query_tokens = query.lower().split()

    scores = bm25.get_scores(query_tokens)

    scored_chunks = []

    for index, score in enumerate(scores):
        scored_chunks.append((index, score))

    scored_chunks.sort(
        key=lambda x: x[1],
        reverse=True
    )

    top_chunks = []

    for chunk_index, score in scored_chunks[:top_k]:
        chunk = chunks[chunk_index].copy()
        chunk["score"] = score
        top_chunks.append(chunk)

    return top_chunks


def reciprocal_rank_fusion(semantic_results, bm25_results, top_k=3):
    """
    combine the results from semantic search and BM25 using Reciprocal Rank Fusion (RRF).
    """

    fusion_scores = {}

    for rank, chunk in enumerate(semantic_results, start=1):

        chunk_id = chunk["id"]

        if chunk_id not in fusion_scores:
            fusion_scores[chunk_id] = 0

        fusion_scores[chunk_id] += 1 / (60 + rank)

    for rank, chunk in enumerate(bm25_results, start=1):

        chunk_id = chunk["id"]

        if chunk_id not in fusion_scores:
            fusion_scores[chunk_id] = 0

        fusion_scores[chunk_id] += 1 / (60 + rank)

    sorted_chunks = sorted(fusion_scores.items(),key=lambda item: item[1],reverse=True)

    all_chunks = chunk_documents()

    chunk_lookup = {}

    for chunk in all_chunks:
        chunk_lookup[chunk["id"]] = chunk

    retrieved_chunks = []

    for chunk_id, score in sorted_chunks[:top_k]:
        retrieved_chunks.append(chunk_lookup[chunk_id])

    return retrieved_chunks


def hybrid_search(query: str,top_k: int = 3) -> list[dict]:
    """
    Retrieve the most relevant policy chunks using
    Hybrid Search (Semantic + BM25 + RRF).
    """
    semantic_results = semantic_search(query=query, n_results=top_k)

    bm25_results = bm25_search(query=query, top_k=top_k)

    retrieved_chunks = reciprocal_rank_fusion(
        semantic_results=semantic_results,
        bm25_results=bm25_results,
        top_k=top_k,
    )

    return retrieved_chunks
