import base64
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

from sqlalchemy import create_engine, ForeignKey, select
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship, sessionmaker

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


db_path = "sqlite:///receipt.db"
engine = create_engine(db_path)


class Base(DeclarativeBase):
    pass


class DBReceipt(Base):
    __tablename__ = "receipts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    total: Mapped[float] = mapped_column()
    tag: Mapped[str] = mapped_column()

    # Establish a bidirectional relationship with DBItem
    items: Mapped[list["DBItem"]] = relationship("DBItem", back_populates="receipt")

    def __repr__(self):
        return f"<DBReceipt(id={self.id}, total={self.total}, tag={self.tag}, items={self.items})>"


class DBItem(Base):
    __tablename__ = "items"
    item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("receipts.id"))
    name: Mapped[str] = mapped_column()
    price: Mapped[float] = mapped_column()

    # Define the relationship back to DBReceipt
    receipt: Mapped[DBReceipt] = relationship("DBReceipt", back_populates="items")

    def __repr__(self):
        return f"<DBItem(item_id={self.item_id}, name={self.name}, price={self.price})>"


if __name__ == "__main__":
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    image_path = "receipt.png"
    response = generate_response(image_path=image_path, response_format=Recipe)
    recipe_instance = response.choices[0].message.parsed

    session = Session()
    new_receipt = DBReceipt(
        tag=recipe_instance.tag,
        total=recipe_instance.total,
    )
    session.add(new_receipt)
    for item in recipe_instance.items:
        new_item = DBItem(name=item.name, price=item.price, receipt=new_receipt)
        session.add(new_item)
    session.commit()

    # Print receipt:
    stmt = select(DBReceipt).order_by(DBReceipt.id)
    receipts = session.execute(stmt).scalars().all()

    for receipt in receipts:
        print(receipt)