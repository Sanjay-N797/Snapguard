import os
import io
import base64
import time
import traceback
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from services.scanner import get_scanner
from services.redactor import get_redactor
from services.hardware import get_hardware_info
from database.database import get_stats, get_history, delete_history
from config import OUTPUTS_DIR, DATA_DIR

app = FastAPI(title="SnapGuard API", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Store in-memory latest scan cache for session
LATEST_SCAN_CACHE = {}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Server processing error: {str(exc)}"}
    )

@app.get("/")
def read_root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>SnapGuard Web App</h1>")

@app.get("/api/info")
def get_info():
    stats = get_stats()
    hw_info = get_hardware_info()
    return {
        "stats": stats,
        "hardware": hw_info
    }

@app.get("/api/history")
def fetch_history():
    records = get_history(limit=50)
    return {"history": records}

@app.post("/api/history/delete")
def clear_history_log():
    delete_history()
    return {"status": "success", "message": "History cleared."}

@app.post("/api/scan")
async def scan_file_upload(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    filename = file.filename or "uploaded_file.png"
    file_bytes = await file.read()

    scanner = get_scanner()
    result = scanner.scan_file(filename, file_bytes)

    preview_b64 = ""
    if result.get("preview_image") is not None:
        buf = io.BytesIO()
        result["preview_image"].save(buf, format="PNG")
        preview_b64 = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"

    response_payload = {
        "scan_id": result["scan_id"],
        "filename": result["filename"],
        "file_type": result["file_type"],
        "full_text": result["full_text"],
        "findings": result["findings"],
        "risk_analysis": result["risk_analysis"],
        "processing_time": result["processing_time"],
        "ocr_results": result["ocr_results"],
        "ocr_confidence": result.get("ocr_confidence", 0.0),
        "preview_image": preview_b64,
        "redaction_result": result.get("redaction_result", {})
    }

    LATEST_SCAN_CACHE["current"] = {
        "raw_bytes": file_bytes,
        "result": result
    }

    return response_payload

@app.post("/api/scan-demo/{sample_name}")
def scan_demo_file(sample_name: str):
    sample_path = os.path.join(DATA_DIR, "sample_docs", sample_name)
    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail="Sample file not found")

    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    scanner = get_scanner()
    result = scanner.scan_file(sample_name, file_bytes)

    preview_b64 = ""
    if result.get("preview_image") is not None:
        buf = io.BytesIO()
        result["preview_image"].save(buf, format="PNG")
        preview_b64 = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"

    response_payload = {
        "scan_id": result["scan_id"],
        "filename": result["filename"],
        "file_type": result["file_type"],
        "full_text": result["full_text"],
        "findings": result["findings"],
        "risk_analysis": result["risk_analysis"],
        "processing_time": result["processing_time"],
        "ocr_results": result["ocr_results"],
        "ocr_confidence": result.get("ocr_confidence", 0.0),
        "preview_image": preview_b64,
        "redaction_result": result.get("redaction_result", {})
    }

    LATEST_SCAN_CACHE["current"] = {
        "raw_bytes": file_bytes,
        "result": result
    }

    return response_payload

@app.post("/api/redact")
def redact_file():
    if "current" not in LATEST_SCAN_CACHE:
        raise HTTPException(status_code=400, detail="No active scan available")

    cached = LATEST_SCAN_CACHE["current"]
    scan_res = cached["result"]
    raw_bytes = cached["raw_bytes"]

    redactor = get_redactor()
    redact_result = redactor.redact_document(
        original_filename=scan_res["filename"],
        file_type=scan_res["file_type"],
        file_bytes=raw_bytes,
        scan_result=scan_res
    )

    if redact_result.get("is_valid"):
        protected_filename = redact_result["protected_filename"]
        return {
            "status": "success",
            "protected_filename": protected_filename,
            "download_url": f"/api/download/{protected_filename}"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=redact_result.get("error", "Protected file could not be generated. Please try again.")
        )

@app.get("/api/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(OUTPUTS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Protected file not found")
    return FileResponse(file_path, filename=filename, media_type="application/octet-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)
