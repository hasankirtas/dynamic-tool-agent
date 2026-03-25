import importlib
import inspect
import os
import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder
from src.tools.abstraction.base_tool import BaseTool


class ToolRegistry:
    """
    Manages tool discovery, registration, and semantic retrieval.
    Uses ChromaDB for storage and BGE models for embedding/reranking.
    """

    def __init__(self, db_path: str = "./chroma_db"):
        self.db_path = db_path

        self.embedding_model = SentenceTransformer("BAAI/bge-large-en-v1.5")
        self.reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name="tool_registry",
            metadata={"hnsw:space": "cosine"},
        )

        self._tools: dict[str, BaseTool] = {}

    def _auto_discover_tools(self) -> list[BaseTool]:
        """
        Dynamically scans the 'implementations' directory for tool classes.
        Enables seamless addition of new capabilities without manual registration.
        """
        tools = []
        implementations_dir = os.path.join(os.path.dirname(__file__), "implementations")

        for filename in os.listdir(implementations_dir):
            if not filename.endswith("_tool.py"):
                continue

            module_name = f"src.tools.implementations.{filename[:-3]}"
            module = importlib.import_module(module_name)

            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseTool) and obj is not BaseTool:
                    tools.append(obj())

        return tools

    def register_all(self) -> int:
        """
        Populates the transient tool map and synchronizes the vector database.
        Returns the number of newly registered tools.
        """
        tools = self._auto_discover_tools()
        existing_ids = set(self.collection.get()["ids"])

        registered_count = 0
        for tool in tools:
            meta = tool.metadata
            self._tools[meta.name] = tool

            if meta.name in existing_ids:
                continue

            search_text = meta.to_search_text()
            embedding = self.embedding_model.encode(search_text).tolist()

            self.collection.add(
                ids=[meta.name],
                embeddings=[embedding],
                documents=[search_text],
                metadatas=[{
                    "name": meta.name,
                    "description": meta.description,
                    "category": meta.category,
                    "tags": ",".join(meta.tags),
                }],
            )
            registered_count += 1

        return registered_count

    def search(self, query: str, top_k: int = 5, category: str | None = None) -> list[dict]:
        """
        Executes a two-stage retrieval pipeline:
        1. Semantic Search: Initial filtering via vector similarity (BGE-Large).
        2. Reranking: Cross-Encoder (BGE-Reranker) scoring to minimize false positives.
        """
        query_embedding = self.embedding_model.encode(query).tolist()

        where_filter = None
        if category:
            where_filter = {"category": category}

        fetch_count = min(top_k * 2, self.collection.count())
        if fetch_count == 0:
            return []

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=fetch_count,
            where=where_filter if where_filter else None,
        )

        if not results["documents"] or not results["documents"][0]:
            return []

        candidates = []
        for i, doc in enumerate(results["documents"][0]):
            candidates.append({
                "name": results["metadatas"][0][i]["name"],
                "description": results["metadatas"][0][i]["description"],
                "category": results["metadatas"][0][i]["category"],
                "document": doc,
                "similarity_score": 1 - results["distances"][0][i],
            })

        rerank_pairs = [[query, c["document"]] for c in candidates]
        rerank_scores = self.reranker.predict(rerank_pairs)

        for i, score in enumerate(rerank_scores):
            candidates[i]["rerank_score"] = float(score)

        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        final_results = []
        for c in candidates[:top_k]:
            tool = self._tools.get(c["name"])
            final_results.append({
                "name": c["name"],
                "description": c["description"],
                "category": c["category"],
                "relevance_score": round(c["rerank_score"], 4),
                "schema": tool.schema if tool else None,
            })

        return final_results

    def get_tool(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def get_schema(self, name: str) -> dict | None:
        tool = self._tools.get(name)
        return tool.schema if tool else None

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())
