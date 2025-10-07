import math
import time

from loguru import logger
from mpmath import mp

from app.celery_app import celery_app
from app.schemas.progress_response import ProgressResponse


@celery_app.task(bind=True)
def calculate_pi_task(self, n_digits: int) -> ProgressResponse:
    """Calculate Pi using the most 'efficient' algorithm available:
    calculate Pi immediately, but reveal each digit with exponentially
    decreasing delay.

     The delay formula: delay = 5.0 * exp(-8.0 * f), f = (i / n_digits)
    - First digit (f = 0):       5 seconds
    - Middle digit (f = 0.5):   ~0.1 seconds
    - Last digit (f = 1):     ~0.001 seconds

    Args:
        n_digits: Number of decimal digits to calculate.

    Returns:
        ProgressResponse: {state, progress, result}
    """
    logger.info(f"Starting Pi calculation for {n_digits} decimals")

    total_chars = n_digits + 1

    mp.dps = n_digits + 10  # Set decimal places precision (with buffer)
    pi_value = mp.nstr(mp.pi, total_chars, strip_zeros=False)

    total_time = 0.0
    for i in range(total_chars):
        progress_ratio = i / max(total_chars - 1, 1)
        delay = 5.0 * math.exp(-8.0 * progress_ratio)

        progress = (i + 1) / total_chars
        self.update_state(
            state="PROGRESS",
            meta={"progress": progress, "result": None},
        )

        time.sleep(delay)
        total_time += delay

        # Log every 10 digits
        if (i + 1) % 10 == 0:
            logger.info(
                f"Still revealing... {i + 1}/{total_chars} digits "
                f"(current delay: {delay:.3f}s)"
            )

    logger.info(
        f"Calculation complete: {pi_value}. (total time: {total_time:.2f}s"
    )

    response = ProgressResponse(
        state="FINISHED",
        progress=1.0,
        result=pi_value,
    )
    return response.model_dump()
