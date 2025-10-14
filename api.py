from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from google_sheets_extractor.main import main as run_pipeline

app = FastAPI()

class RunRequest(BaseModel):
    spreadsheet_id: str
    metrics_profile: str | None = None

@app.post("/run")
async def run(request: RunRequest):
    """
    Triggers the data processing pipeline.
    """
    # Set environment variables for the pipeline
    os.environ["SPREADSHEET_ID"] = request.spreadsheet_id
    if request.metrics_profile:
        os.environ["METRICS_CONFIG_FILE"] = request.metrics_profile

    try:
        run_pipeline()
        return {"status": "Pipeline executed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """
    Returns the status of the service.
    """
    return {"status": "ok"}

@app.get("/last-report")
async def get_last_report():
    """
    (Not implemented) Returns information about the last generated report.
    """
    return {"message": "Endpoint not yet implemented."}