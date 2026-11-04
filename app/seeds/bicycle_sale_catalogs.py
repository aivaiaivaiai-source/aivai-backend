"""Brand/model SoT for Bicycle L1 sale subtypes.

Parts bicycle brands live in parts_vehicle_catalogs (VehicleType.bicycle).
Kids bikes are out of Transport — Kids World (do not seed VehicleType.kids_bike here).
"""
from __future__ import annotations

from app.models.category_enums import VehicleType

# (slug, name, country, vehicle_type)
BICYCLE_SALE_BRANDS: list[tuple[str, str, str | None, VehicleType]] = [
    # Mountain
    ("trek-mtb", "Trek", "USA", VehicleType.mountain_bike),
    ("giant-mtb", "Giant", "Taiwan", VehicleType.mountain_bike),
    ("specialized-mtb", "Specialized", "USA", VehicleType.mountain_bike),
    ("merida-mtb", "Merida", "Taiwan", VehicleType.mountain_bike),
    ("canyon-mtb", "Canyon", "Germany", VehicleType.mountain_bike),
    ("cube-mtb", "CUBE", "Germany", VehicleType.mountain_bike),
    ("scott-mtb", "Scott", "Switzerland", VehicleType.mountain_bike),
    ("cannondale-mtb", "Cannondale", "USA", VehicleType.mountain_bike),
    ("author-mtb", "Author", "Czech", VehicleType.mountain_bike),
    ("stels-mtb", "Stels", "Russia", VehicleType.mountain_bike),
    ("forward-mtb", "Forward", "Russia", VehicleType.mountain_bike),
    ("format-mtb", "Format", "Russia", VehicleType.mountain_bike),
    ("aspect-mtb", "Aspect", "Russia", VehicleType.mountain_bike),
    ("gt-mtb", "GT", "USA", VehicleType.mountain_bike),
    ("gestalt-mtb", "Gestalt", "KG", VehicleType.mountain_bike),
    ("phoenix-mtb", "Phoenix", "China", VehicleType.mountain_bike),
    # City
    ("trek-city", "Trek", "USA", VehicleType.city_bike),
    ("giant-city", "Giant", "Taiwan", VehicleType.city_bike),
    ("merida-city", "Merida", "Taiwan", VehicleType.city_bike),
    ("author-city", "Author", "Czech", VehicleType.city_bike),
    ("stels-city", "Stels", "Russia", VehicleType.city_bike),
    ("forward-city", "Forward", "Russia", VehicleType.city_bike),
    ("stern-city", "Stern", "Russia", VehicleType.city_bike),
    ("electra", "Electra", "USA", VehicleType.city_bike),
    ("schwinn-city", "Schwinn", "USA", VehicleType.city_bike),
    ("format-city", "Format", "Russia", VehicleType.city_bike),
    ("aist", "Aist", "Belarus", VehicleType.city_bike),
    ("desna", "Desna", "Russia", VehicleType.city_bike),
    ("gestalt-city", "Gestalt", "KG", VehicleType.city_bike),
    ("pride-city", "Pride", "Ukraine", VehicleType.city_bike),
    # Road
    ("trek-road", "Trek", "USA", VehicleType.road_bike),
    ("specialized-road", "Specialized", "USA", VehicleType.road_bike),
    ("canyon-road", "Canyon", "Germany", VehicleType.road_bike),
    ("merida-road", "Merida", "Taiwan", VehicleType.road_bike),
    ("cube-road", "CUBE", "Germany", VehicleType.road_bike),
    ("scott-road", "Scott", "Switzerland", VehicleType.road_bike),
    ("cannondale-road", "Cannondale", "USA", VehicleType.road_bike),
    ("giant-road", "Giant", "Taiwan", VehicleType.road_bike),
    ("cervelo", "Cervelo", "Canada", VehicleType.road_bike),
    ("pinarello", "Pinarello", "Italy", VehicleType.road_bike),
    ("author-road", "Author", "Czech", VehicleType.road_bike),
    ("format-road", "Format", "Russia", VehicleType.road_bike),
    # Teen (Lalafo chip; kids → Kids World)
    ("stels-teen", "Stels", "Russia", VehicleType.teen_bike),
    ("forward-teen", "Forward", "Russia", VehicleType.teen_bike),
    ("format-teen", "Format", "Russia", VehicleType.teen_bike),
    ("author-teen", "Author", "Czech", VehicleType.teen_bike),
    ("giant-teen", "Giant", "Taiwan", VehicleType.teen_bike),
    ("trek-teen", "Trek", "USA", VehicleType.teen_bike),
    ("aspect-teen", "Aspect", "Russia", VehicleType.teen_bike),
    ("pride-teen", "Pride", "Ukraine", VehicleType.teen_bike),
    ("gestalt-teen", "Gestalt", "KG", VehicleType.teen_bike),
    ("merida-teen", "Merida", "Taiwan", VehicleType.teen_bike),
    # E-bike (Lalafo chip)
    ("xiaomi-ebike", "Xiaomi", "China", VehicleType.e_bike),
    ("himo", "Himo", "China", VehicleType.e_bike),
    ("ado", "ADO", "China", VehicleType.e_bike),
    ("engwe", "Engwe", "China", VehicleType.e_bike),
    ("samebike", "Samebike", "China", VehicleType.e_bike),
    ("fiido", "Fiido", "China", VehicleType.e_bike),
    ("likebike", "Like.Bike", "Russia", VehicleType.e_bike),
    ("stels-ebike", "Stels", "Russia", VehicleType.e_bike),
    ("forward-ebike", "Forward", "Russia", VehicleType.e_bike),
    ("trek-ebike", "Trek", "USA", VehicleType.e_bike),
    ("giant-ebike", "Giant", "Taiwan", VehicleType.e_bike),
    ("specialized-ebike", "Specialized", "USA", VehicleType.e_bike),
    ("cube-ebike", "CUBE", "Germany", VehicleType.e_bike),
    ("tern-ebike", "Tern", "Taiwan", VehicleType.e_bike),
    ("gazelle", "Gazelle", "Netherlands", VehicleType.e_bike),
    ("phillips-ebike", "Phillips", None, VehicleType.e_bike),
    ("kugoo-ebike", "Kugoo", "China", VehicleType.e_bike),
    # BMX
    ("gt-bmx", "GT", "USA", VehicleType.bmx),
    ("cult", "Cult", "USA", VehicleType.bmx),
    ("sunday", "Sunday", "USA", VehicleType.bmx),
    ("haro", "Haro", "USA", VehicleType.bmx),
    ("mongoose", "Mongoose", "USA", VehicleType.bmx),
    ("stolen", "Stolen", "USA", VehicleType.bmx),
    ("fiend", "Fiend", "USA", VehicleType.bmx),
    ("odyssey", "Odyssey", "USA", VehicleType.bmx),
    ("stels-bmx", "Stels", "Russia", VehicleType.bmx),
    ("author-bmx", "Author", "Czech", VehicleType.bmx),
    ("wethepeople-bmx", "WeThePeople", "Germany", VehicleType.bmx),
    # Other bicycles (folding / rare / misc) — gravel/fixie are types, not brands
    ("brompton", "Brompton", "UK", VehicleType.other_bicycle),
    ("tern", "Tern", "Taiwan", VehicleType.other_bicycle),
    ("dahon", "Dahon", "USA", VehicleType.other_bicycle),
    ("strida", "Strida", "UK", VehicleType.other_bicycle),
    ("stels-other-bike", "Stels", "Russia", VehicleType.other_bicycle),
    ("forward-other-bike", "Forward", "Russia", VehicleType.other_bicycle),
    ("format-other-bike", "Format", "Russia", VehicleType.other_bicycle),
    ("xiaomi-bike", "Xiaomi", "China", VehicleType.other_bicycle),
    # Catch-all «Другая марка» per typed sale catalog (optional brand UX)
    ("other-mountain-bike", "Другая марка", None, VehicleType.mountain_bike),
    ("other-city-bike", "Другая марка", None, VehicleType.city_bike),
    ("other-road-bike", "Другая марка", None, VehicleType.road_bike),
    ("other-teen-bike", "Другая марка", None, VehicleType.teen_bike),
    ("other-e-bike", "Другая марка", None, VehicleType.e_bike),
    ("other-bmx", "Другая марка", None, VehicleType.bmx),
    ("other-other-bicycle", "Другая марка", None, VehicleType.other_bicycle),
]

BICYCLE_SALE_MODELS: dict[str, list[tuple[str, str]]] = {
    "trek-mtb": [
        ("marlin", "Marlin"),
        ("roscoe", "Roscoe"),
        ("fuel-ex", "Fuel EX"),
        ("slash", "Slash"),
    ],
    "giant-mtb": [
        ("talon", "Talon"),
        ("atx", "ATX"),
        ("stance", "Stance"),
        ("trance", "Trance"),
    ],
    "specialized-mtb": [
        ("rockhopper", "Rockhopper"),
        ("chisel", "Chisel"),
        ("stumpjumper", "Stumpjumper"),
        ("epic", "Epic"),
    ],
    "merida-mtb": [
        ("big-seven", "Big.Seven"),
        ("big-nine", "Big.Nine"),
        ("one-twenty", "One-Twenty"),
        ("ninety-six", "Ninety-Six"),
    ],
    "canyon-mtb": [
        ("grand-canyon", "Grand Canyon"),
        ("neuron", "Neuron"),
        ("spectral", "Spectral"),
        ("strive", "Strive"),
    ],
    "cube-mtb": [
        ("aim", "Aim"),
        ("acid", "Acid"),
        ("stereo", "Stereo"),
        ("reaction", "Reaction"),
    ],
    "scott-mtb": [
        ("aspect", "Aspect"),
        ("scale", "Scale"),
        ("spark", "Spark"),
        ("genius", "Genius"),
    ],
    "cannondale-mtb": [
        ("trail", "Trail"),
        ("habit", "Habit"),
        ("scalpel", "Scalpel"),
        ("jekyll", "Jekyll"),
    ],
    "author-mtb": [
        ("impulse", "Impulse"),
        ("solution", "Solution"),
        ("instinct", "Instinct"),
    ],
    "stels-mtb": [
        ("navigator", "Navigator"),
        ("miss", "Miss"),
        ("pilot", "Pilot"),
    ],
    "forward-mtb": [
        ("apache", "Apache"),
        ("racing", "Racing"),
        ("unit", "Unit"),
    ],
    "format-mtb": [
        ("1212", "1212"),
        ("1412", "1412"),
        ("5312", "5312"),
    ],
    "aspect-mtb": [
        ("nickel", "Nickel"),
        ("ideal", "Ideal"),
        ("spark", "Spark"),
    ],
    "gt-mtb": [
        ("aggressor", "Aggressor"),
        ("avalanche", "Avalanche"),
        ("sensor", "Sensor"),
    ],
    "trek-city": [
        ("fx", "FX"),
        ("verve", "Verve"),
        ("district", "District"),
        ("dual-sport", "Dual Sport"),
    ],
    "giant-city": [
        ("escape", "Escape"),
        ("rove", "Rove"),
        ("flourish", "Flourish"),
    ],
    "merida-city": [
        ("crossway", "Crossway"),
        ("speeder", "Speeder"),
        ("silex", "Silex"),
    ],
    "author-city": [
        ("era", "Era"),
        ("compact", "Compact"),
        ("classic", "Classic"),
    ],
    "stels-city": [
        ("navigator-300", "Navigator 300"),
        ("miss-5000", "Miss 5000"),
        ("breeze", "Breeze"),
    ],
    "forward-city": [
        ("barcelona", "Barcelona"),
        ("seattle", "Seattle"),
        ("hanoi", "Hanoi"),
    ],
    "stern-city": [
        ("energy", "Energy"),
        ("motion", "Motion"),
        ("dynamic", "Dynamic"),
    ],
    "electra": [
        ("townie", "Townie"),
        ("cruiser", "Cruiser"),
        ("loft", "Loft"),
    ],
    "schwinn-city": [
        ("voyageur", "Voyageur"),
        ("suburban", "Suburban"),
        ("traveler", "Traveler"),
    ],
    "format-city": [
        ("5342", "5342"),
        ("5343", "5343"),
        ("9222", "9222"),
    ],
    "aist": [
        ("voyage", "Voyage"),
        ("cruise", "Cruise"),
        ("city", "City"),
    ],
    "desna": [
        ("2510", "2510"),
        ("2700", "2700"),
        ("city", "City"),
    ],
    "trek-road": [
        ("domane", "Domane"),
        ("emonda", "Émonda"),
        ("madone", "Madone"),
        ("checkpoint", "Checkpoint"),
    ],
    "specialized-road": [
        ("allez", "Allez"),
        ("tarmac", "Tarmac"),
        ("rouleur", "Roubaix"),
        ("aethos", "Aethos"),
    ],
    "canyon-road": [
        ("endurace", "Endurace"),
        ("ultimate", "Ultimate"),
        ("aeroad", "Aeroad"),
        ("inflite", "Inflite"),
    ],
    "merida-road": [
        ("scultura", "Scultura"),
        ("reacto", "Reacto"),
        ("ride", "Ride"),
    ],
    "cube-road": [
        ("attain", "Attain"),
        ("agree", "Agree"),
        ("litening", "Litening"),
    ],
    "scott-road": [
        ("addict", "Addict"),
        ("foil", "Foil"),
        ("speedster", "Speedster"),
    ],
    "cannondale-road": [
        ("synapse", "Synapse"),
        ("supersix", "SuperSix"),
        ("caad13", "CAAD13"),
        ("systemsix", "SystemSix"),
    ],
    "giant-road": [
        ("contend", "Contend"),
        ("tcr", "TCR"),
        ("propel", "Propel"),
        ("defy", "Defy"),
    ],
    "cervelo": [
        ("r5", "R5"),
        ("s5", "S5"),
        ("caledonia", "Caledonia"),
    ],
    "pinarello": [
        ("dogma", "Dogma"),
        ("prince", "Prince"),
        ("paris", "Paris"),
    ],
    "author-road": [
        ("aura", "Aura"),
        ("charisma", "Charisma"),
        ("orbit", "Orbit"),
    ],
    "format-road": [
        ("2222", "2222"),
        ("2313", "2313"),
        ("3332", "3332"),
    ],
    "gt-bmx": [
        ("performer", "Performer"),
        ("slammer", "Slammer"),
        ("pro", "Pro"),
    ],
    "cult": [
        ("gateway", "Gateway"),
        ("juvenile", "Juvenile"),
        ("control", "Control"),
    ],
    "sunday": [
        ("blueprint", "Blueprint"),
        ("scout", "Scout"),
        ("primer", "Primer"),
    ],
    "haro": [
        ("downtown", "Downtown"),
        ("sd", "SD"),
        ("midway", "Midway"),
    ],
    "mongoose": [
        ("legion", "Legion"),
        ("title", "Title"),
        ("mode", "Mode"),
    ],
    "stolen": [
        ("sinner", "Sinner"),
        ("stereo", "Stereo"),
        ("agent", "Agent"),
    ],
    "fiend": [
        ("type-a", "Type A"),
        ("type-b", "Type B"),
        ("vapor", "Vapor"),
    ],
    "odyssey": [
        ("springfield", "Springfield"),
        ("r32", "R32"),
    ],
    "stels-bmx": [
        ("pilot-130", "Pilot 130"),
        ("tiger", "Tiger"),
        ("black", "Black"),
    ],
    "author-bmx": [
        ("agang", "A-Gang"),
        ("circus", "Circus"),
        ("descent", "Descent"),
    ],
    "brompton": [
        ("c-line", "C Line"),
        ("p-line", "P Line"),
        ("t-line", "T Line"),
        ("g-line", "G Line"),
    ],
    "tern": [
        ("link", "Link"),
        ("verge", "Verge"),
        ("node", "Node"),
        ("byb", "BYB"),
    ],
    "dahon": [
        ("mariner", "Mariner"),
        ("vybe", "Vybe"),
        ("hit", "Hit"),
        ("mu", "Mu"),
    ],
    "strida": [
        ("lt", "LT"),
        ("sd", "SD"),
        ("evo", "Evo"),
    ],
    "stels-other-bike": [
        ("pilot-950", "Pilot 950"),
        ("folding", "Folding"),
        ("navigator-fold", "Navigator Fold"),
    ],
    "forward-other-bike": [
        ("arsenal", "Arsenal"),
        ("enigma", "Enigma"),
        ("folding", "Folding"),
    ],
    "format-other-bike": [
        ("5343-fold", "5343 Fold"),
        ("9222-fold", "9222 Fold"),
    ],
    "xiaomi-bike": [
        ("qiycle", "Qicycle"),
        ("himo", "Himo"),
        ("folding", "Folding"),
    ],
    "gestalt-mtb": [
        ("mtb-26", "MTB 26"),
        ("mtb-29", "MTB 29"),
        ("trail", "Trail"),
    ],
    "phoenix-mtb": [
        ("mtb-26", "MTB 26"),
        ("mtb-27", "MTB 27.5"),
        ("mtb-29", "MTB 29"),
    ],
    "gestalt-city": [
        ("city", "City"),
        ("comfort", "Comfort"),
        ("folding", "Folding"),
    ],
    "pride-city": [
        ("marvel", "Marvel"),
        ("quadro", "Quadro"),
        ("rocco", "Rocco"),
    ],
    "stels-teen": [
        ("navigator-610", "Navigator 610"),
        ("navigator-630", "Navigator 630"),
        ("miss-6100", "Miss 6100"),
    ],
    "forward-teen": [
        ("apache-1-0", "Apache 1.0"),
        ("racing-1-0", "Racing 1.0"),
        ("unit-1-0", "Unit 1.0"),
    ],
    "format-teen": [
        ("1411", "1411"),
        ("1412", "1412"),
        ("1311", "1311"),
    ],
    "author-teen": [
        ("impulse", "Impulse"),
        ("cosmic", "Cosmic"),
        ("vision", "Vision"),
    ],
    "giant-teen": [
        ("talon-jr", "Talon Jr"),
        ("xtc-jr", "XTC Jr"),
        ("arx", "ARX"),
    ],
    "trek-teen": [
        ("marlin-4", "Marlin 4"),
        ("precaliber-24", "Precaliber 24"),
        ("wahoo-24", "Wahoo 24"),
    ],
    "aspect-teen": [
        ("nickel", "Nickel"),
        ("ideal", "Ideal"),
        ("air", "Air"),
    ],
    "pride-teen": [
        ("marvel", "Marvel"),
        ("rocco", "Rocco"),
        ("quasar", "Quasar"),
    ],
    "gestalt-teen": [
        ("mtb-24", "MTB 24"),
        ("city-24", "City 24"),
    ],
    "merida-teen": [
        ("matts-j", "Matts J"),
        ("dakar", "Dakar"),
    ],
    "xiaomi-ebike": [
        ("qiycle", "Qicycle"),
        ("himo-c20", "Himo C20"),
        ("himo-c26", "Himo C26"),
    ],
    "himo": [
        ("c20", "C20"),
        ("c26", "C26"),
        ("z20", "Z20"),
        ("z26", "Z26"),
    ],
    "ado": [
        ("a20", "A20"),
        ("a20f", "A20F"),
        ("d30", "D30"),
    ],
    "engwe": [
        ("engine-pro", "Engine Pro"),
        ("l20", "L20"),
        ("ep-2-pro", "EP-2 Pro"),
    ],
    "samebike": [
        ("20lvxd30", "20LVXD30"),
        ("louque", "Louque"),
    ],
    "fiido": [
        ("d11", "D11"),
        ("d21", "D21"),
        ("m1-pro", "M1 Pro"),
    ],
    "likebike": [
        ("one", "One"),
        ("city", "City"),
        ("fold", "Fold"),
    ],
    "stels-ebike": [
        ("navigator-e", "Navigator E"),
        ("pilot-e", "Pilot E"),
    ],
    "forward-ebike": [
        ("apache-e", "Apache E"),
        ("unit-e", "Unit E"),
    ],
    "trek-ebike": [
        ("rail", "Rail"),
        ("powerfly", "Powerfly"),
        ("verve-plus", "Verve+"),
    ],
    "giant-ebike": [
        ("explore-eplus", "Explore E+"),
        ("stance-eplus", "Stance E+"),
        ("road-eplus", "Road E+"),
    ],
    "specialized-ebike": [
        ("turbo-levo", "Turbo Levo"),
        ("turbo-vado", "Turbo Vado"),
        ("turbo-como", "Turbo Como"),
    ],
    "cube-ebike": [
        ("stereo-hybrid", "Stereo Hybrid"),
        ("reaction-hybrid", "Reaction Hybrid"),
        ("nuride-hybrid", "Nuride Hybrid"),
    ],
    "tern-ebike": [
        ("gadot", "GSD"),
        ("hsd", "HSD"),
        ("quick-haul", "Quick Haul"),
    ],
    "gazelle": [
        ("ultimate", "Ultimate"),
        ("paris", "Paris"),
        ("medeo", "Medeo"),
    ],
    "phillips-ebike": [
        ("city-e", "City E"),
        ("cargo-e", "Cargo E"),
        ("fold-e", "Fold E"),
    ],
    "kugoo-ebike": [
        ("kirin-v3", "Kirin V3"),
        ("kirin-v2", "Kirin V2"),
        ("m4-pro", "M4 Pro"),
    ],
    "wethepeople-bmx": [
        ("justice", "Justice"),
        ("crs", "CRS"),
        ("envy", "Envy"),
    ],
    "other-mountain-bike": [
        ("other-model", "Другая модель"),
    ],
    "other-city-bike": [
        ("other-model", "Другая модель"),
    ],
    "other-road-bike": [
        ("other-model", "Другая модель"),
    ],
    "other-teen-bike": [
        ("other-model", "Другая модель"),
    ],
    "other-e-bike": [
        ("other-model", "Другая модель"),
    ],
    "other-bmx": [
        ("other-model", "Другая модель"),
    ],
    "other-other-bicycle": [
        ("other-model", "Другая модель"),
    ],
}
