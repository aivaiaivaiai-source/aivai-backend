"""Home & garden catalog canonicalization (legacy L2 → mobile skeleton)."""
from __future__ import annotations

# Inactive home-garden L2 — superseded / consolidated. Rows stay in DB.
RETIRED_HOME_GARDEN_LEGACY_SLUGS: frozenset[str] = frozenset(
    {
        # Coarse v1
        "home-furniture",
        "home-decor",
        "home-garden-plants",
        # Furniture splits → single «Мебель» (home-garden-mebel-dlya-doma)
        "home-garden-kuhonnaya-mebel",
        "home-garden-matrasy-i-osnovaniya",
        "home-garden-mebel-dlya-sada-i-dachi",
        # Lighting/electrics live under repair-construction / electronics — not home-garden
        "home-garden-osveschenie-i-elektrika-dlya-doma",
        # Decor splits → single «Декор и интерьер»
        "home-garden-sadovyy-dekor",
        "home-garden-prazdnichnyy-i-sezonnyy-dekor",
    }
)

# Canonical active leaf for unified furniture / decor.
HOME_GARDEN_FURNITURE_SLUG = "home-garden-mebel-dlya-doma"
HOME_GARDEN_CARPETS_SLUG = "home-garden-tekstil-i-kovry"
HOME_GARDEN_DECOR_SLUG = "home-garden-dekor-i-interer"

# Alias text that lived on legacy / split L2 → canonical leaf.
HOME_GARDEN_LEGACY_ALIAS_REMAP: dict[str, str] = {
    "диван": "home-garden-mebel-dlya-doma-divany",
    "шкаф": "home-garden-mebel-dlya-doma-shkafy",
    "кровать": "home-garden-mebel-dlya-doma-krovati",
    "стол": "home-garden-mebel-dlya-doma-stoly",
    "мебель": HOME_GARDEN_FURNITURE_SLUG,
    "кухня": HOME_GARDEN_FURNITURE_SLUG,
    "кухонный гарнитур": "home-garden-mebel-dlya-doma-mebelnye-garnitury-kuhonnye-garnitury",
    "матрас": "home-garden-mebel-dlya-doma-matrasy",
    "ортопедический матрас": "home-garden-mebel-dlya-doma-matrasy",
    "шторы": "home-garden-shtory-zhalyuzi-i-karnizy",
    "ковер": "home-garden-tekstil-i-kovry-kovry",
    "коврик": "home-garden-tekstil-i-kovry-kovriki",
    "люстра": "repair-construction-elektrika-i-osveschenie",
    "бра": "repair-construction-elektrika-i-osveschenie",
    "торшер": "repair-construction-elektrika-i-osveschenie",
    "лампа": "repair-construction-elektrika-i-osveschenie",
    "декор": HOME_GARDEN_DECOR_SLUG,
    "садовый декор": HOME_GARDEN_DECOR_SLUG,
    "садовая фигура": "home-garden-dekor-i-interer-sadovye-figury",
    "новогодний декор": "home-garden-tovary-dlya-prazdnikov-novogodnie-tovary-drugoy-novogodniy-dekor",
    "ёлка искусственная": "home-garden-tovary-dlya-prazdnikov-novogodnie-tovary-elki",
    "гирлянда": "home-garden-tovary-dlya-prazdnikov-novogodnie-tovary-novogodnie-girlyandy",
    "растения": "home-garden-komnatnye-rasteniya-i-tsvety",
    "саженцы": "home-garden-sazhentsy-i-rassada",
    "газон": "home-garden-semena-i-posadochnyy-material-semena-gazona",
    "зеркало": "home-garden-zerkala-nastennye-zerkala",
    "газонокосилка": "home-garden-sadovaya-tehnika-gazonokosilki",
    "печь для бани": "home-garden-kaminy-pechi-i-aksessuary-pechi-dlya-bani-i-sauny",
    "веник": "home-garden-tovary-dlya-bani-i-sauny-veniki",
}
