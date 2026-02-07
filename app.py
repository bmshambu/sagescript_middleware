import asyncio
import uuid
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body,BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any, Union
import json
import shutil
import os
from datetime import datetime
from uuid import uuid4
import logging
import traceback
import threading
# Import your existing utilities/config


from tools.save_job import save_scheduled_job
from rq_config import test_generation_queue
from tools.extract_rows import extract_test_cases
from tools.priority_summary import summarize_test_case_priorities
from psycopg.rows import dict_row
from db import get_connection as get_db

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)




app = FastAPI(title="AI-SageScript Backend (FastAPI)")

origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "https://sageui.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# ------------ Pydantic models ------------

class FunctionalTestRequest(BaseModel):
    user_story: str
    acceptance_criteria: str
    # accept the same label names that UI used, or internal keys
    framework_choice: Optional[str] 
    # model_name: Optional[str] 
    # api_key: Optional[str] 
    user_id: int
    project_name: str
    sub_project_name: Optional[str] = None
    description: Optional[str] = None

class FunctionalTestResponse(BaseModel):
    test_cases: List[Dict[str, Any]]
    automation_scripts: Dict[str, Any]

class UnitTestsRequest(BaseModel):
    repo_url: HttpUrl
    # If file_path is omitted, endpoint will clone and return a list of candidate files
    file_path: Optional[str] = None
    # Optionally allow providing raw code directly instead of cloning
    raw_code: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None

class CloneFilesResponse(BaseModel):
    repo_dir: str
    files: List[str]

class GeneratedUnitTestResponse(BaseModel):
    repo_dir: Optional[str]
    file_path: str
    detected_language: Optional[str]
    framework: Optional[str]
    unit_test_code: str
    file_extension: Optional[str]

class CreateProjectRequest(BaseModel):
    name: str
    parentId: str
    user_id: int   # TEMP: later from JWT
    description: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str


# ------------ Helpers ------------

def _map_framework_label_to_key(label: str) -> str:
    framework_map = {
        "Java + Selenium": "java_selenium",
        "JavaScript + TestComplete": "js_testcomplete",
        # keep same mapping as your Streamlit app
    }

# ------------ Endpoints ------------
from fastapi import HTTPException

@app.post("/api/login")
async def login(req: LoginRequest):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 1. Fetch user by email or display name
            cur.execute(
                """
                SELECT u.user_id, u.display_name, u.email, u.status
                FROM users u
                WHERE u.email = %s OR u.display_name = %s
                """,
                (req.username, req.username)
            )
            user = cur.fetchone()

            if not user:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            if user["status"] != "active":
                raise HTTPException(status_code=403, detail="User inactive or locked")

            # 2. Fetch credentials
            cur.execute(
                """
                SELECT password_hash
                FROM user_credentials
                WHERE user_id = %s
                """,
                (user["user_id"],)
            )
            creds = cur.fetchone()

            if not creds:
                raise HTTPException(status_code=401, detail="Credentials not found")

            # ⚠ TEMP: plain comparison for testers
            if req.password != creds["password_hash"]:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # 3. Fetch tenant access
            cur.execute(
                """
                SELECT
                    t.tenant_id,
                    t.tenant_name,
                    tua.access_role,
                    tua.access_level
                FROM tenant_user_access tua
                JOIN tenants t ON t.tenant_id = tua.tenant_id
                WHERE tua.user_id = %s
                  AND tua.status = 'active'
                """,
                (user["user_id"],)
            )
            access = cur.fetchall()

            if not access:
                raise HTTPException(status_code=403, detail="No tenant access")

            return {
                "userId": user["user_id"],
                "displayName": user["display_name"],
                "email": user["email"],
                "tenants": [
                    {
                        "tenantId": row["tenant_id"],
                        "tenantName": row["tenant_name"],
                        "role": row["access_role"],
                        "accessLevel": row["access_level"],
                    }
                    for row in access
                ],
            }

    finally:
        conn.close()

@app.post("/api/projects/create")
async def create_project(req: CreateProjectRequest, request: Request):
    conn = get_db()
    try:
        # 1. Validate user_id
        user_id = getattr(req, "user_id", None)

        if user_id is None:
            raise HTTPException(status_code=400, detail="user_id is required")

        try:
            user_id = int(user_id)
        except Exception:
            raise HTTPException(status_code=400, detail="user_id must be an integer")

        # 2. Prepare fields
        project_name = req.name
        sub_project_name = None if req.parentId == "root" else req.parentId
        description = getattr(req, "description", None)

        # 3. Insert project (PostgreSQL style)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_projects (
                    user_id,
                    project_name,
                    sub_project_name,
                    description
                )
                VALUES (%s, %s, %s, %s)
                RETURNING project_id
                """,
                (
                    user_id,
                    project_name,
                    sub_project_name,
                    description,
                ),
            )

            project_id = cur.fetchone()["project_id"]

        conn.commit()

        return {
            "id": project_id,
            "name": project_name,
            "count": 0,
            "subFolders": [],
        }

    finally:
        conn.close()


from fastapi import HTTPException

@app.get("/api/projects/{username}")
async def get_user_projects(username: str):
    """
    Return list of projects for the user with display_name == username.
    If user not found, returns 404.
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 1. Fetch user
            cur.execute(
                """
                SELECT user_id, display_name
                FROM users
                WHERE display_name = %s
                """,
                (username,),
            )
            user = cur.fetchone()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # 2. Fetch projects
            cur.execute(
                """
                SELECT
                    project_id AS id,
                    project_name AS name,
                    sub_project_name
                FROM user_projects
                WHERE user_id = %s
                """,
                (user["user_id"],),
            )
            projects = cur.fetchall()

            result = []
            for row in projects:
                result.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "subFolders": []
                        if not row["sub_project_name"]
                        else [row["sub_project_name"]],
                    }
                )

            return result

    finally:
        conn.close()





@app.post("/api/generate-test-cases")
async def submit_tests(
    payload: Union[FunctionalTestRequest, List[FunctionalTestRequest]]
    #background_tasks: BackgroundTasks
):
    # Normalize input
    payloads = payload if isinstance(payload, list) else [payload]

    # 2️⃣ Convert to dicts
    payload_dicts = [p.model_dump() for p in payloads]

    # 3️⃣ Save job + user stories
    job_id = save_scheduled_job(payload_dicts)


    # 4️⃣ Enqueue async processing
    test_generation_queue.enqueue(
        "worker.generate_functional_tests_job",
        job_id
    )


    return {
        "job_id": job_id,
        "status": "IN_QUEUE",
        "user_story_count": len(payloads)
    }


@app.get("/api/jobs")
async def get_all_jobs():
    jobs_list = []

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    sj.job_id,
                    sj.project_name,
                    sj.description,
                    sj.status,
                    sj.submitted_at,
                    COUNT(ftc.test_case_id) AS test_count
                FROM scheduled_jobs sj
                LEFT JOIN function_test_cases ftc
                    ON sj.job_id = ftc.job_id
                GROUP BY
                    sj.job_id,
                    sj.project_name,
                    sj.description,
                    sj.status,
                    sj.submitted_at
                ORDER BY sj.submitted_at DESC
                """
            )

            rows = cursor.fetchall()
            STATUS_MAP = {
                "IN_QUEUE": "In Queue",
                "IN_PROGRESS": "In Progress",
                "COMPLETED": "Completed",
                "FAILED": "Failed"
            }

            for row in rows:
                jobs_list.append(
                    {
                        "id": row["job_id"],  # UI uses this for the list
                        "project": row["project_name"],
                        "description": row["description"],
                        "status": STATUS_MAP.get(row["status"], "In Queue"),
                        # PostgreSQL returns datetime objects already
                        "submitted": row["submitted_at"].strftime("%b %d, %I:%M %p"),
                        "tests": row["test_count"],
                    }
                )

        return jobs_list

    finally:
        conn.close()


@app.get("/api/jobs/{job_id}")
async def get_job_by_id(job_id: str):
    """
    Fetch job details by job_id.
    """
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # 1️⃣ Fetch job details
            cursor.execute(
                """
                SELECT
                    job_id,
                    project_name,
                    sub_project_name,
                    description,
                    status,
                    submitted_at,
                    framework_choice
                FROM scheduled_jobs
                WHERE job_id = %s
                """,
                (job_id,),
            )
            job = cursor.fetchone()

            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            # 2️⃣ Fetch associated user stories
            cursor.execute(
                """
                SELECT
                    user_story_id,
                    user_story_text,
                    acceptance_criteria
                FROM user_stories
                WHERE job_id = %s
                """,
                (job_id,),
            )
            user_stories = cursor.fetchall()

            stories_list = []

            for story in user_stories:
                # 3️⃣ Fetch functional test cases
                cursor.execute(
                    """
                    SELECT test_case_id, result
                    FROM function_test_cases
                    WHERE user_story_id = %s
                    """,
                    (story["user_story_id"],),
                )
                functional_rows = cursor.fetchall()

                # 4️⃣ Fetch automation scripts
                cursor.execute(
                    """
                    SELECT automation_id, script
                    FROM automation_scripts
                    WHERE user_story_id = %s
                    """,
                    (story["user_story_id"],),
                )
                automation_scripts = cursor.fetchall()

                # 5️⃣ Process test cases
                functional_test_cases = extract_test_cases(functional_rows)
                summary = summarize_test_case_priorities(functional_test_cases)

                stories_list.append(
                    {
                        "user_story_id": story["user_story_id"],
                        "user_story_text": story["user_story_text"],
                        "acceptance_criteria": story["acceptance_criteria"],
                        "functional_test_cases": functional_test_cases,
                        "automation_scripts": automation_scripts,
                        "high_priority_count": summary.get("high", 0),
                        "medium_priority_count": summary.get("medium", 0),
                        "low_priority_count": summary.get("low", 0),
                    }
                )

            return {
                "id": job["job_id"],
                "project": job["project_name"],
                "status": job["status"],
                "test_count": len(stories_list),
            }

    finally:
        conn.close()



@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job by job_id.
    """
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # 1️⃣ Check if job exists
            cursor.execute(
                """
                SELECT job_id
                FROM scheduled_jobs
                WHERE job_id = %s
                """,
                (job_id,),
            )
            job = cursor.fetchone()

            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            # 2️⃣ Delete the job (CASCADE handles children)
            cursor.execute(
                """
                DELETE FROM scheduled_jobs
                WHERE job_id = %s
                """,
                (job_id,),
            )

        conn.commit()

        return {"status": "success", "message": "Job deleted"}

    finally:
        conn.close()





@app.post("/api/jobs/{job_id}/regenerate")
async def regenerate_job(job_id: str, background_tasks: BackgroundTasks):
    """
    Re-submit a job for processing by resetting its status and re-queuing it.
    """
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # 1️⃣ Check if job exists
            cursor.execute(
                """
                SELECT job_id
                FROM scheduled_jobs
                WHERE job_id = %s
                """,
                (job_id,),
            )
            job = cursor.fetchone()

            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            # 2️⃣ Reset job state
            cursor.execute(
                """
                UPDATE scheduled_jobs
                SET status = 'IN_QUEUE',
                    submitted_at = CURRENT_TIMESTAMP
                WHERE job_id = %s
                """,
                (job_id,),
            )

        conn.commit()

        # 3️⃣ Re-trigger processing
        background_tasks.add_task(
            test_generation_queue.enqueue,
            "worker.generate_functional_tests_job",
            job_id,
        )

        return {
            "status": "success",
            "message": "Job sent to queue",
            "job_id": job_id,
        }

    finally:
        conn.close()


@app.get("/api/results/{job_id}")
async def get_job_results(job_id: str):
    # Fetch job from mock DBasync def create_project(req: CreateProjectRequest, request: Request):
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # 1️⃣ Fetch functional test cases for the job
            cursor.execute(
                """
                SELECT
                    ftc.test_case_id,
                    ftc.result
                FROM function_test_cases ftc
                WHERE ftc.job_id = %s
                """,
                (job_id,),
            )
            functional_rows = cursor.fetchall()

            # 2️⃣ Extract test cases
            test_cases = extract_test_cases(functional_rows)
            # 4️⃣ Summarize priorities
            summary = summarize_test_case_priorities(test_cases)

            # 5️⃣ Fetch automation scripts for the job
            cursor.execute(
                """
                SELECT
                    ascr.script
                FROM automation_scripts ascr
                JOIN user_stories us ON ascr.user_story_id = us.user_story_id
                WHERE us.job_id = %s
                """,
                (job_id,),
            )
            automation_rows = cursor.fetchall()

            # 6️⃣ Process automation scripts
            # dict comprehension to store scripts by their 

            automation_scripts = automation_rows[0]["script"] if automation_rows else {}



            # automation_scripts = {
            #     row["automation_id"]: row["script"] for row in automation_rows
            # }
            # automation_scripts = automation_scripts[]
   
            # 3️⃣ Fetch job info
            cursor.execute(
                """
                SELECT
                    job_id,
                    project_name,
                    description,
                    status,
                    submitted_at
                FROM scheduled_jobs
                WHERE job_id = %s
                """,
                (job_id,),
            )   
            job = cursor.fetchone() 
            STATUS_MAP = {
                "IN_QUEUE": "In Queue",
                "IN_PROGRESS": "In Progress",
                "COMPLETED": "Completed",
                "FAILED": "Failed"
            }
            
            job_info= {
                "job_id": job_id,
                "project_name": job["project_name"],
                "description": job["description"],
                "status": STATUS_MAP.get(job["status"], "In Queue"),
                "submitted_at": job["submitted_at"],
                "test_count": len(test_cases)
            }

            return {
                "high_priority_count": summary.get("high", 0),
                "medium_priority_count": summary.get("medium", 0),
                "low_priority_count": summary.get("low", 0),
                "test_cases": test_cases,
                "automation_scripts": automation_scripts,
                "job_info": job_info
            }

    finally:
        conn.close()

@app.get("/api/dashboard/{user_id}")
async def get_dashboard_stats(user_id: int):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 1. Aggregate Top Stats
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM user_projects WHERE user_id = %s) as total_projects,
                    (SELECT COUNT(*) FROM user_projects WHERE user_id = %s AND sub_project_name IS NULL) as root_projects,
                    (SELECT COUNT(*) FROM function_test_cases ftc 
                     JOIN scheduled_jobs sj ON ftc.job_id = sj.job_id 
                     WHERE sj.user_id = %s) as total_test_cases,
                    (SELECT COUNT(*) FROM automation_scripts ascr 
                     JOIN user_stories us ON ascr.user_story_id = us.user_story_id 
                     JOIN scheduled_jobs sj ON us.job_id = sj.job_id 
                     WHERE sj.user_id = %s) as total_scripts
            """, (user_id, user_id, user_id, user_id))
            top_stats = cur.fetchone()

            # 2. Recent Jobs (Last 5)
            cur.execute("""
                SELECT 
                    sj.project_name as name, 
                    sj.description, 
                    sj.status,
                    COUNT(ftc.test_case_id) as test_count
                FROM scheduled_jobs sj
                LEFT JOIN function_test_cases ftc ON sj.job_id = ftc.job_id
                WHERE sj.user_id = %s
                GROUP BY sj.job_id, sj.project_name, sj.description, sj.status, sj.submitted_at
                ORDER BY sj.submitted_at DESC
                LIMIT 5
            """, (user_id,))
            recent_jobs = cur.fetchall()

            # 3. Job Status Breakdown
            cur.execute("""
                SELECT status, COUNT(*) as count
                FROM scheduled_jobs
                WHERE user_id = %s
                GROUP BY status
            """, (user_id,))
            status_rows = cur.fetchall()
            
            # Formatting 
            status_map = {row['status']: row['count'] for row in status_rows}

            return {
                "stats": [
                    { "label": "Total Projects", "value": str(top_stats['total_projects']), "subtext": f"{top_stats['root_projects']} root folders" },
                    { "label": "Test Cases", "value": str(top_stats['total_test_cases']), "subtext": "Generated across all jobs" },
                    { "label": "Automation Scripts", "value": str(top_stats['total_scripts']), "subtext": "Java/Selenium/JS" },
                    { "label": "Active Jobs", "value": str(status_map.get('IN_PROGRESS', 0) + status_map.get('IN_QUEUE', 0)), "subtext": "Currently in pipeline" }
                ],
                "recentJobs": [
                    {
                        "name": job['name'],
                        "description": job['description'] or "No description",
                        "status": job['status'].replace('_', ' ').title(),
                        "testCount": job['test_count']
                    } for job in recent_jobs
                ],
                "jobStatusStats": [
                    { "label": "Completed", "value": status_map.get('COMPLETED', 0), "color": "#10b981" },
                    { "label": "In Progress", "value": status_map.get('IN_PROGRESS', 0), "color": "#f59e0b" },
                    { "label": "In Queue", "value": status_map.get('IN_QUEUE', 0), "color": "#6b7280" }
                ]
            }

    
    
    finally:
        conn.close()
