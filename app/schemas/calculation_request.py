from typing import Annotated

from pydantic import BaseModel, Field


class CalculatePiRequest(BaseModel):
    n: Annotated[
        int,
        Field(
            ge=1,
            description="Number of decimal digits to calculate.",
            examples=[100],
        ),
    ]
