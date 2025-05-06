from pydantic import BaseModel
from typing import List

class Recipe(BaseModel):
    title: str
    ingredients: List[str]
    steps: List[str]

class Profile(BaseModel):
    name: str
    hobbies: List[str]
    bio: str

# Add more prompt models here as needed

MODEL_MAP = {
    "recipe": Recipe,
    "profile": Profile,
}
