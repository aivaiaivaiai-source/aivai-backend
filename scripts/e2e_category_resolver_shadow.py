"""Live shadow E2E for Category Resolver Substage 3C-3B."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
PHONE = "+79001234567"

CASES = [
    ("Продам КамАЗ", None, {"transport-cargo"}),
    ("Предлагаю грузоперевозки", None, {"services-gruzoperevozki-i-pereezdy"}),
    ("Продам экскаватор", None, {"transport-special-equipment-ekskavatory", "transport-special-equipment"}),
    ("Предлагаю услуги экскаватора", None, {"services-uslugi-spetstehniki"}),
    ("Продам запчасти Toyota", None, {"transport-auto-parts"}),
    ("Услуги сантехника", None, {"services-santehnika"}),
    ("Ищу работу водителем", None, {"jobs-resume", "jobs-rezyume-soiskateley"}),
    ("Нужен водитель", None, {"jobs-vacancies", "jobs-vakansii-bez-opyta"}),
]


def req(method: str, path: str, *, token: str | None = None, body: dict | None = None) -> tuple[int, object]:
    url = f"{BASE}{path}"
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


def main() -> int:
    ok = True
    code, health = req("GET", "/api/v1/health")
    if code != 200:
        print(f"FAIL health {code} {health}")
        return 1

    code, login = req("POST", "/api/v1/auth/login", body={"phone": PHONE, "full_name": "Resolver E2E"})
    if code != 200 or not isinstance(login, dict) or "access_token" not in login:
        print(f"FAIL login {code} {login}")
        return 1
    token = login["access_token"]

    results: list[dict] = []
    for intent_text, _visual, acceptable in CASES:
        time.sleep(1.2)
        code, draft = req(
            "POST",
            "/api/v1/listings",
            token=token,
            body={
                "title": f"E2E resolver: {intent_text[:24]}",
                "description": None,
                "price": "0",
                "currency": "KGS",
                "status": "draft",
            },
        )
        if code != 201 or not isinstance(draft, dict):
            ok = False
            print(f"FAIL create listing for {intent_text!r}: {code} {draft}")
            continue
        listing_id = int(draft["id"])
        category_before = draft.get("category_id")

        code, put = req(
            "PUT",
            f"/api/v1/listings/{listing_id}/user-intent",
            token=token,
            body={"raw_intent_text": intent_text},
        )
        if code not in (200, 201):
            ok = False
            print(f"FAIL PUT intent {intent_text!r}: {code} {put}")
            continue

        code, resolved = req(
            "POST",
            f"/api/v1/listings/{listing_id}/category-resolver/resolve",
            token=token,
        )
        if code != 200 or not isinstance(resolved, dict):
            ok = False
            print(f"FAIL resolve {intent_text!r}: {code} {resolved}")
            continue

        code, got = req("GET", f"/api/v1/listings/{listing_id}/category-resolver", token=token)
        code2, listing_after = req("GET", f"/api/v1/listings/{listing_id}", token=token)
        category_after = listing_after.get("category_id") if isinstance(listing_after, dict) else None

        payload = resolved.get("result") if isinstance(resolved.get("result"), dict) else resolved
        got_payload = got.get("result") if isinstance(got, dict) and isinstance(got.get("result"), dict) else got

        slug = payload.get("suggested_slug") or (
            got_payload.get("suggested_slug") if isinstance(got_payload, dict) else None
        )
        action = (payload.get("intent_semantics") or {}).get("action")
        status = payload.get("status")
        cat_ok = slug in acceptable
        shadow_ok = category_before == category_after
        case_ok = cat_ok and shadow_ok and status in ("suggested", "ambiguous")
        if not case_ok:
            ok = False
        row = {
            "intent": intent_text,
            "action": action,
            "status": status,
            "suggested_slug": slug,
            "acceptable": sorted(acceptable),
            "category_id_before": category_before,
            "category_id_after": category_after,
            "pass": case_ok,
        }
        results.append(row)
        mark = "PASS" if case_ok else "FAIL"
        print(f"{mark} {intent_text!r} -> {slug} ({status}) category_id {category_before}->{category_after}")

    out_path = ".local/resolver_shadow_e2e.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"ok": ok, "cases": results}, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {out_path}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
