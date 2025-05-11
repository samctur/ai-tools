from pydantic import BaseModel
from typing import List, Any


# Add more prompt models here as needed
class Recipe(BaseModel):
    title: str
    ingredients: List[str]
    steps: List[str]


class Profile(BaseModel):
    name: str
    hobbies: List[str]
    bio: str


# Define the mapping of model types to Pydantic models
def create_prompt(dto_type: str, obj: Any) -> str:
    if dto_type == "recipe":
        return (
            f"A professional food photography shot of {obj.title}, "
            f"made with {', '.join(obj.ingredients)}. "
            "Served in a beautiful setting. High resolution."
        )
    elif dto_type == "profile":
        return (
            f"Portrait of {obj.name}, who enjoys {', '.join(obj.hobbies)}. "
            f"Bio: {obj.bio}"
        )
    else:
        return f"Prompt data: {obj.dict()}"


MODEL_MAP = {
    "recipe": Recipe,
    "profile": Profile,
}
