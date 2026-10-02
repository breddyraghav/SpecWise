import json
import os

# =========================================================
# DATA
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "products.json")

with open(DATA_PATH, "r", encoding="utf-8") as file:
    products = json.load(file)


# =========================================================
# HELPERS
# =========================================================

def normalize(text):
    return str(text).lower().strip()


def inr(amount):
    return f"₹{int(amount):,}"


def purpose_matches(user_purpose, product_purposes):
    """Exact match (the old substring check matched 'ai' inside 'daily')."""
    wanted = normalize(user_purpose)
    return wanted in [normalize(p) for p in product_purposes]


def budget_points(price, budget, maximum):
    gap = (budget - price) / budget

    if gap >= 0.25:
        factor = 0.92
    elif gap >= 0.15:
        factor = 0.96
    elif gap >= 0.05:
        factor = 1.0
    else:
        factor = 0.98

    return maximum * factor


def budget_reason(price, budget):
    gap = budget - price
    if gap <= 0:
        return "Right at your budget"
    return f"{inr(gap)} under your budget"


def requirement_points(actual, required, maximum):
    """Products already passed the hard filter, so actual >= required."""
    if required <= 0:
        return maximum
    ratio = actual / required
    factor = min(1.0, 0.9 + 0.1 * (ratio - 1) / 0.25)
    return maximum * factor


def level_points(actual, target, maximum):
    """Reward products close to the wanted level.
    Falling short is penalised fully, exceeding it only lightly."""
    diff = actual - target
    penalty = -diff / 30 if diff < 0 else diff / 30 * 0.25
    return maximum * max(0.0, 1 - penalty)


def display_points(product, preference, maximum):
    if preference == "High Refresh Rate":
        hz = product["refresh_rate"]
        for limit, factor in [(240, 1.0), (165, 0.95), (120, 0.85), (90, 0.5)]:
            if hz >= limit:
                return maximum * factor
        return 0

    if preference == "Large Screen":
        size = product["display_size"]
        for limit, factor in [(17, 1.0), (16, 0.95), (15, 0.75), (14, 0.5)]:
            if size >= limit:
                return maximum * factor
        return maximum * 0.25

    return maximum


# =========================================================
# SCORING ENGINE
# =========================================================

class Scorer:
    """Collects score parts so the UI can show exactly how a match was built."""

    def __init__(self):
        self.parts = []
        self.reasons = []

    def add(self, label, earned, maximum, reason=None):
        self.parts.append(
            {"label": label, "earned": earned, "max": maximum}
        )
        if reason:
            self.reasons.append(reason)

    def note(self, reason):
        self.reasons.append(reason)

    def weighted(self, total, items):
        """items: (label, product_score_out_of_100, user_weight_1_to_10).
        Weights are relative, so the points always add up to `total`."""
        weight_sum = sum(w for _, _, w in items) or 1

        for label, value, weight in items:
            maximum = total * weight / weight_sum
            reason = None
            if value >= 90 and weight >= 7:
                reason = (
                    f"Strong {label.lower()} ({value}/100), "
                    f"which you rated {weight}/10"
                )
            self.add(label, maximum * value / 100, maximum, reason)

    def result(self, product):
        earned = sum(p["earned"] for p in self.parts)
        maximum = sum(p["max"] for p in self.parts)
        return {
            "product": product,
            "score": 100 * earned / maximum if maximum else 0,
            "reasons": self.reasons,
            "breakdown": self.parts,
        }


def run(category, check, build):
    results, rejected = [], []

    for product in products[category]:
        reason = check(product)
        if reason:
            rejected.append({"product": product, "reason": reason})
            continue
        results.append(build(product))

    results.sort(key=lambda item: item["score"], reverse=True)
    return results, rejected


# =========================================================
# MOBILE
# =========================================================

def recommend_mobile(
    budget,
    operating_system,
    minimum_ram,
    minimum_storage,
    priority,
    camera_importance,
    gaming_importance,
    battery_importance,
    performance_importance,
):
    def check(p):
        if p["price"] > budget:
            return f"Over budget by {inr(p['price'] - budget)}"
        if normalize(p["os"]) != normalize(operating_system):
            return f"Runs {p['os']}, not {operating_system}"
        if p["ram"] < minimum_ram:
            return f"Only {p['ram']} GB RAM"
        if p["storage"] < minimum_storage:
            return f"Only {p['storage']} GB storage"
        return None

    def build(p):
        s = Scorer()
        s.add("Budget", budget_points(p["price"], budget, 15), 15,
              budget_reason(p["price"], budget))
        s.add("RAM", requirement_points(p["ram"], minimum_ram, 10), 10,
              f"{p['ram']} GB RAM (you asked for {minimum_ram:g}+)")
        s.add("Storage", requirement_points(p["storage"], minimum_storage, 10), 10,
              f"{p['storage']} GB storage (you asked for {minimum_storage:g}+)")

        matched = purpose_matches(priority, p["purpose"])
        s.add("Main priority", 15 if matched else 0, 15,
              f"Built for {priority.lower()}" if matched else None)

        s.weighted(50, [
            ("Camera", p["camera_score"], camera_importance),
            ("Gaming", p["gaming_score"], gaming_importance),
            ("Battery", p["battery_score"], battery_importance),
            ("Performance", p["performance_score"], performance_importance),
        ])
        return s.result(p)

    return run("mobiles", check, build)


# =========================================================
# LAPTOP
# =========================================================

LAPTOP_LEVELS = {"Basic": 30, "Medium": 50, "High": 70, "Extreme": 90}
GPU_TIER = {
    "integrated": 30,
    "rtx 5060": 70,
    "rtx 5070": 85,
    "rtx professional": 80,
}


def laptop_performance(p):
    """Laptops have no performance field in the JSON, so derive one.
    Better: add a real 'performance_score' to each laptop."""
    perf = GPU_TIER.get(normalize(p["gpu"]), 50)
    cpu = normalize(p["processor"])
    if p["ram"] >= 32:
        perf += 5
    if "ultra 9" in cpu or "ryzen 9" in cpu:
        perf += 5
    return min(perf, 100)


def recommend_laptop(
    budget,
    purpose,
    minimum_ram,
    minimum_storage,
    gpu_required,
    performance_level,
    display_preference,
):
    def check(p):
        if p["price"] > budget:
            return f"Over budget by {inr(p['price'] - budget)}"
        if p["ram"] < minimum_ram:
            return f"Only {p['ram']} GB RAM"
        if p["storage"] < minimum_storage:
            return f"Only {p['storage']} GB storage"
        if gpu_required == "Yes" and normalize(p["gpu"]) == "integrated":
            return "Integrated graphics only"
        return None

    def build(p):
        s = Scorer()
        s.add("Budget", budget_points(p["price"], budget, 20), 20,
              budget_reason(p["price"], budget))

        matched = purpose_matches(purpose, p["purpose"])
        s.add("Purpose", 20 if matched else 0, 20,
              f"Suitable for {purpose.lower()}" if matched else None)

        s.add("RAM", requirement_points(p["ram"], minimum_ram, 15), 15,
              f"{p['ram']} GB RAM (you asked for {minimum_ram:g}+)")
        s.add("Storage", requirement_points(p["storage"], minimum_storage, 10), 10,
              f"{p['storage']} GB storage (you asked for {minimum_storage:g}+)")

        pts = level_points(
            laptop_performance(p), LAPTOP_LEVELS[performance_level], 25
        )
        s.add("Performance", pts, 25,
              f"{p['gpu']} graphics suit {performance_level.lower()} performance"
              if pts >= 20 else None)

        if gpu_required == "Yes":
            s.note(f"Dedicated {p['gpu']} GPU")

        pts = display_points(p, display_preference, 10)
        reason = None
        if display_preference == "High Refresh Rate" and p["refresh_rate"] >= 120:
            reason = f"{p['refresh_rate']} Hz display"
        elif display_preference == "Large Screen" and p["display_size"] >= 16:
            reason = f"Large {p['display_size']} inch display"
        s.add("Display", pts, 10, reason)

        return s.result(p)

    return run("laptops", check, build)


# =========================================================
# BIKE
# =========================================================

BIKE_LEVELS = {"Basic": 72, "Medium": 80, "High": 88, "Extreme": 95}


def recommend_bike(
    budget,
    bike_type,
    purpose,
    performance_level,
    mileage_importance,
    comfort_importance,
    technology_importance,
    abs_required,
):
    def check(p):
        if p["price"] > budget:
            return f"Over budget by {inr(p['price'] - budget)}"
        if normalize(p["type"]) != normalize(bike_type):
            return f"A {p['type']}, not a {bike_type}"
        if abs_required == "Yes" and not p["abs"]:
            return "No ABS"
        return None

    def build(p):
        s = Scorer()
        s.add("Budget", budget_points(p["price"], budget, 20), 20,
              budget_reason(p["price"], budget))

        matched = purpose_matches(purpose, p["purpose"])
        s.add("Purpose", 20 if matched else 0, 20,
              f"Suited to {purpose.lower()}" if matched else None)

        pts = level_points(
            p["performance_score"], BIKE_LEVELS[performance_level], 20
        )
        s.add("Performance", pts, 20,
              f"Performance fits a {performance_level.lower()} level"
              if pts >= 16 else None)

        s.weighted(40, [
            ("Mileage", p["mileage_score"], mileage_importance),
            ("Comfort", p["comfort_score"], comfort_importance),
            ("Technology", p["technology_score"], technology_importance),
        ])

        s.note(f"{bike_type} bike")
        if abs_required == "Yes":
            s.note("Has ABS")

        return s.result(p)

    return run("bikes", check, build)