from typing import Annotated, Literal

from pydantic import BaseModel, Field


class ProgressResponse(BaseModel):
    state: Annotated[
        Literal["PROGRESS", "FINISHED"],
        Field(
            description="Current state of the task",
            examples=["PROGRESS"],
        ),
    ]
    progress: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            description="Progress from 0.0 to 1.0",
            examples=[0.25],
        ),
    ]
    result: Annotated[
        str | None,
        Field(
            description="Calculated Pi value as string",
            examples=[None, "3.14159265358979323846"],
        ),
    ]
