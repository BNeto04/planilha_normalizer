import datetime
import os
import re
import uuid
from typing import Dict, List

from fastapi import BackgroundTasks, FastAPI, HTTPException
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from google.oauth2 import service_account
from pydantic import BaseModel, HttpUrl

from google_sheets_extractor.main import main as run_pipeline

app = FastAPI()

# --- Constants ---
CREDENTIALS_FILE = "./credentials.json"

# --- In-memory store for job statuses ---
job_store: Dict[str, Dict] = {}


# --- Pydantic Models ---
class RunRequest(BaseModel):
    spreadsheet_id: str
    credentials_file: str | None = None
    source_sheets: List[str] | None = None


class RunFromUrlRequest(BaseModel):
    spreadsheet_url: HttpUrl
    source_sheets: List[str] | None = None


class GetSheetsRequest(BaseModel):
    spreadsheet_url: HttpUrl


class GetSheetsResponse(BaseModel):
    spreadsheet_id: str
    sheets: List[str]


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


# --- Helper Functions ---
def _extract_spreadsheet_id(url: str) -> str:
    """Extracts the spreadsheet ID from a Google Sheets URL."""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid Google Sheets URL.")
    return match.group(1)


def _get_sheets_from_spreadsheet(spreadsheet_id: str) -> List[str]:
    """Lists all sheets in a given spreadsheet."""
    try:
        if not os.path.exists(CREDENTIALS_FILE):
            raise FileNotFoundError("credentials.json not found.")

        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        service = build("sheets", "v4", credentials=creds)
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = [sheet["properties"]["title"] for sheet in sheet_metadata.get("sheets", [])]
        return sheets
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RefreshError as e:
        raise HTTPException(status_code=400, detail=f"Invalid credentials: {e}")
    except Exception as e:
        # Catch other potential API errors
        raise HTTPException(status_code=400, detail=f"Failed to access spreadsheet: {e}")


def execute_pipeline_task(job_id: str, spreadsheet_id: str, source_sheets: List[str] | None):
    """Wrapper to run the pipeline and update job status."""
    try:
        run_pipeline(
            spreadsheet_id=spreadsheet_id,
            credentials_file=CREDENTIALS_FILE,
            source_sheets=source_sheets,
        )
        job_store[job_id]["status"] = "completed"
        job_store[job_id]["result"] = "Pipeline executed successfully."
    except Exception as e:
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["result"] = str(e)
    finally:
        job_store[job_id]["finished_at"] = datetime.datetime.utcnow()


# --- Endpoints ---
@app.post("/get-sheets", response_model=GetSheetsResponse)
async def get_sheets(request: GetSheetsRequest):
    """
    Lists all sheets in a spreadsheet given its URL.
    """
    spreadsheet_id = _extract_spreadsheet_id(str(request.spreadsheet_url))
    sheets = _get_sheets_from_spreadsheet(spreadsheet_id)
    return GetSheetsResponse(spreadsheet_id=spreadsheet_id, sheets=sheets)


@app.post("/run-from-url", response_model=JobResponse)
async def run_from_url(request: RunFromUrlRequest, background_tasks: BackgroundTasks):
    """
    Triggers the pipeline from a spreadsheet URL.
    """
    spreadsheet_id = _extract_spreadsheet_id(str(request.spreadsheet_url))
    source_sheets = request.source_sheets

    if not source_sheets:
        source_sheets = _get_sheets_from_spreadsheet(spreadsheet_id)

    job_id = str(uuid.uuid4())
    job_store[job_id] = {
        "status": "running",
        "submitted_at": datetime.datetime.utcnow(),
        "finished_at": None,
        "result": None,
        "spreadsheet_id": spreadsheet_id,
    }

    background_tasks.add_task(execute_pipeline_task, job_id, spreadsheet_id, source_sheets)

    return JobResponse(
        job_id=job_id,
        status="running",
        submitted_at=job_store[job_id]["submitted_at"],
    )


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
        "spreadsheet_id": request.spreadsheet_id,
    }

    # Use the local credentials file by default
    credentials_file = request.credentials_file or CREDENTIALS_FILE

    background_tasks.add_task(
        execute_pipeline_task,
        job_id,
        request.spreadsheet_id,
        request.source_sheets,
    )

    return JobResponse(
        job_id=job_id,
        status="running",
        submitted_at=job_store[job_id]["submitted_at"],
    )


@app.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """
    Retrieves the status of a specific job.
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Add job_id to the dictionary before returning
    response_data = job.copy()
    response_data["job_id"] = job_id
    return StatusResponse(**response_data)


@app.get("/last-report")
async def get_last_report():
    """
    Returns information about the last successfully completed report.
    """
    completed_jobs = [
        job for job in job_store.values() if job.get("status") == "completed"
    ]
    if not completed_jobs:
        raise HTTPException(status_code=404, detail="No completed reports found.")

    last_job = max(completed_jobs, key=lambda x: x["finished_at"])
    return {
        "spreadsheet_id": last_job.get("spreadsheet_id"),
        "finished_at": last_job.get("finished_at"),
    }