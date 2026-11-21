from datetime import datetime
from enum import Enum

from pydantic import AfterValidator, Field
from typing_extensions import Annotated

ShortStr = Annotated[
    str, 
    Field(max_length=100, description="A string no longer than 100 characters")
]

LongStr = Annotated[
    ShortStr, 
    Field(max_length=1000, description="A string no longer than 1000 characters")
]

def validate_year(year: int) -> int:
    current_year = datetime.now().year
    if year > current_year:
        raise ValueError(
            f"Year cannot be later than the current year. ({current_year})"
        )

    return year

Year = Annotated[
    int, Field(description="Year no later than the current"), 
    AfterValidator(validate_year)
]

Id = Annotated[
    int, Field(ge=1, description="Non-negative ID")
]


class BookStatusEnum(str, Enum):
    PLANNING = "planning to read"
    READING = "reading"
    READ = "read"

BookStatus = Annotated[BookStatusEnum, Field(description="Book reading status")]

BookRating = Annotated[
    int, 
    Field(ge=1, le=5, description="Rating from 1 to 5")
]

PaginationLimit = Annotated[int, Field(ge=1, le=100, description="Query records limit")]
PaginationOffset = Annotated[int, Field(ge=0, description="Query offset")]