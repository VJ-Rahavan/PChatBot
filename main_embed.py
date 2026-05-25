import os
import sys
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()
    
DOCS_FOLDER  = "./my_docs"
DB_PATH      = "./chroma_db"
COLLECTION   = "my_docs"
CHUNK_SIZE   = 500        # characters (LangChain splitter uses chars, not tokens)
CHUNK_OVERLAP = 50
TOP_K        = 3

# Free local embedding model — no API key needed
# Swap to "text-embedding-3-small" via OpenAIEmbeddings if you prefer
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",   # small, fast, good quality
    model_kwargs={"device": "cpu"},
)

groq_client = ChatGroq(
    model="llama-3.3-70b-versatile",         # or mixtral-8x7b-32768
    api_key=os.environ["GROQ_API_KEY"],
)


# ── Indexing ──────────────────────────────────────────────────────────────────

# def index_folder(folder: str):
#     """Load .txt and .md files, chunk, embed, store in ChromaDB."""
#     os.makedirs(folder, exist_ok=True)

#     # LangChain loader — handles all .txt and .md files in the folder
#     loader = DirectoryLoader(
#         folder,
#         glob="**/*.{txt,md}",
#         loader_cls=TextLoader,
#         loader_kwargs={"encoding": "utf-8"},
#         show_progress=True,
#     )
#     docs = loader.load()

#     if not docs:
#         print(f"No .txt or .md files found in {folder}/")
#         return

#     print(f"Loaded {len(docs)} files")

#     # Chunk with overlap — respects paragraph/sentence boundaries
#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=CHUNK_SIZE,
#         chunk_overlap=CHUNK_OVERLAP,
#         separators=["\n\n", "\n", ". ", " ", ""],
#     )
#     chunks = splitter.split_documents(docs)
#     print(f"Split into {len(chunks)} chunks")

#     # Each chunk keeps its source metadata automatically:
#     # chunk.metadata == {"source": "./my_docs/filename.txt"}

#     # Store in ChromaDB — LangChain handles embedding + storing in one call
#     vectorstore = Chroma.from_documents(
#         documents=chunks,
#         embedding=embeddings,
#         persist_directory=DB_PATH,
#         collection_name=COLLECTION,
#         collection_metadata={"hnsw:space": "cosine"},
#     )
#     print(f"Done. {vectorstore._collection.count()} chunks in DB.")


def index_folder(folder: str):
    os.makedirs(folder, exist_ok=True)

    # Load files manually — DirectoryLoader glob is unreliable
    from langchain_community.document_loaders import TextLoader
    from pathlib import Path

    docs = []
    for filepath in Path(folder).rglob("*"):
        if filepath.suffix in (".txt", ".md"):
            print(f"  Loading: {filepath.name}")
            loader = TextLoader(str(filepath), encoding="utf-8")
            docs.extend(loader.load())

    if not docs:
        print(f"No .txt or .md files found in {folder}/")
        return

    print(f"Loaded {len(docs)} files")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"Split into {len(chunks)} chunks")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_PATH,
        collection_name=COLLECTION,
        collection_metadata={"hnsw:space": "cosine"},
    )
    print(f"Done. {vectorstore._collection.count()} chunks in DB.")

# ── Searching ─────────────────────────────────────────────────────────────────

def get_vectorstore():
    """Load existing ChromaDB collection."""
    return Chroma(
        persist_directory=DB_PATH,
        embedding_function=embeddings,
        collection_name=COLLECTION,
        collection_metadata={"hnsw:space": "cosine"},
    )


def search(query: str, n: int = TOP_K, source_filter: str | None = None):
    """Find top-n chunks most similar to the query."""
    vs = get_vectorstore()

    if vs._collection.count() == 0:
        print("Nothing indexed yet. Run: python search_my_docs.py index")
        return None, None

    # Optional: filter to a specific file
    where = {"source": {"$contains": source_filter}} if source_filter else None

    results = vs.similarity_search_with_score(
        query=query,
        k=n,
        filter=where,
    )

    print(f'\nTop {len(results)} results for: "{query}"\n')
    print("─" * 60)

    for rank, (doc, score) in enumerate(results, 1):
        source = os.path.basename(doc.metadata.get("source", "unknown"))
        # LangChain returns cosine distance (lower = better), convert to similarity
        similarity = 1 - score
        print(f"#{rank}  [{source}]  similarity: {similarity:.3f}")
        print(f"    {doc.page_content[:200].strip()}...")
        print()

    return results


def search_and_answer(query: str, n: int = TOP_K):
    """
    Retrieve relevant chunks, then ask Groq to answer based on them.
    This is the full RAG pattern — Stage 4 preview.
    """
    vs = get_vectorstore()

    if vs._collection.count() == 0:
        print("Nothing indexed yet.")
        return

    results = vs.similarity_search(query, k=n)

    # Build context string from retrieved chunks
    context = "\n\n---\n\n".join([
        f"[{os.path.basename(doc.metadata.get('source', '?'))}]\n{doc.page_content}"
        for doc in results
    ])

    prompt = f"""Answer the question using only the context below.
If the answer isn't in the context, say "I don't see that in the documents."

Context:
{context}

Question: {query}
"""

    print(f'\nSearching for: "{query}"')
    print("─" * 60)

    response = groq_client.invoke([HumanMessage(content=prompt)])
    print(response.content)
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python search_my_docs.py index")
        print('  python search_my_docs.py search "your question"')
        print('  python search_my_docs.py ask    "your question"   ← uses Groq to answer')
        print('  python search_my_docs.py search "question" --file notes.txt')
        return

    command = sys.argv[1]

    if command == "index":
        print(f"Indexing {DOCS_FOLDER}/\n")
        index_folder(DOCS_FOLDER)

    elif command == "search":
        if len(sys.argv) < 3:
            print('Provide a query: python search_my_docs.py search "question"')
            return
        query = sys.argv[2]
        source = sys.argv[sys.argv.index("--file") + 1] if "--file" in sys.argv else None
        search(query, source_filter=source)

    elif command == "ask":
        if len(sys.argv) < 3:
            print('Provide a query: python search_my_docs.py ask "question"')
            return
        search_and_answer(sys.argv[2])

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()