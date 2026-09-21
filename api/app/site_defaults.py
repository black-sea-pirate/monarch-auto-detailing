PRICE_KEYS = (
    "maintenance",
    "deep",
    "complete",
    "pet_hair",
    "extraction",
    "leather",
    "salt_stain",
    "suv_surcharge",
    "large_vehicle_surcharge",
)


def price(base_price_cents: int) -> dict[str, int | bool | None]:
    return {
        "base_price_cents": base_price_cents,
        "discount_price_cents": None,
        "discount_enabled": False,
    }


DEFAULT_PRICING = {
    "maintenance": price(9900),
    "deep": price(17900),
    "complete": price(24900),
    "pet_hair": price(4500),
    "extraction": price(2500),
    "leather": price(3000),
    "salt_stain": price(3000),
    "suv_surcharge": price(2500),
    "large_vehicle_surcharge": price(5000),
}

DEFAULT_SECTIONS = {
    "pricing_enabled": True,
    "portfolio_enabled": False,
    "founding_offer_enabled": False,
}
