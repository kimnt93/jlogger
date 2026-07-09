"""Structured values: nested dicts, lists, and mixed types.

The Rust core serializes nested containers directly to JSON. Use `with_dict`
to merge a whole mapping, or `with_value` for a single field.
"""

import jlogger as jlog

logger = jlog.getLogger("orders")

if __name__ == "__main__":
    order = {
        "id": "ord_1001",
        "items": [
            {"sku": "BTC", "qty": 2, "price": 65000.5},
            {"sku": "ETH", "qty": 10, "price": 3200.0},
        ],
        "tags": ["priority", "vip"],
        "paid": True,
        "coupon": None,
    }

    logger.info() \
        .with_dict(order) \
        .with_value("total", 84000.5) \
        .msg("order placed")

    # Single nested value under one key.
    logger.info() \
        .with_value("customer", {"id": 7, "tier": "gold"}) \
        .msg("customer resolved")
