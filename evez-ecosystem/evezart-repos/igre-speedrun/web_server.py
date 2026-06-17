"""EVEZ-OS IGRE Speedrun — Internet Genetic Reverse Engineering & Outcome Projecteering
FastAPI server exposing genome extraction, reverse engineering, and speedrun APIs.
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import time
import os
import sys
import numpy as np
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "disclosure.tools"))

from genome_extractor import GenomeExtractor, InternetGenome, GeneCategory
from outcome_projecteer import OutcomeProjecteer, OutcomeMetric, SpeedrunResult

# Try to import disclosure.tools for cross-integration
try:
    from gap_detector.ingestion import ingest_bytes, ingest_text
    from gap_detector.spectral_engine import SpectralEngine
    from gap_detector.report import generate_report
    DISCLOSURE_AVAILABLE = True
except ImportError:
    DISCLOSURE_AVAILABLE = False

app = FastAPI(
    title="EVEZ-OS IGRE Speedrun",
    version="1.0.0",
    description="Internet Genetic Reverse Engineering & Speedrun Outcome Projecteering",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

extractor = GenomeExtractor(operator="evez666")
projecteer = OutcomeProjecteer(operator="evez666")


@app.get("/health")
def health():
    return {"status": "ok", "service": "igre-speedrun", "version": "1.0.0", "ts": int(time.time())}


# ─── Genome Extraction ─────────────────────────────────────

@app.post("/api/v1/genome/extract")
async def extract_genome(file: UploadFile = File(...)):
    """Upload a document corpus and extract its internet genome."""
    if not DISCLOSURE_AVAILABLE:
        raise HTTPException(status_code=500, detail="disclosure.tools not available for ingestion")

    content = await file.read()
    filename = file.filename or "upload.json"

    docs = ingest_bytes(content, filename)
    documents = [d.to_corpus_entry() for d in docs]

    genome = extractor.extract_from_documents(documents)
    return genome.to_dict()


@app.post("/api/v1/genome/extract/text")
async def extract_genome_text(
    texts: list[str] = Form(...),
    ids: list[str] = Form(None),
):
    """Extract genome from submitted text strings."""
    documents = []
    for i, text in enumerate(texts):
        doc_id = ids[i] if ids and i < len(ids) else f"DOC-{i}"
        documents.append({"id": doc_id, "text": text})

    genome = extractor.extract_from_documents(documents)
    return genome.to_dict()


@app.post("/api/v1/genome/extract/adjacency")
async def extract_genome_adjacency(
    adjacency: list[list[float]] = Form(...),
    labels: list[str] = Form(None),
):
    """Extract genome from a raw adjacency matrix."""
    A = np.array(adjacency)
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise HTTPException(status_code=422, detail="Must provide a square adjacency matrix")

    node_labels = labels if labels else None
    genome = extractor.extract_from_adjacency(A, node_labels)
    return genome.to_dict()


@app.post("/api/v1/genome/compare")
async def compare_genomes(
    genome_a: str = Form(...),
    genome_b: str = Form(...),
):
    """Compare two genomes (provide JSON genome data)."""
    try:
        ga_data = json.loads(genome_a)
        gb_data = json.loads(genome_b)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {e}")

    # Reconstruct minimal genome objects for comparison
    ga = InternetGenome(
        genome_id=ga_data.get("genome_id", "A"),
        timestamp=ga_data.get("timestamp", 0),
        n_nodes=ga_data.get("n_nodes", 0),
        n_edges=ga_data.get("n_edges", 0),
        eigenvalues=ga_data.get("eigenvalues", []),
        phi=ga_data.get("phi", 0),
        eta_star=ga_data.get("eta_star", 0),
        dominant_positive=ga_data.get("dominant_positive", 0),
        dominant_negative=ga_data.get("dominant_negative", 0),
    )
    gb = InternetGenome(
        genome_id=gb_data.get("genome_id", "B"),
        timestamp=gb_data.get("timestamp", 0),
        n_nodes=gb_data.get("n_nodes", 0),
        n_edges=gb_data.get("n_edges", 0),
        eigenvalues=gb_data.get("eigenvalues", []),
        phi=gb_data.get("phi", 0),
        eta_star=gb_data.get("eta_star", 0),
        dominant_positive=gb_data.get("dominant_positive", 0),
        dominant_negative=gb_data.get("dominant_negative", 0),
    )

    comparison = extractor.compare_genomes(ga, gb)
    return comparison


# ─── Speedrun Outcome Projecteering ────────────────────────

@app.post("/api/v1/speedrun/run")
async def run_speedrun(file: UploadFile = File(...)):
    """Upload a document corpus and run a speedrun analysis."""
    if not DISCLOSURE_AVAILABLE:
        raise HTTPException(status_code=500, detail="disclosure.tools not available for ingestion")

    content = await file.read()
    filename = file.filename or "upload.json"

    docs = ingest_bytes(content, filename)
    documents = [d.to_corpus_entry() for d in docs]

    # Extract genome first
    genome = extractor.extract_from_documents(documents)

    # Build adjacency for speedrun
    n = len(documents)
    adjacency = np.zeros((n, n))
    import re
    doc_terms = []
    for doc in documents:
        text = doc.get("text", "")
        terms = set(re.findall(r'[a-z]{4,}', text.lower()))
        doc_terms.append(terms)

    for i in range(n):
        for j in range(n):
            if i != j:
                intersection = len(doc_terms[i] & doc_terms[j])
                union = len(doc_terms[i] | doc_terms[j])
                adjacency[i][j] = intersection / max(union, 1)

    # Run speedrun
    node_labels = [doc.get("id", f"N{i}") for i, doc in enumerate(documents)]
    result = projecteer.speedrun(adjacency, node_labels)

    return {
        "genome": genome.to_dict(),
        "speedrun": result.to_dict(),
    }


@app.post("/api/v1/speedrun/simulate")
async def simulate_intervention(
    adjacency: list[list[float]] = Form(...),
    target_nodes: list[int] = Form(...),
    intervention_type: str = Form("add_edge"),
):
    """Simulate a single intervention on an adjacency matrix."""
    A = np.array(adjacency)
    from outcome_projecteer import Intervention, InterventionType

    try:
        int_type = InterventionType(intervention_type)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid intervention type: {intervention_type}")

    intervention = Intervention(
        id="INT-CUSTOM",
        type=int_type,
        target_nodes=target_nodes,
        description=f"Custom {intervention_type} intervention on nodes {target_nodes}",
    )

    result = projecteer.simulate_intervention(A, intervention)
    return result


# ─── EVEZ-OS Integration ───────────────────────────────────

@app.get("/api/v1/integration/disclosure")
async def cross_disclosure_analysis():
    """Run genome extraction on disclosure.tools demo corpus + speedrun."""
    if not DISCLOSURE_AVAILABLE:
        raise HTTPException(status_code=500, detail="disclosure.tools not available")

    sample_docs = [
        {"id": "AARO-2024-001", "text": "Unidentified anomalous phenomena assessment office report redacted classified", "date": "2024-03"},
        {"id": "AARO-2024-002", "text": "UAP incident report redacted Naval aviation encounter classified sighting", "date": "2024-03"},
        {"id": "AARO-2024-003", "text": "FOIA release AARO historical records review partially redacted", "date": "2024-06"},
        {"id": "AARO-2024-004", "text": "Department of Defense statement on UAP classification top secret", "date": "2024-06"},
        {"id": "AARO-2024-005", "text": "National Archives UAP document release partial gaps in records", "date": "2024-09"},
        {"id": "AARO-2024-006", "text": "Pentagon UAP task force historical analysis volumes 1-9 missing records", "date": "2024-09"},
    ]

    # Extract genome
    genome = extractor.extract_from_documents(sample_docs)

    # Run disclosure spectral analysis
    engine = SpectralEngine(operator="evez666")
    engine.load_corpus(sample_docs)
    spectral = engine.analyze()

    # Speedrun on the same corpus
    n = len(sample_docs)
    import re
    doc_terms = []
    for doc in sample_docs:
        terms = set(re.findall(r'[a-z]{4,}', doc["text"].lower()))
        doc_terms.append(terms)

    adjacency = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                intersection = len(doc_terms[i] & doc_terms[j])
                union = len(doc_terms[i] | doc_terms[j])
                adjacency[i][j] = intersection / max(union, 1)

    node_labels = [doc["id"] for doc in sample_docs]
    speedrun = projecteer.speedrun(adjacency, node_labels)

    return {
        "genome": genome.to_dict(),
        "spectral": spectral,
        "speedrun": speedrun.to_dict(),
        "thesis": "Censorship is the dominant negative eigenvalue. Speedrun = inject information at shadow nodes.",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8099)
