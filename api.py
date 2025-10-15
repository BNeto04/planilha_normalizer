from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from google_sheets_extractor.main import main as run_pipeline

app = FastAPI()

class RunRequest(BaseModel):
    spreadsheet_id: str
    credentials_file: str | None = None

@app.post("/run")
async def run(request: RunRequest):
    """
    Triggers the data processing pipeline.
    """
    try:
        # Call the pipeline directly with arguments
        run_pipeline(
            spreadsheet_id=request.spreadsheet_id,
            credentials_file=request.credentials_file
        )
        return {"status": "Pipeline executed successfully."}
    except SystemExit as e:
        # SystemExit is raised on configuration errors, treat as a client error
        return HTTPException(status_code=400, detail=f"Pipeline stopped with exit code {e.code}.")
    except Exception as e:
        # Catch other exceptions as internal server errors
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