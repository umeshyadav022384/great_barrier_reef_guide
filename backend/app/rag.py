import os
import re
from pathlib import Path
from typing import Dict, List, Optional


class RAGSystem:
    """Lightweight local RAG implementation that works without external services."""

    def __init__(self, persist_directory: str = None):
        current_dir = Path(__file__).resolve().parent
        backend_dir = current_dir.parent
        self.persist_directory = persist_directory or str(backend_dir / "data" / "chromadb")
        self.documents_by_location: Dict[str, List[str]] = {}
        self._load_documents()

    def _load_documents(self):
        current_dir = Path(__file__).resolve().parent
        backend_dir = current_dir.parent
        doc_dir = backend_dir / "data" / "documents"

        if not doc_dir.exists():
            print(f"⚠️ Documents directory not found: {doc_dir}")
            return

        txt_files = sorted([p for p in doc_dir.glob("*.txt")])
        if not txt_files:
            print(f"⚠️ No .txt files found in {doc_dir}")
            return

        for path in txt_files:
            location = path.stem
            try:
                lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
                self.documents_by_location[location] = lines
                print(f"📄 Loaded local knowledge for {location}")
            except Exception as exc:
                print(f"❌ Error loading {path.name}: {exc}")

    def search(self, query: str, location_filter: str, n_results: int = 3) -> List[str]:
        docs = self.documents_by_location.get(location_filter, [])
        if not docs:
            return []

        lowered_query = re.findall(r"[a-z0-9]+", query.lower())
        scored: List[tuple[int, str]] = []
        for doc in docs:
            lowered_doc = doc.lower()
            score = sum(1 for term in lowered_query if term in lowered_doc)
            if score > 0:
                scored.append((score, doc))

        if not scored:
            return []

        scored.sort(key=lambda item: item[0], reverse=True)
        return [doc for _, doc in scored[:n_results]]

    def get_all_documents(self, location: Optional[str] = None):
        if location:
            return self.documents_by_location.get(location, [])
        return self.documents_by_location

    def get_collection_stats(self) -> Dict:
        return {
            "total_documents": sum(len(items) for items in self.documents_by_location.values()),
            "locations": list(self.documents_by_location.keys()),
            "persist_directory": self.persist_directory,
            "embedding_model": "local-text-search"
        }

    def clear_collection(self):
        self.documents_by_location = {}