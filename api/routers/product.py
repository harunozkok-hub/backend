from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, List
from datetime import timedelta
from starlette import status

from services.wix_api_service import wix_post_request
from dependencies.deps import db_dependency, user_dependency
from routers.product_pydantic import ProductSchema, CategoryBase, CategorySchema
from helpers.wix_mapper import map_wix_product_to_db_model
from models import Product, ProductAdditionalInfo, Category, ProductImage


router = APIRouter(prefix="/product", tags=["Product"])


@router.post(
    "/sync-wix-categories",
    status_code=status.HTTP_200_OK,
    response_model=List[CategoryBase],
)
async def sync_wix_categories_route(
    db: db_dependency,
    user: user_dependency,
):
    try:
        data = await wix_post_request("stores/v1/collections/query")
        synced_categories = []

        for item in data.get("collections", []):
            category = db.query(Category).filter_by(wix_id=item["id"]).first()
            if not category:
                category = Category(wix_id=item["id"])

            category.name = item.get("name")
            category.description = item.get("description")
            category.visible_in_wix = item.get("visible", True)
            db.add(category)
            synced_categories.append(category)

        db.commit()
        return synced_categories

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# can be run after syncing categories
@router.post(
    "/sync-wix-products",
    status_code=status.HTTP_200_OK,
    response_model=List[ProductSchema],
)
async def sync_wix_products(user: user_dependency, db: db_dependency):
    try:
        data = await wix_post_request("stores-reader/v1/products/query")
        synced_products = []

        for item in data.get("products", []):
            mapped = map_wix_product_to_db_model(item)

            # Create/update product
            product = db.query(Product).filter_by(wix_id=mapped["wix_id"]).first()
            if not product:
                product = Product(wix_id=mapped["wix_id"])
            for field in [
                "name",
                "description",
                "price",
                "discounted_price",
                "discounted_type",
                "discounted_amount",
                "visible_in_wix",
                "weight",
            ]:
                setattr(product, field, mapped[field])

            db.add(product)
            db.commit()
            db.refresh(product)

            # 3. Replace image(s)
            db.query(ProductImage).filter_by(product_id=product.id).delete()
            for image in mapped["images"]:
                db.add(
                    ProductImage(
                        media_url=image["media_url"],
                        thumbnail_url=image["thumbnail_url"],
                        product_id=product.id,
                    )
                )

            # 4. Replace categories
            product.categories.clear()
            for wix_cat_id in mapped.get("category_ids", []):
                category = db.query(Category).filter_by(wix_id=wix_cat_id).first()
                if category:
                    product.categories.append(category)

            # 5. Replace additional info
            db.query(ProductAdditionalInfo).filter_by(product_id=product.id).delete()
            for info in mapped.get("additional_info", []):
                db.add(
                    ProductAdditionalInfo(
                        title=info["title"],
                        description=info["description"],
                        product_id=product.id,
                    )
                )

            db.commit()
            synced_products.append(product)

        return synced_products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🚀 Get all products
@router.get("/products", response_model=List[ProductSchema])
def get_all_products(db: db_dependency, user: user_dependency):
    products = db.query(Product).all()
    return products


# 🚀 Get single product by ID
@router.get("/product/{id}", response_model=ProductSchema)
def get_product_by_id(id: int, db: db_dependency, user: user_dependency):
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# 📦 Get all categories
@router.get("/categories", response_model=List[CategorySchema])
def get_all_categories(db: db_dependency, user: user_dependency):
    categories = db.query(Category).all()
    return categories


# 📦 Get single category by ID
@router.get("/category/{id}", response_model=CategorySchema)
def get_category_by_id(id: int, db: db_dependency, user: user_dependency):
    category = db.query(Category).filter(Category.id == id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category
