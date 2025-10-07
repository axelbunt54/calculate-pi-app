from typing import Annotated

from pydantic import BaseModel, Field


class CalculatePiResponse(BaseModel):
    task_id: Annotated[
        str,
        Field(
            description="Unique task identifier to check progress",
            examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
        ),
    ]
    message: Annotated[
        str,
        Field(
            description="Human-readable message",
            examples=["Pi calculation started"],
        ),
    ]
