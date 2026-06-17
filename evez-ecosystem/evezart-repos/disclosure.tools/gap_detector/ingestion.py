"""
Document ingestion pipeline for disclosure.tools
Handles PDF, text, JSON, and URL ingestion → normalized corpus format.
"""
import json
import re
import hashlib
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class IngestedDocument:
    """Normalized document representation."""
    id: str
    title: str
    text: str
    sections: List[str]
    date: str
    source: str
    source_type: str  # pdf, text, json, url, manual
    metadata: Dict = field(default_factory=dict)
    references: List[Tuple[int, int]] = field(default_factory=list)
    hash: str = ""

    def to_corpus_entry(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "text": self.text,
            "sections": self.sections,
            "date": self.date,
            "source": self.source,
            "source_type": self.source_type,
            "metadata": self.metadata,
            "references": self.references,
            "hash": self.hash,
        }


def _compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _extract_sections(text: str, max_section_len: int = 2000) -> List[str]:
    """Split text into sections by headers, page breaks, or paragraph clusters."""
    # Try splitting by common FOIA document headers
    header_patterns = [
        r'\n(?=(?:SECTION|Section|PART|Part|CHAPTER|Chapter|APPENDIX|Appendix|EXHIBIT|Exhibit)\s)',
        r'\n(?=(?:\d+\.|I+\.|A\.)\s+[A-Z])',  # numbered headers
        r'\n-{3,}\n',   # horizontal rules
        r'\n={3,}\n',
        r'\n\*\*\*\n',
        r'\f',          # form feed (page break)
    ]

    sections = []
    for pattern in header_patterns:
        parts = re.split(pattern, text)
        if len(parts) > 1:
            sections = [p.strip() for p in parts if p.strip()]
            break

    if not sections:
        # Fall back: split by double newlines into paragraph clusters
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        sections = []
        current = ""
        for para in paragraphs:
            if len(current) + len(para) > max_section_len and current:
                sections.append(current)
                current = para
            else:
                current = (current + "\n\n" + para).strip()
        if current:
            sections.append(current)

    # Last resort: chunk by size
    if not sections:
        sections = [text[i:i+max_section_len] for i in range(0, len(text), max_section_len)]

    return sections


def _extract_references(sections: List[str]) -> List[Tuple[int, int]]:
    """Detect cross-references between sections (citation links)."""
    refs = []
    ref_patterns = [
        r'(?:see|refer to|referenced in|per|according to|as stated in|per)\s+(?:Section|Part|Chapter|Appendix|Exhibit|paragraph|para\.?)\s*(\d+|[A-Z]|[IVXL]+)',
        r'(?:Figure|Table|Eq\.)\s*\d+',
        r'\[(\d+)\]',  # bracket citations [1], [2]
    ]
    for i, section in enumerate(sections):
        section_lower = section.lower()
        for j, other in enumerate(sections):
            if i == j:
                continue
            # Check if section i references content in section j
            other_terms = set(re.findall(r'[A-Za-z]{4,}', other.lower()))
            section_terms = set(re.findall(r'[A-Za-z]{4,}', section_lower))
            overlap = len(other_terms & section_terms)
            # Threshold: meaningful term overlap suggests a reference
            if overlap >= 3:
                refs.append((i, j))

    return refs


def ingest_text(text: str, title: str = "Untitled", date: str = "", source: str = "manual",
                source_type: str = "text") -> IngestedDocument:
    """Ingest raw text into normalized document format."""
    doc_id = f"DOC-{hashlib.sha256(text.encode()).hexdigest()[:8].upper()}"
    sections = _extract_sections(text)
    references = _extract_references(sections)

    return IngestedDocument(
        id=doc_id,
        title=title,
        text=text,
        sections=sections,
        date=date or datetime.utcnow().strftime("%Y-%m-%d"),
        source=source,
        source_type=source_type,
        metadata={"n_sections": len(sections), "n_refs": len(references)},
        references=references,
        hash=_compute_hash(text),
    )


def ingest_pdf(pdf_path: str) -> IngestedDocument:
    """Ingest a PDF file → extract text, sections, references."""
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber required: pip install pdfplumber")

    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n\n"

    if not full_text.strip():
        raise ValueError(f"No text extracted from {pdf_path}")

    title = Path(pdf_path).stem.replace("_", " ").replace("-", " ").title()
    return ingest_text(full_text, title=title, source=pdf_path, source_type="pdf")


def ingest_json(json_path: str) -> List[IngestedDocument]:
    """Ingest a JSON file (single doc or array of docs)."""
    with open(json_path) as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = [data]

    docs = []
    for item in data:
        text = item.get("text", item.get("content", ""))
        title = item.get("title", item.get("id", "Untitled"))
        date = item.get("date", "")
        source = item.get("source", json_path)
        doc = ingest_text(text, title=title, date=date, source=source, source_type="json")
        if "id" in item:
            doc.id = item["id"]
        doc.metadata.update({k: v for k, v in item.items() if k not in ("text", "content", "title", "id", "date")})
        docs.append(doc)

    return docs


def ingest_url(url: str) -> IngestedDocument:
    """Ingest a URL by fetching and extracting text content."""
    import httpx
    resp = httpx.get(url, follow_redirects=True, timeout=30)
    resp.raise_for_status()
    text = resp.text

    # Strip HTML tags if present
    if "<html" in text.lower():
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.result = []
                self.skip = False
            def handle_starttag(self, tag, attrs):
                if tag in ("script", "style", "nav", "footer"):
                    self.skip = True
            def handle_endtag(self, tag):
                if tag in ("script", "style", "nav", "footer"):
                    self.skip = False
            def handle_data(self, data):
                if not self.skip:
                    self.result.append(data.strip())

        extractor = TextExtractor()
        extractor.feed(text)
        text = "\n".join(line for line in extractor.result if line)

    return ingest_text(text, title=url, source=url, source_type="url")


def ingest_file(file_path: str) -> List[IngestedDocument]:
    """Auto-detect file type and ingest."""
    path = Path(file_path)
    if path.suffix == ".pdf":
        return [ingest_pdf(file_path)]
    elif path.suffix == ".json":
        return ingest_json(file_path)
    elif path.suffix in (".txt", ".md", ".text"):
        text = path.read_text()
        doc = ingest_text(text, title=path.stem, source=file_path, source_type="text")
        return [doc]
    else:
        # Try reading as text
        try:
            text = path.read_text()
            doc = ingest_text(text, title=path.stem, source=file_path, source_type="text")
            return [doc]
        except Exception as e:
            raise ValueError(f"Cannot ingest {file_path}: {e}")


def ingest_bytes(data: bytes, filename: str) -> List[IngestedDocument]:
    """Ingest from uploaded bytes (e.g., from FastAPI UploadFile)."""
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            return [ingest_pdf(tmp_path)]
        finally:
            os.unlink(tmp_path)
    elif suffix == ".json":
        json_data = json.loads(data)
        if isinstance(json_data, dict):
            json_data = [json_data]
        with tempfile.NamedTemporaryFile(mode='w', suffix=".json", delete=False) as tmp:
            json.dump(json_data, tmp)
            tmp_path = tmp.name
        try:
            return ingest_json(tmp_path)
        finally:
            os.unlink(tmp_path)
    else:
        text = data.decode("utf-8", errors="replace")
        doc = ingest_text(text, title=Path(filename).stem, source=filename, source_type="upload")
        return [doc]
