from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional

class User(Document):
    username: str
    password_hash: str


class SalesMeta(BaseModel):
    ebay_link: Optional[str] = None
    vinted_link: Optional[str] = None
    other_link: Optional[str] = None


class Product(Document):
    owner_id: PydanticObjectId
    title: str
    description: str
    bought_price: Optional[float] = None
    target_price: float 
    sold_price: Optional[float] = None
    sales_meta: Optional[SalesMeta] = None
    note: Optional[str] = None