from typing import Annotated

from pydantic import BaseModel, Field


class ProgressRequest(BaseModel):
    task_id: Annotated[
        str,
        Field(
            description="Task ID returned from /calculate_pi",
            examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
        ),
    ]
