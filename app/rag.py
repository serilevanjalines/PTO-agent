import chromadb
from chromadb.utils import embedding_functions

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

    for document in documents:

        policy = document["policy"]
        content = document["content"]
        sections = content.split("## ")

        for section in sections[1:]:

            country, text = section.split("\n", maxsplit=1)
            chunks.append(
                {
                    "policy": policy,
                    "country": country.strip(),
                    "text": text.strip(),
                }
            )

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

    for document, metadata, distance in zip(documents, metadatas, distances):

        retrieved_chunks.append(
            {
                "policy": metadata["policy"],
                "country": metadata["country"],
                "text": document,
                "distance": distance,
            }
        )

    return retrieved_chunks