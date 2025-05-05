from pydantic import BaseModel
from typing import List

class Profile(BaseModel):
    name: str
    hobbies: List[str]
    bio: str

# Add more prompt models here as needed

MODEL_MAP = {
    "profile": Profile,
}
