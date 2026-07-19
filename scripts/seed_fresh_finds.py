# ruff: noqa: T201
"""Idempotent development-data seeder for the Fresh Finds storefront.

Creates a minimal demo catalog (categories, product type, products with variants,
channel listings and stock) so a local storefront has something to render.

Safe to run repeatedly: every object is looked up before creation.
Intended for development and staging only — never run against production data
you care about without reviewing the objects it creates.

Usage:
    python scripts/seed_fresh_finds.py
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

from django.utils import timezone  # noqa: E402
from django.utils.text import slugify  # noqa: E402

from saleor.channel.models import Channel  # noqa: E402
from saleor.product.models import (  # noqa: E402
    Category,
    Product,
    ProductChannelListing,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
)
from saleor.warehouse.models import Stock, Warehouse  # noqa: E402

DEFAULT_STOCK_QUANTITY = 100

PRODUCTS = [
    {"name": "Organic Red Apple", "category": "Fruits", "price": "1.50"},
    {"name": "Fresh Bananas", "category": "Fruits", "price": "0.50"},
    {"name": "Baby Carrots", "category": "Vegetables", "price": "2.00"},
    {"name": "Green Broccoli", "category": "Vegetables", "price": "1.75"},
]


def seed():
    channel = Channel.objects.filter(slug="default-channel").first()
    if not channel:
        channel = Channel.objects.create(
            name="Default Channel",
            slug="default-channel",
            currency_code="USD",
            is_active=True,
        )
    print(f"Using channel: {channel.slug} ({channel.currency_code})")

    warehouse = Warehouse.objects.first()
    if not warehouse:
        warehouse = Warehouse.objects.create(
            name="Default Warehouse", slug="default-warehouse"
        )
    print(f"Using warehouse: {warehouse.name}")

    categories = {}
    for name in ("Fruits", "Vegetables"):
        categories[name], _ = Category.objects.get_or_create(
            name=name, defaults={"slug": slugify(name)}
        )
    print("Categories ensured.")

    product_type, _ = ProductType.objects.get_or_create(
        name="Fresh Produce",
        defaults={
            "slug": "fresh-produce",
            "has_variants": True,
            "is_shipping_required": True,
        },
    )
    print("Product type ensured.")

    now = timezone.now()
    for item in PRODUCTS:
        product, created = Product.objects.get_or_create(
            name=item["name"],
            defaults={
                "slug": slugify(item["name"]),
                "category": categories[item["category"]],
                "product_type": product_type,
            },
        )

        ProductChannelListing.objects.get_or_create(
            product=product,
            channel=channel,
            defaults={
                "is_published": True,
                "published_at": now,
                "visible_in_listings": True,
                "available_for_purchase_at": now,
                "currency": channel.currency_code,
            },
        )

        variant, _ = ProductVariant.objects.get_or_create(
            product=product,
            sku=f"SKU-{slugify(item['name'])}",
            defaults={"name": "Standard"},
        )

        ProductVariantChannelListing.objects.get_or_create(
            variant=variant,
            channel=channel,
            defaults={
                "price_amount": item["price"],
                "discounted_price_amount": item["price"],
                "currency": channel.currency_code,
            },
        )

        Stock.objects.get_or_create(
            warehouse=warehouse,
            product_variant=variant,
            defaults={"quantity": DEFAULT_STOCK_QUANTITY},
        )

        print(f"{'Created' if created else 'Ensured'} product: {product.name}")

    print("Seeding complete.")


if __name__ == "__main__":
    seed()
