from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict
import uuid
import datetime

from google_sheets_extractor.main import main as run_pipeline

app = FastAPI()

# In-memory store for job statuses
job_store: Dict[str, Dict] = {}

# --- Models ---
class RunRequest(BaseModel):
    spreadsheet_id: str
    credentials_file: str | None = None
    source_sheets: List[str] | None = None

class JobResponse(BaseModel):
    job_id: str
    status: str
    submitted_at: datetime.datetime

class StatusResponse(BaseModel):
    job_id: str
    status: str
    submitted_at: datetime.datetime
    finished_at: datetime.datetime | None = None
    result: str | None = None

# --- Helper Function ---
def execute_pipeline_task(job_id: str, request: RunRequest):
    """Wrapper to run the pipeline and update job status."""
    try:
        run_pipeline(
            spreadsheet_id=request.spreadsheet_id,
            credentials_file=request.credentials_file,
            source_sheets=request.source_sheets
        )
        job_store[job_id]["status"] = "completed"
        job_store[job_id]["result"] = "Pipeline executed successfully."
    except Exception as e:
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["result"] = str(e)
    finally:
        job_store[job_id]["finished_at"] = datetime.datetime.utcnow()

# --- Endpoints ---
@app.post("/run", response_model=JobResponse)
async def run(request: RunRequest, background_tasks: BackgroundTasks):
    """
    Triggers the data processing pipeline as a background task.
    """
    job_id = str(uuid.uuid4())
    job_store[job_id] = {
        "status": "running",
        "submitted_at": datetime.datetime.utcnow(),
        "finished_at": None,
        "result": None,
        "spreadsheet_id": request.spreadsheet_id # Store for last-report
    }

    background_tasks.add_task(execute_pipeline_task, job_id, request)

    return JobResponse(
        job_id=job_id,
        status="running",
        submitted_at=job_store[job_id]["submitted_at"]
    )

@app.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """
    Retrieves the status of a specific job.
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return StatusResponse(**job, job_id=job_id)

@app.get("/last-report")
async def get_last_report():
    """
    Returns information about the last successfully completed report.
    """
    # Find the most recent, successfully completed job
    completed_jobs = [
        job for job in job_store.values() if job["status"] == "completed"
    ]
    if not completed_jobs:
        raise HTTPException(status_code=404, detail="No completed reports found.")

    last_job = max(completed_jobs, key=lambda x: x["finished_at"])
    return {
        "spreadsheet_id": last_job.get("spreadsheet_id"),
        "finished_at": last_job.get("finished_at")
    }