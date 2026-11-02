"""
Tests for the ChromaDB vector store service.

Run with: pytest tests/test_vector_store.py -v
"""

import pytest
import tempfile
import os


@pytest.fixture
def temp_vector_store(tmp_path):
    """Create a VectorStore with a temporary directory."""
    test_path = str(tmp_path / "test_chroma")
    os.environ["CHROMA_PATH"] = test_path

    from api.services.vector_store import VectorStore
    VectorStore._instances.clear()
    store = VectorStore(chroma_path=test_path)
    return store


class TestVectorStore:
    """Tests for vector_store.py."""

    def test_add_document(self, temp_vector_store):
        """Should add document chunks to the collection."""
        store = temp_vector_store

        store.add_document(
            text="Python is a high-level programming language. It supports multiple paradigms.",
            doc_id="test_doc_1",
            metadata={"subject": "Programming", "type": "syllabus"},
        )

        assert store.get_document_count() > 0

    def test_search_returns_results(self, temp_vector_store):
        """Search should return relevant documents."""
        store = temp_vector_store

        store.add_document(
            text="Arrays are contiguous blocks of memory. Linked lists use pointers to connect nodes.",
            doc_id="ds_notes",
            metadata={"subject": "Data Structures"},
        )

        results = store.search("What uses pointers?")

        assert len(results["documents"][0]) > 0
        # Should find the document about linked lists
        assert any("pointer" in doc.lower() for doc in results["documents"][0])

    def test_search_empty_collection(self, temp_vector_store):
        """Search on empty collection should return empty results."""
        store = temp_vector_store

        results = store.search("anything")
        assert results["documents"] == [[]]

    def test_save_and_search_conversation(self, temp_vector_store):
        """Should save and retrieve conversation memory."""
        store = temp_vector_store

        store.save_conversation(
            user_message="What is recursion?",
            agent_response="Recursion is when a function calls itself.",
            user_id="test_user",
        )

        results = store.search_memory("recursion", user_id="test_user")
        assert len(results) > 0
        assert "recursion" in results[0].lower()

    def test_delete_document(self, temp_vector_store):
        """Should delete all chunks for a document."""
        store = temp_vector_store

        store.add_document(
            text="Test content for deletion.",
            doc_id="delete_me",
            metadata={"type": "test"},
        )

        initial_count = store.get_document_count()
        assert initial_count > 0

        store.delete_document("delete_me")

        # Count should decrease (or be zero if it was the only doc)
        final_count = store.get_document_count()
        assert final_count < initial_count

    def test_multiple_documents(self, temp_vector_store):
        """Should handle multiple documents correctly."""
        store = temp_vector_store

        store.add_document(
            text="Machine learning is a subset of artificial intelligence.",
            doc_id="ml_doc",
            metadata={"subject": "AI"},
        )

        store.add_document(
            text="Databases store data in tables with rows and columns.",
            doc_id="db_doc",
            metadata={"subject": "Databases"},
        )

        # Search for ML content
        results = store.search("artificial intelligence")
        assert len(results["documents"][0]) > 0
