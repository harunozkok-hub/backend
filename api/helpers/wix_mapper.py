def map_wix_product_to_db_model(wix_product: dict) -> dict:
    price_data = wix_product.get("priceData", {})
    discount_data = wix_product.get("discount", {})

    product_data = {
        "wix_id": wix_product.get("id"),
        "name": wix_product.get("name"),
        "description": wix_product.get("description"),
        "visible_in_wix": wix_product.get("visible", True),
        "weight": wix_product.get("weight", 0.0),
        "price": price_data.get("price", 0.0),
        "discounted_price": price_data.get("discountedPrice", 0.0),
        "discounted_type": discount_data.get("type"),
        "discounted_amount": discount_data.get("amount", 0.0),
        "images": [],  # to fill
        "category_ids": wix_product.get("collectionIds"),  # to fill
        "additional_info": [],  # optional
    }

    # Images (media.items -> image.url)

    main_media = wix_product.get("media", {}).get("mainMedia", {})
    image_data = {
        "media_url": main_media.get("thumbnail", {}).get("url", {}),
        "thumbnail_url": main_media.get("thumbnail", {}).get("url", {}),
    }

    if image_data.get("media_url"):
        product_data["images"].append(image_data)

    # Optional: Additional Info
    for section in wix_product.get("additionalInfoSections", []):
        product_data["additional_info"].append(
            {"title": section.get("title"), "description": section.get("description")}
        )

    return product_data
