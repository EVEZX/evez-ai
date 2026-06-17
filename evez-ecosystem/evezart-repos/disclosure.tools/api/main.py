from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import tempfile
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gap_detector.spectral import analyze_document, detect_gaps, build_reference_graph, compute_laplacian

app = FastAPI(
    title="disclosure.tools API",
    description="UAP/FOIA eigenforensics gap detection. Negative eigenvalues = missing records.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "online", "product": "disclosure.tools", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "ok", "eta_star": 0.03}


@app.post("/analyze")
async def analyze(
    sections: list[str],
    references: list[list[int]],
    doc_name: str = "unnamed_doc",
):
    """
    Run eigenforensics gap detection on a document graph.
    
    - **sections**: List of document section names
    - **references**: List of [i, j] pairs indicating cross-references between sections  
    - **doc_name**: Name of the document being analyzed
    """
    if len(sections) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 sections")
    
    adj = build_reference_graph(sections, [(r[0], r[1]) for r in references])
    lap = compute_laplacian(adj)
    report = detect_gaps(lap, doc_name, sections)
    return JSONResponse(content=report.to_dict())


@app.post("/analyze/file")
async def analyze_file(file: UploadFile = File(...)):
    """
    Upload a processed doc JSON file and run gap detection.
    """
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Upload a .json file (see corpus/README.md for format)")
    
    content = await file.read()
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.json', delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        report = analyze_document(tmp_path)
        return JSONResponse(content=report.to_dict())
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        os.unlink(tmp_path)
