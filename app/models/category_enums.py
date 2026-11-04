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
    # Create-listing extensions (Jobs pilot → reusable for other L1).
    multi_select = "multi_select"
    time = "time"


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
    agricultural = "agricultural"
    electric = "electric"
    bicycle = "bicycle"
    watercraft = "watercraft"
    trailer = "trailer"
    # Mototechnika L1 sale subtypes (separate brand/model SoT).
    scooter = "scooter"
    motoroller = "motoroller"  # Lalafo «Мотороллеры муравей»
    atv = "atv"
    buggy = "buggy"
    tricycle = "tricycle"
    snowmobile = "snowmobile"
    kart = "kart"
    other_moto = "other_moto"
    # Electric transport L1 sale subtypes (VehicleType.electric stays for parts).
    e_scooter = "e_scooter"  # kick scooters / электросамокаты
    e_moped = "e_moped"  # sit-down city scooters / электроскутеры
    e_motorcycle = "e_motorcycle"
    e_atv = "e_atv"
    hoverboard = "hoverboard"
    monowheel = "monowheel"
    segway = "segway"
    golf_cart = "golf_cart"
    other_electric = "other_electric"
    # Bicycle L1 sale subtypes (VehicleType.bicycle stays for parts).
    mountain_bike = "mountain_bike"
    city_bike = "city_bike"
    road_bike = "road_bike"
    bmx = "bmx"
    e_bike = "e_bike"
    kids_bike = "kids_bike"
    teen_bike = "teen_bike"
    other_bicycle = "other_bicycle"
    # Cargo transport L1 sale subtypes (VehicleType.truck stays for parts).
    dump_truck = "dump_truck"
    tractor_unit = "tractor_unit"
    flatbed_truck = "flatbed_truck"
    box_truck = "box_truck"
    refrigerated_truck = "refrigerated_truck"
    light_truck = "light_truck"
    tanker_truck = "tanker_truck"
    tow_truck = "tow_truck"
    other_truck = "other_truck"
    # Buses L1 sale subtypes (VehicleType.bus stays for full buses + parts).
    microbus = "microbus"
    motorhome = "motorhome"
    # Special equipment L1 sale subtypes (VehicleType.special stays for parts).
    excavator = "excavator"
    loader = "loader"
    truck_crane = "truck_crane"
    aerial_platform = "aerial_platform"
    bulldozer = "bulldozer"
    road_roller = "road_roller"
    grader = "grader"
    manipulator = "manipulator"
    concrete_equipment = "concrete_equipment"
    concrete_mixer = "concrete_mixer"
    concrete_pump = "concrete_pump"
    septic_truck = "septic_truck"
    mini_dumper = "mini_dumper"
    forklift = "forklift"
    municipal = "municipal"
    drilling = "drilling"
    crushing_screening = "crushing_screening"
    attachment = "attachment"
    other_special = "other_special"
    # Farm machinery L1 sale subtypes (VehicleType.agricultural stays for parts).
    tractor = "tractor"
    mini_tractor = "mini_tractor"
    walk_behind = "walk_behind"
    combine = "combine"
    seeder = "seeder"
    potato_planter = "potato_planter"
    # Legacy umbrellas (kept for existing brand rows; new sale uses implement types).
    tillage = "tillage"
    forage = "forage"
    plow = "plow"
    harrow = "harrow"
    cultivator = "cultivator"
    hiller = "hiller"
    ditcher = "ditcher"
    mulcher = "mulcher"
    mower = "mower"
    walk_behind_mower = "walk_behind_mower"
    baler = "baler"
    header = "header"
    rake = "rake"
    feed_mixer = "feed_mixer"
    sprayer = "sprayer"
    fertilizer_spreader = "fertilizer_spreader"
    manure_spreader = "manure_spreader"
    potato_digger = "potato_digger"
    kun = "kun"
    farm_crusher = "farm_crusher"
    grain_thrower = "grain_thrower"
    grain_cleaner = "grain_cleaner"
    film_layer = "film_layer"
    ridge_former = "ridge_former"
    agri_drone = "agri_drone"
    farm_implement = "farm_implement"
    other_agri = "other_agri"
    # Water transport L1 sale subtypes (VehicleType.watercraft stays for parts).
    boat = "boat"
    motorboat = "motorboat"
    yacht = "yacht"
    jet_ski = "jet_ski"
    other_watercraft = "other_watercraft"
    boat_motor = "boat_motor"
    # Trailers L1 sale subtypes (VehicleType.trailer stays for parts).
    drawbar_trailer = "drawbar_trailer"
    semi_trailer = "semi_trailer"
    camper_trailer = "camper_trailer"


class VehicleAliasTarget(str, Enum):
    brand = "brand"
    model = "model"


class VehicleExecution(str, Enum):
    """Listing/model body role: cargo vs passenger (not body style detail)."""

    cargo = "cargo"
    passenger = "passenger"


class VehicleCatalogContext(str, Enum):
    """Picker/catalog filter context (API SoT)."""

    car_sale = "car_sale"
    passenger_parts = "passenger_parts"
    cargo_parts = "cargo_parts"
    bus_parts = "bus_parts"
