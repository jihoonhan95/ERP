import json
import os
from datetime import datetime


DATA_FILE = os.path.join(os.path.dirname(__file__), "../data/sales_data.json")


class SalesManager:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save(self):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_sale(self, date: str, item: str, quantity: int, price: int, category: str = ""):
        record = {
            "id": int(datetime.now().timestamp() * 1000),
            "date": date,
            "item": item,
            "quantity": quantity,
            "price": price,
            "total": quantity * price,
            "category": category,
        }
        self.data.append(record)
        self._save()
        return record

    def delete_sale(self, record_id: int):
        self.data = [r for r in self.data if r["id"] != record_id]
        self._save()

    def update_sale(self, record_id: int, **kwargs):
        for record in self.data:
            if record["id"] == record_id:
                record.update(kwargs)
                if "quantity" in kwargs or "price" in kwargs:
                    record["total"] = record["quantity"] * record["price"]
                break
        self._save()

    def get_all(self):
        return sorted(self.data, key=lambda r: r["date"], reverse=True)

    def filter_by_period(self, start: str, end: str):
        return [r for r in self.data if start <= r["date"] <= end]

    def filter_by_category(self, category: str):
        if not category:
            return self.data
        return [r for r in self.data if r["category"] == category]

    def summary(self, records=None):
        if records is None:
            records = self.data
        total_revenue = sum(r["total"] for r in records)
        total_quantity = sum(r["quantity"] for r in records)
        count = len(records)
        return {
            "total_revenue": total_revenue,
            "total_quantity": total_quantity,
            "count": count,
            "average": total_revenue // count if count else 0,
        }

    def get_categories(self):
        return sorted(set(r["category"] for r in self.data if r["category"]))
