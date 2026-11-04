"""Brand/model SoT for Water Transport L1 sale subtypes.

Parts watercraft brands live in parts_vehicle_catalogs (VehicleType.watercraft).
"""
from __future__ import annotations

from app.models.category_enums import VehicleType

# (slug, name, country, vehicle_type)
WATER_SALE_BRANDS: list[tuple[str, str, str | None, VehicleType]] = [
    # Boats — лодки
    ("progress", "Прогресс", "Russia", VehicleType.boat),
    ("kazanka", "Казанка", "Russia", VehicleType.boat),
    ("voronezh", "Воронеж", "Russia", VehicleType.boat),
    ("krim", "Крым", "Russia", VehicleType.boat),
    ("quicksilver-boat", "Quicksilver", "Belgium", VehicleType.boat),
    ("yamaha-boat", "Yamaha", "Japan", VehicleType.boat),
    ("walker-bay", "Walker Bay", "USA", VehicleType.boat),
    ("zodiac", "Zodiac", "France", VehicleType.boat),
    ("brig", "BRIG", "Ukraine", VehicleType.boat),
    ("badger", "Badger", "Russia", VehicleType.boat),
    # Motorboats — катера
    ("bayliner-mb", "Bayliner", "USA", VehicleType.motorboat),
    ("searay-mb", "Sea Ray", "USA", VehicleType.motorboat),
    ("quicksilver-mb", "Quicksilver", "Belgium", VehicleType.motorboat),
    ("yamaha-mb", "Yamaha", "Japan", VehicleType.motorboat),
    ("wellcraft", "Wellcraft", "USA", VehicleType.motorboat),
    ("chaparral", "Chaparral", "USA", VehicleType.motorboat),
    ("mastercraft", "MasterCraft", "USA", VehicleType.motorboat),
    ("velvette", "Velvette", "Russia", VehicleType.motorboat),
    ("neat", "NEAT", "Russia", VehicleType.motorboat),
    ("realcraft", "Realcraft", "Russia", VehicleType.motorboat),
    # Yachts
    ("beneteau", "Beneteau", "France", VehicleType.yacht),
    ("jeanneau", "Jeanneau", "France", VehicleType.yacht),
    ("princess", "Princess", "UK", VehicleType.yacht),
    ("sunseeker", "Sunseeker", "UK", VehicleType.yacht),
    ("azimut", "Azimut", "Italy", VehicleType.yacht),
    ("fairline", "Fairline", "UK", VehicleType.yacht),
    ("bavaria", "Bavaria", "Germany", VehicleType.yacht),
    ("hanse", "Hanse", "Germany", VehicleType.yacht),
    ("lagoon", "Lagoon", "France", VehicleType.yacht),
    ("searay-yacht", "Sea Ray", "USA", VehicleType.yacht),
    # Jet skis — manufacturers only (Spark/GTI/Ultra are models, not brands).
    ("sea-doo", "Sea-Doo", "Canada", VehicleType.jet_ski),
    ("yamaha-waverunner", "Yamaha", "Japan", VehicleType.jet_ski),
    ("kawasaki-jetski", "Kawasaki", "Japan", VehicleType.jet_ski),
    ("krash", "KRASH", None, VehicleType.jet_ski),
    ("taiga", "Taiga", "Canada", VehicleType.jet_ski),
    # Other watercraft — craft brands only (no engine manufacturers as craft).
    ("yamaha-other-water", "Yamaha", "Japan", VehicleType.other_watercraft),
    ("sea-doo-other", "Sea-Doo", "Canada", VehicleType.other_watercraft),
    ("bayliner-other", "Bayliner", "USA", VehicleType.other_watercraft),
    ("quicksilver-other", "Quicksilver", "Belgium", VehicleType.other_watercraft),
    ("zodiac-other", "Zodiac", "France", VehicleType.other_watercraft),
    ("progress-other", "Прогресс", "Russia", VehicleType.other_watercraft),
]

WATER_SALE_MODELS: dict[str, list[tuple[str, str]]] = {
    "progress": [
        ("2m", "2М"),
        ("4", "4"),
        ("4m", "4М"),
    ],
    "kazanka": [
        ("5m", "5М"),
        ("5m2", "5М2"),
        ("5m3", "5М3"),
        ("5m4", "5М4"),
    ],
    "voronezh": [
        ("m", "М"),
        ("m-1", "М-1"),
    ],
    "krim": [
        ("m", "М"),
        ("yumsh", "ЮМШ"),
    ],
    "quicksilver-boat": [
        ("activ-455", "Activ 455"),
        ("activ-505", "Activ 505"),
        ("tendy-350", "Tendy 350"),
    ],
    "yamaha-boat": [
        ("242x", "242X"),
        ("ar195", "AR195"),
        ("sx195", "SX195"),
    ],
    "walker-bay": [
        ("generation", "Generation"),
        ("adventure", "Adventure"),
    ],
    "zodiac": [
        ("cadet", "Cadet"),
        ("medline", "Medline"),
        ("pro", "Pro"),
    ],
    "brig": [
        ("falcon", "Falcon"),
        ("eagle", "Eagle"),
        ("navigator", "Navigator"),
    ],
    "badger": [
        ("air-line", "Air Line"),
        ("heavy-duty", "Heavy Duty"),
    ],
    "bayliner-mb": [
        ("element", "Element"),
        ("vr5", "VR5"),
        ("trophy", "Trophy"),
        ("vr6", "VR6"),
    ],
    "searay-mb": [
        ("spx-190", "SPX 190"),
        ("sdx-250", "SDX 250"),
        ("sundancer-265", "Sundancer 265"),
    ],
    "quicksilver-mb": [
        ("activ-555", "Activ 555"),
        ("activ-675", "Activ 675"),
        ("activ-755", "Activ 755"),
    ],
    "yamaha-mb": [
        ("242x-e", "242X E-Series"),
        ("ar250", "AR250"),
        ("sx250", "SX250"),
    ],
    "wellcraft": [
        ("scarab", "Scarab"),
        ("fisherman", "Fisherman"),
    ],
    "chaparral": [
        ("ssi-21", "SSI 21"),
        ("vortex", "Vortex"),
        ("ssi-23", "SSI 23"),
    ],
    "mastercraft": [
        ("x24", "X24"),
        ("nxt22", "NXT22"),
        ("prostar", "ProStar"),
    ],
    "velvette": [
        ("20", "20"),
        ("23", "23"),
        ("classic", "Classic"),
    ],
    "neat": [
        ("460", "460"),
        ("530", "530"),
    ],
    "realcraft": [
        ("510", "510"),
        ("600", "600"),
    ],
    "beneteau": [
        ("oceanis", "Oceanis"),
        ("flyer", "Flyer"),
        ("gran-turismo", "Gran Turismo"),
    ],
    "jeanneau": [
        ("sun-odyssey", "Sun Odyssey"),
        ("cap-camarat", "Cap Camarat"),
        ("leader", "Leader"),
    ],
    "princess": [
        ("v50", "V50"),
        ("f45", "F45"),
        ("y72", "Y72"),
    ],
    "sunseeker": [
        ("predator", "Predator"),
        ("manhattan", "Manhattan"),
        ("portofino", "Portofino"),
    ],
    "azimut": [
        ("atlantis", "Atlantis"),
        ("fly", "Fly"),
        ("s6", "S6"),
    ],
    "fairline": [
        ("targa", "Targa"),
        ("squadron", "Squadron"),
    ],
    "bavaria": [
        ("cruiser", "Cruiser"),
        ("virtess", "Virtess"),
        ("r40", "R40"),
    ],
    "hanse": [
        ("348", "348"),
        ("418", "418"),
        ("508", "508"),
    ],
    "lagoon": [
        ("40", "40"),
        ("42", "42"),
        ("46", "46"),
    ],
    "searay-yacht": [
        ("sundancer", "Sundancer"),
        ("fly", "Fly"),
        ("l-series", "L-Series"),
    ],
    "sea-doo": [
        ("gti", "GTI"),
        ("gtx", "GTX"),
        ("rxp-x", "RXP-X"),
        ("rxt-x", "RXT-X"),
        ("spark", "Spark"),
        ("spark-2up", "Spark 2UP"),
        ("spark-3up", "Spark 3UP"),
        ("spark-trixx", "Spark Trixx"),
        ("gti-130", "GTI 130"),
        ("gti-170", "GTI 170"),
        ("gti-se", "GTI SE"),
    ],
    "yamaha-waverunner": [
        ("vx", "VX"),
        ("fx", "FX"),
        ("gp1800", "GP1800"),
        ("ex", "EX"),
    ],
    "kawasaki-jetski": [
        ("stx-160", "STX 160"),
        ("ultra-310", "Ultra 310"),
        ("sx-r", "SX-R"),
        ("ultra-310lx", "Ultra 310LX"),
        ("ultra-310x", "Ultra 310X"),
    ],
    "krash": [
        ("racer", "Racer"),
        ("sport", "Sport"),
    ],
    "taiga": [
        ("oka", "Oka"),
        ("nomad", "Nomad"),
    ],
    "yamaha-other-water": [
        ("vx", "VX"),
        ("242x", "242X"),
    ],
    "sea-doo-other": [
        ("gti", "GTI"),
        ("spark", "Spark"),
    ],
    "bayliner-other": [
        ("element", "Element"),
        ("vr5", "VR5"),
    ],
    "quicksilver-other": [
        ("activ-555", "Activ 555"),
        ("activ-675", "Activ 675"),
    ],
    "zodiac-other": [
        ("cadet", "Cadet"),
        ("medline", "Medline"),
    ],
    "progress-other": [
        ("2m", "2М"),
        ("4", "4"),
    ],
}
