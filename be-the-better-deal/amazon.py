"""Amazon product data fetcher.

Currently uses mock data for development. To connect to real Amazon data,
replace this with an integration to Keepa API, Rainforest API, Product
Advertising API, or a custom scraper.
"""

import random
from datetime import datetime


def fetch_asin(asin: str) -> dict:
    """Fetch price, deal, and coupon info for an ASIN.

    Returns a dict with: price, list_price, deal_type, deal_details,
    coupon_amount, coupon_code.
    """
    # Mock implementation — simulates variety of deal/coupon scenarios
    base = random.uniform(15, 80)
    price = round(base * (0.7 + random.random() * 0.3), 2)
    list_price = round(price * (1.1 + random.random() * 0.3), 2) if random.random() > 0.3 else None

    deal_type = random.choice([None, None, "Lightning Deal", "Today's Deal", "Prime Day"])
    deal_details = f"Ends in {random.randint(2, 12)}h" if deal_type else None

    coupon_amount = random.choice([None, None, None, "10% off", "$5 off", "15% off"])
    coupon_code = "SAVE10" if coupon_amount and random.random() > 0.6 else None

    return {
        "price": price,
        "list_price": list_price,
        "deal_type": deal_type,
        "deal_details": deal_details,
        "coupon_amount": coupon_amount,
        "coupon_code": coupon_code,
        "fetched_at": datetime.utcnow().isoformat(),
    }
