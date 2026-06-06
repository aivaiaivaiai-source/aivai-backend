from enum import Enum


class CategoryEntityType(str, Enum):
    """Cross-category semantic type for AI routing (not OLX tree depth)."""

    object = "object"
    service = "service"
    construction = "construction"
    equipment = "equipment"
    raw_material = "raw_material"
    business = "business"
    food = "food"
    animal = "animal"
    job = "job"
    general = "general"


class CategoryFieldType(str, Enum):
    string = "string"
    number = "number"
    decimal = "decimal"
    boolean = "boolean"
    enum = "enum"
    city = "city"
    brand = "brand"
    model = "model"
    year = "year"
    price = "price"


class CategoryFilterType(str, Enum):
    """Advanced/search filters — not used in AI dialogue."""

    range = "range"
    select = "select"
    multi_select = "multi_select"
    boolean = "boolean"
    text = "text"


class CategoryRuleType(str, Enum):
    routing = "routing"
    moderation = "moderation"
    guardrail = "guardrail"
    dialogue = "dialogue"


class ModerationAction(str, Enum):
    allow = "allow"
    block = "block"
    moderation_queue = "moderation_queue"
    warn = "warn"


class VehicleType(str, Enum):
    car = "car"
    truck = "truck"
    motorcycle = "motorcycle"
    special = "special"
    bus = "bus"


class VehicleAliasTarget(str, Enum):
    brand = "brand"
    model = "model"
