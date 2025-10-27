from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from api.models import SalesMeta, User, Product
from app.core.jwt import FastJWT
from beanie import PydanticObjectId


product_router = APIRouter(prefix="/products")


@product_router.get("/")
async def list_products(request: Request):
    # TODO: Make middleware to get user from token
    token = await FastJWT().decode(request.headers["Authorization"])
    user = await User.get(token.id)
    if not user:
        raise HTTPException(401, "Unauthorized")
    # TODO: pagination, projection model
    products = await Product.find(
        Product.owner_id == user.id,
    ).to_list()

    products = [
        {**product.model_dump(), "id": str(product.id)} for product in products
    ]

    return products


class ProductCreateRequest(BaseModel):
    title: str
    description: str | None = None
    price: float
    target_price: float | None = None
    note: str | None = None


@product_router.post("/")
async def create_product(request: Request, payload: ProductCreateRequest):
    token = await FastJWT().decode(request.headers["Authorization"])
    user = await User.get(token.id)
    if not user:
        raise HTTPException(401, "Unauthorized")

    product = Product(
        title=payload.title,
        description=payload.description,
        bought_price=payload.price,
        target_price=payload.target_price,
        owner_id=user.id,
        note=payload.note,
    )
    await product.save()
    return product


@product_router.get("/{product_id}")
async def get_product(request: Request, product_id: PydanticObjectId):
    token = await FastJWT().decode(request.headers["Authorization"])
    user = await User.get(token.id)
    if not user:
        raise HTTPException(401, "Unauthorized")

    product = await Product.get(product_id)
    if not product or product.owner_id != user.id:
        raise HTTPException(404, "Product not found")

    return product

@product_router.delete("/{product_id}")
async def delete_product(request: Request, product_id: PydanticObjectId):
    token = await FastJWT().decode(request.headers["Authorization"])
    user = await User.get(token.id)
    if not user:
        raise HTTPException(401, "Unauthorized")

    product = await Product.get(product_id)
    if not product or product.owner_id != user.id:
        raise HTTPException(404, "Product not found")

    await product.delete()
    return {"message": "Product deleted successfully"}



class ProductSellRequest(BaseModel):
    sold_price: float

@product_router.post("/{product_id}/sell")
async def sell_product(request: Request, product_id: PydanticObjectId, payload: ProductSellRequest):
    token = await FastJWT().decode(request.headers["Authorization"])
    user = await User.get(token.id)
    if not user:
        raise HTTPException(401, "Unauthorized")

    product = await Product.get(product_id)
    if not product or product.owner_id != user.id:
        raise HTTPException(404, "Product not found")

    product.sold_price = payload.sold_price
    
    await product.save()
    return product


class ProductSalesMetaRequest(BaseModel):
    ebay_link: str | None = None
    vinted_link: str | None = None
    other_link: str | None = None


@product_router.post("/{product_id}/sales_meta")
async def add_sales_meta(request: Request, product_id: PydanticObjectId, payload: ProductSalesMetaRequest):
    token = await FastJWT().decode(request.headers["Authorization"])
    user = await User.get(token.id)
    if not user:
        raise HTTPException(401, "Unauthorized")

    product = await Product.get(product_id)
    if not product or product.owner_id != user.id:
        raise HTTPException(404, "Product not found")

    product.sales_meta = SalesMeta(
        ebay_link=payload.ebay_link,
        vinted_link=payload.vinted_link,
        other_link=payload.other_link,
    )
    
    await product.save()
    return product


class ProductUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    bought_price: float | None = None
    target_price: float | None = None
    note: str | None = None

@product_router.put("/{product_id}")
async def update_product(request: Request, product_id: PydanticObjectId, payload: ProductUpdateRequest):
    token = await FastJWT().decode(request.headers["Authorization"])
    user = await User.get(token.id)
    if not user:
        raise HTTPException(401, "Unauthorized")

    product = await Product.get(product_id)
    if not product or product.owner_id != user.id:
        raise HTTPException(404, "Product not found")

    if payload.title is not None:
        product.title = payload.title
    if payload.description is not None:
        product.description = payload.description
    if payload.bought_price is not None:
        product.bought_price = payload.bought_price
    if payload.target_price is not None:
        product.target_price = payload.target_price
    if payload.note is not None:
        product.note = payload.note
    
    await product.save()
    return product