import base64
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()


class Recipe(BaseModel):
    items: list["Item"]
    total: float = Field(..., description="Total amount of the receipt")
    tag: str = Field(..., description="Single word describing the type of purchase (e.g., Food, Tools, Transportation)")


class Item(BaseModel):
    name: str = Field(..., description="Name should not have any special characters")
    price: float = Field(..., description="Price of the item")


def encode_image(image_path: str) -> str:
    """Encode an image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def generate_response(image_path: str, response_format: BaseModel):
    return client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Extract the data from the receipt"},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Help me extract the receipt information from the following image",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encode_image(image_path)}"
                        },
                    },
                ],
            },
        ],
        response_format=response_format,
    )

if __name__ == "__main__":
    image_path = "receipt.png"
    response = generate_response(
        image_path=image_path,
        response_format= Recipe
    )
    recipe_instance = response.choices[0].message.parsed
    print(recipe_instance)