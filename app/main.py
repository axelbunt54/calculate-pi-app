from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from loguru import logger

from app.celery_app import celery_app
from app.schemas import (
    CalculatePiRequest,
    CalculatePiResponse,
    ProgressRequest,
    ProgressResponse,
)
from app.tasks.calculate_pi import calculate_pi_task


tags_metadata = [
    {
        "name": "Pi Calculation",
        "description": "Calculate Pi asynchronously and check progress.",
    },
]

app = FastAPI(
    title="Calculate Pi API",
    description=(
        "An asynchronous Pi calculation service with Celery. "
        "Start a calculation task and monitor its progress."
    ),
    version="1.0.0",
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=tags_metadata,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")


@app.post(
    "/calculate_pi",
    summary="Start Pi calculation",
    description=(
        "Initiates an asynchronous calculation of Pi to n decimal places. "
        "Returns a task_id that can be used to check progress."
    ),
    tags=["Pi Calculation"],
    responses={
        200: {
            "description": "Task started successfully",
            "content": {
                "application/json": {
                    "example": {
                        "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "message": "Pi calculation started for 100 digits",
                    }
                }
            },
        },
        422: {"description": "Invalid parameters"},
        500: {
            "description": "Calculation request failed",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to calculate Pi: <reason>"}
                }
            },
        },
    },
)
def calculate_pi(request: CalculatePiRequest) -> CalculatePiResponse:
    """Start asynchronous Pi calculation.

    Args:
        request: Request with number of decimal digits to calculate.

    Returns:
        Task information with task_id for progress tracking.
    """
    logger.info(f"Received request to calculate Pi with {request.n} digits")

    try:
        task = calculate_pi_task.delay(request.n)
        logger.info(f"Task {task.id} started for {request.n} digits")

        return CalculatePiResponse(
            task_id=task.id,
            message=f"Pi calculation started for {request.n} digits",
        )
    except Exception as e:
        logger.error(f"Failed to start task: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start calculation: {str(e)}"
        )


@app.post(
    "/check_progress",
    summary="Check calculation progress",
    description=(
        "Check the progress of a Pi calculation task. "
        "Returns current state, progress (0.0 to 1.0), and result if finished."
    ),
    tags=["Pi Calculation"],
    responses={
        200: {
            "description": "Task status retrieved successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "in_progress": {
                            "summary": "Task in progress",
                            "value": {
                                "state": "PROGRESS",
                                "progress": 0.25,
                                "result": None,
                            },
                        },
                        "finished": {
                            "summary": "Task completed",
                            "value": {
                                "state": "FINISHED",
                                "progress": 1.0,
                                "result": "3.14159265358979323846",
                            },
                        },
                    }
                }
            },
        },
        404: {"description": "Task not found"},
        500: {
            "description": "Failed to check progress",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to check progress: <reason>"}
                }
            },
        },
    },
)
def check_progress(request: ProgressRequest) -> ProgressResponse:
    """Check the progress of a Pi calculation task.

    Args:
        request: Request with task ID returned from calculate_pi endpoint
                 to check progress.

    Returns:
        Current state, progress, and result (if finished).
    """
    logger.info(f"Checking progress for task {request.task_id}")

    try:
        task_result = celery_app.AsyncResult(request.task_id)

        # Check if task exists by examining the backend metadata
        # PENDING with no info means task was never created
        if task_result.state == "PENDING" and task_result.info is None:
            logger.warning(f"Task {request.task_id} not found")
            raise HTTPException(status_code=404, detail="Task not found")

        # Task failed during execution
        if task_result.state == "FAILURE":
            error_info = (
                str(task_result.info) if task_result.info else "Unknown error"
            )
            logger.error(f"Task {request.task_id} failed: {error_info}")
            raise HTTPException(
                status_code=500, detail=f"Task execution failed: {error_info}"
            )

        # Task completed successfully
        if task_result.state == "SUCCESS":
            result_data = task_result.result
            return ProgressResponse(
                state="FINISHED",
                progress=1.0,
                result=result_data.get("result"),
            )

        # Task in progress (STARTED, PROGRESS, or any other state)
        info = task_result.info or {}
        return ProgressResponse(
            state="PROGRESS",
            progress=info.get("progress", 0.0),
            result=None,
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions (like 404)
    except Exception as e:
        logger.error(
            f"Failed to check progress for task {request.task_id}: "
            f"{type(e).__name__}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check task progress: {str(e)}",
        )
