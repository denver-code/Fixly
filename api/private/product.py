from pathlib import Path
import shutil
from typing import List, Optional
import uuid
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from api.models import SalesMeta, User, Product
from app.core.jwt import FastJWT
from beanie import PydanticObjectId
from app.core.config import config

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

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
        {
            **product.model_dump(),
            "id": str(product.id),
            # Convert image path to URL 
            "images": [
                {
                    "url": f"{config.BASE_URL}api/private/products/{product.id}/images/{Path(img.url).name}",
                    "is_main": img.is_main
                } for img in product.images
            ] if product.images else []
        } for product in products
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
    sold_price: float | None = None
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
    if payload.sold_price is not None:
        product.sold_price = payload.sold_price
    if payload.note is not None:
        product.note = payload.note
    
    await product.save()
    return product

@product_router.post("/{product_id}/images")
async def upload_product_images(
    request: Request,
    product_id: str,
    main_image: UploadFile = File(...),
    other_images: Optional[List[UploadFile]] = File(None)
):
    token = await FastJWT().decode(request.headers["Authorization"])
    user = await User.get(token.id)
    if not user:
        raise HTTPException(401, "Unauthorized")
    product = await Product.get(product_id)
    if not product or product.owner_id != user.id:
        raise HTTPException(404, "Product not found")

    product_dir = UPLOAD_DIR / product_id
    product_dir.mkdir(exist_ok=True)

    main_ext = main_image.filename.split(".")[-1]
    main_filename = f"main_{uuid.uuid4().hex}.{main_ext}"
    main_path = product_dir / main_filename
    with open(main_path, "wb") as f:
        shutil.copyfileobj(main_image.file, f)

    other_paths = []
    if other_images:
        for img in other_images:
            ext = img.filename.split(".")[-1]
            safe_name = f"{uuid.uuid4().hex}.{ext}"
            img_path = product_dir / safe_name
            with open(img_path, "wb") as f:
                shutil.copyfileobj(img.file, f)
            other_paths.append(str(img_path))

    product.images = [{"url": str(main_path), "is_main": True}] + [
        {"url": p, "is_main": False} for p in other_paths
    ]
    await product.save()

    return {"main": str(main_path), "others": other_paths}

# get photo
@product_router.get("/{product_id}/images/{image_name}")
async def get_product_image(request: Request, product_id: PydanticObjectId, image_name: str):
    token = await FastJWT().decode(request.headers["Authorization"])
    user = await User.get(token.id)
    if not user:
        raise HTTPException(401, "Unauthorized")

    product = await Product.get(product_id)
    if not product or product.owner_id != user.id:
        raise HTTPException(404, "Product not found")

    image_path = UPLOAD_DIR / str(product_id) / image_name
    print(image_path)
    if not image_path.exists():
        raise HTTPException(404, "Image not found")

    return FileResponse(image_path)

# delete photos
@product_router.delete("/{product_id}/images/{image_name}")
async def delete_product_image(request: Request, product_id: PydanticObjectId, image_name: str):
    token = await FastJWT().decode(request.headers["Authorization"])
    user = await User.get(token.id)
    if not user:
        raise HTTPException(401, "Unauthorized")

    product = await Product.get(product_id)
    if not product or product.owner_id != user.id:
        raise HTTPException(404, "Product not found")

    image_path = UPLOAD_DIR / product_id / image_name
    if not image_path.exists():
        raise HTTPException(404, "Image not found")

    # Remove image from product images list
    product.images = [img for img in product.images if Path(img.url).name != image_name]
    await product.save()

    # Delete the file
    image_path.unlink()

    return {"message": "Image deleted successfully"}