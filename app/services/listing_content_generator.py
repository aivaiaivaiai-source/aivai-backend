from __future__ import annotations

import re
from typing import Any

from app.core.listing_assistant_rules import MAX_DESCRIPTION_LENGTH
from app.services.category_text import normalize_text

_MEMORY_GB = re.compile(r"\b(\d+)\s*(?:гб|gb)\b", re.I)
_YEAR = re.compile(r"\b((?:19|20)\d{2})\b")
_CONDITION = re.compile(r"\b(хорош\w*|отличн\w*|идеальн\w*|нормальн\w*)\b", re.I)


def _s(val: Any) -> str | None:
    if val is None:
        return None
    t = str(val).strip()
    return t or None


def _category_family(slug: str | None) -> str:
    if not slug:
        return "general"
    if slug.startswith("transport-"):
        return "transport"
    if slug.startswith("animals-"):
        return "animals"
    if slug.startswith("services-"):
        return "services"
    if slug.startswith("real-estate"):
        return "real_estate"
    if slug in ("electronics-phones", "electronics-tablets", "electronics-laptops"):
        return "electronics"
    if slug.startswith("fashion-"):
        return "fashion"
    return "general"


def _capitalize_product_name(raw: str) -> str:
    """Light title cleanup for phones and gadgets."""
    t = raw.strip()
    if not t:
        return t
    replacements = (
        (r"\bайфон\b", "iPhone"),
        (r"\biphone\b", "iPhone"),
        (r"\bсамсунг\b", "Samsung"),
        (r"\bsamsung\b", "Samsung"),
        (r"\bксиаоми\b", "Xiaomi"),
        (r"\bxiaomi\b", "Xiaomi"),
    )
    for pat, rep in replacements:
        t = re.sub(pat, rep, t, flags=re.I)
    t = re.sub(r"\s+", " ", t)
    if re.search(r"\biphone\b", t, re.I):
        t = re.sub(r"\b(\d+)\s*гб\b", r"\1GB", t, flags=re.I)
        t = re.sub(r"\b(\d+)\s*gb\b", r"\1GB", t, flags=re.I)
    return t[:1].upper() + t[1:] if t else t


class ListingContentGenerator:
    """Rule-based title and description generation from known_fields only."""

    @classmethod
    def generate_title(
        cls,
        *,
        seed_text: str,
        known_fields: dict[str, Any],
        category_slug: str | None,
    ) -> str:
        explicit = _s(known_fields.get("title"))
        if explicit:
            return explicit[:120]

        brand = _s(known_fields.get("brand")) or _s(known_fields.get("vehicle_brand"))
        model = _s(known_fields.get("model")) or _s(known_fields.get("vehicle_model"))
        item = _s(known_fields.get("item_type")) or _s(known_fields.get("animal_type"))
        product = _s(known_fields.get("product_type"))
        service = _s(known_fields.get("service_type"))
        year = _s(known_fields.get("year"))
        memory = _s(known_fields.get("memory"))

        family = _category_family(category_slug)

        if family == "transport" and (brand or model):
            parts = [p for p in (brand, model, year) if p]
            return " ".join(parts)[:120]

        if family == "electronics":
            base = seed_text.strip()
            m_mem = _MEMORY_GB.search(seed_text) or _MEMORY_GB.search(normalize_text(seed_text))
            if m_mem and "gb" not in base.lower() and "гб" not in base.lower():
                base = f"{base} {m_mem.group(1)}GB"
            return _capitalize_product_name(base)[:120]

        if family == "animals" and item:
            return f"Продажа: {item}"[:120]

        if family == "services" and (service or item):
            return (service or item)[:120]

        if family == "real_estate":
            rooms = _s(known_fields.get("rooms"))
            deal = _s(known_fields.get("deal_type"))
            if rooms and deal:
                return f"{rooms}-комн., {deal}"[:120]
            if item:
                return item[:120]

        if item:
            return _capitalize_product_name(item)[:120]
        if product:
            return product[:120]

        short_seed = seed_text.strip()
        if len(short_seed) <= 80:
            return _capitalize_product_name(short_seed)[:120]
        return "Объявление на AiVai"[:120]

    @classmethod
    def generate_description(
        cls,
        *,
        title: str,
        known_fields: dict[str, Any],
        category_slug: str | None,
        category_name: str | None,
        seed_text: str = "",
    ) -> str:
        family = _category_family(category_slug)
        city = _s(known_fields.get("city"))
        price = _s(known_fields.get("price"))
        condition = _s(known_fields.get("condition"))
        year = _s(known_fields.get("year"))
        brand = _s(known_fields.get("brand")) or _s(known_fields.get("vehicle_brand"))
        model = _s(known_fields.get("model")) or _s(known_fields.get("vehicle_model"))
        purpose = _s(known_fields.get("purpose"))
        age = _s(known_fields.get("age"))
        item = _s(known_fields.get("item_type")) or _s(known_fields.get("animal_type"))
        size = _s(known_fields.get("size"))
        rooms = _s(known_fields.get("rooms"))
        service = _s(known_fields.get("service_type"))

        cond_hint = ""
        m_cond = _CONDITION.search(seed_text)
        if condition:
            cond_hint = condition
        elif m_cond:
            cond_hint = m_cond.group(1)

        parts: list[str] = []

        if family == "transport":
            subject = " ".join(p for p in (brand, model) if p) or title
            lead = f"Продаётся {subject}"
            if year:
                lead += f", {year} года выпуска"
            if cond_hint:
                lead += f" в {cond_hint} состоянии"
            lead += "."
            parts.append(lead)
            parts.append("Автомобиль готов к осмотру. Уточняйте детали при звонке.")

        elif family == "animals":
            subject = item or title
            lead = f"Продаётся {subject}"
            if age:
                lead += f", возраст {age}"
            if purpose:
                lead += f". Назначение: {purpose}"
            lead += "."
            parts.append(lead)
            parts.append("Животное на месте, возможен осмотр перед покупкой.")

        elif family == "services":
            subject = service or item or title
            parts.append(f"Оказываю услуги: {subject}.")
            parts.append("Работаю аккуратно и в срок. Свяжитесь для уточнения деталей и записи.")

        elif family == "real_estate":
            subject = title
            if rooms:
                subject = f"{rooms}-комнатная квартира"
            parts.append(f"Сдаётся {subject}." if "rent" in (category_slug or "") else f"Продаётся {subject}.")
            parts.append("Подробности по площади и условиям — при обращении.")

        elif family == "electronics":
            parts.append(f"Продаётся {title}")
            if cond_hint:
                parts[-1] += f" в {cond_hint} состоянии"
            parts[-1] += "."
            parts.append(
                "Подходит для повседневного использования, фото, видео и работы. "
                "Устройство полностью рабочее."
            )

        elif family == "fashion":
            parts.append(f"Продаётся {title}.")
            if size:
                parts.append(f"Размер: {size}.")
            if cond_hint:
                parts.append(f"Состояние: {cond_hint}.")
            parts.append("Вещь готова к передаче покупателю.")

        else:
            parts.append(f"Продаётся {title}.")
            if cond_hint:
                parts.append(f"Состояние: {cond_hint}.")
            parts.append("Товар в наличии. Для подробностей напишите или позвоните.")

        if city:
            parts.append(f"Город: {city}.")
        if price:
            parts.append(f"Цена: {price}.")

        text = " ".join(parts)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > MAX_DESCRIPTION_LENGTH:
            text = text[: MAX_DESCRIPTION_LENGTH - 3].rsplit(" ", 1)[0] + "..."
        return text

    @classmethod
    def has_sufficient_fields_for_description(cls, known_fields: dict[str, Any]) -> bool:
        keys = ("city", "price", "brand", "model", "item_type", "title", "year")
        return any(_s(known_fields.get(k)) for k in keys)
