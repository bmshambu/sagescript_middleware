# save_job.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import get_connection


def save_scheduled_job(payloads: list[dict]) -> int:
    """
    Creates a scheduled job and associated user stories.
    Returns job_id.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            first = payloads[0]

            # 1️⃣ Create scheduled job (PostgreSQL style)
            cursor.execute(
                """
                INSERT INTO scheduled_jobs (
                    user_id,
                    project_name,
                    sub_project_name,
                    description,
                    status,
                    user_story_count,
                    framework_choice
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING job_id
                """,
                (
                    first["user_id"],
                    first["project_name"],
                    first.get("sub_project_name"),
                    first.get("description"),
                    "IN_QUEUE",
                    len(payloads),
                    first["framework_choice"],
                ),
            )

            job_id = cursor.fetchone()["job_id"]

            # 2️⃣ Insert user stories
            for idx, p in enumerate(payloads, start=1):
                user_story_id = f"US-{job_id}-{idx}"

                cursor.execute(
                    """
                    INSERT INTO user_stories (
                        user_story_id,
                        job_id,
                        user_story_text,
                        acceptance_criteria
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        user_story_id,
                        job_id,
                        p["user_story"],
                        p["acceptance_criteria"],
                    ),
                )

        conn.commit()
        return job_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
