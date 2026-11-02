"""
Tests for the PDF parser service.

Run with: pytest tests/test_pdf_parser.py -v
"""

import pytest
import tempfile
import os

import fitz  # PyMuPDF


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF for testing."""
    pdf_path = tmp_path / "test_syllabus.pdf"

    doc = fitz.open()
    page = doc.new_page()

    # Add syllabus-like content
    text = """
COMPUTER SCIENCE 101 - DATA STRUCTURES

Unit 1: INTRODUCTION TO DATA STRUCTURES
1.1 What are Data Structures
1.2 Abstract Data Types
1.3 Algorithm Analysis

Unit 2: LINEAR DATA STRUCTURES
2.1 Arrays and Dynamic Arrays
2.2 Linked Lists (Singly, Doubly, Circular)
2.3 Stacks and Queues

Unit 3: SORTING ALGORITHMS
3.1 Bubble Sort and Selection Sort
3.2 Merge Sort
3.3 Quicksort
3.4 Time Complexity Analysis

Unit 4: TREES AND GRAPHS
4.1 Binary Trees
4.2 Binary Search Trees
4.3 AVL Trees
4.4 Graph Representations
4.5 BFS and DFS
"""
    page.insert_text((72, 72), text, fontsize=11)
    doc.save(str(pdf_path))
    doc.close()

    return str(pdf_path)


class TestPDFParser:
    """Tests for pdf_parser.py."""

    def test_parse_returns_expected_keys(self, sample_pdf):
        """Parse result should contain all expected fields."""
        from api.services.pdf_parser import parse_pdf

        result = parse_pdf(sample_pdf)

        assert "full_text" in result
        assert "topics" in result
        assert "page_count" in result
        assert "chunks" in result

    def test_parse_extracts_text(self, sample_pdf):
        """Parser should extract readable text."""
        from api.services.pdf_parser import parse_pdf

        result = parse_pdf(sample_pdf)

        assert len(result["full_text"]) > 100
        assert "Data Structures" in result["full_text"]

    def test_parse_detects_topics(self, sample_pdf):
        """Parser should detect section headers as topics."""
        from api.services.pdf_parser import parse_pdf

        result = parse_pdf(sample_pdf)

        assert len(result["topics"]) > 0
        # Should find unit headers or numbered sections
        topics_text = " ".join(result["topics"]).lower()
        assert any(word in topics_text for word in ["data", "sort", "tree", "unit"])

    def test_parse_creates_chunks(self, sample_pdf):
        """Parser should split text into chunks."""
        from api.services.pdf_parser import parse_pdf

        result = parse_pdf(sample_pdf)

        assert len(result["chunks"]) >= 1
        # Each chunk should be reasonable size
        for chunk in result["chunks"]:
            assert len(chunk) > 10
            assert len(chunk) < 1000

    def test_parse_page_count(self, sample_pdf):
        """Parser should report correct page count."""
        from api.services.pdf_parser import parse_pdf

        result = parse_pdf(sample_pdf)
        assert result["page_count"] == 1

    def test_parse_nonexistent_file(self):
        """Parser should raise error for missing files."""
        from api.services.pdf_parser import parse_pdf

        with pytest.raises(FileNotFoundError):
            parse_pdf("nonexistent_file.pdf")
