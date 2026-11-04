"""One-off E2E smoke for Substage 3C-1 user intent API."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
LAN = "http://192.168.1.15:8000"
PHONE = "+79001234567"


def req(
    method: str,
    path: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    base: str = BASE,
) -> tuple[int, dict | str | None]:
    url = f"{base}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


def main() -> int:
    results: list[str] = []
    ok = True

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        status = "PASS" if cond else "FAIL"
        if not cond:
            ok = False
        line = f"{status} {name}" + (f" — {detail}" if detail else "")
        results.append(line)
        print(line)

    code, health = req("GET", "/api/v1/health")
    check("health localhost", code == 200, str(health))

    code, lan_health = req("GET", "/api/v1/health", base=LAN)
    check("health LAN", code == 200, str(lan_health))

    code, login = req(
        "POST",
        "/api/v1/auth/login",
        body={"phone": PHONE, "full_name": "E2E Intent"},
    )
    check("login", code == 200 and isinstance(login, dict) and "access_token" in login)
    if not isinstance(login, dict) or "access_token" not in login:
        print("\n".join(results))
        return 1
    token = login["access_token"]

    code, anon = req("PUT", "/api/v1/listings/1/user-intent", body={"raw_intent_text": "x"})
    check("anonymous PUT forbidden", code in (401, 403), str(anon))

    code, draft = req(
        "POST",
        "/api/v1/listings",
        token=token,
        body={
            "title": "E2E intent smoke draft",
            "description": None,
            "price": "0",
            "currency": "KGS",
            "status": "draft",
        },
    )
    check("create draft", code == 201 and isinstance(draft, dict))
    if not isinstance(draft, dict):
        print("\n".join(results))
        return 1
    listing_id = int(draft["id"])
    initial_category = draft.get("category_id")

    code, missing = req("GET", f"/api/v1/listings/{listing_id}/user-intent", token=token)
    check(
        "GET initial missing",
        code == 200
        and isinstance(missing, dict)
        and missing.get("intent_status") == "missing",
        str(missing),
    )

    code, empty = req(
        "PUT",
        f"/api/v1/listings/{listing_id}/user-intent",
        token=token,
        body={"raw_intent_text": "   "},
    )
    check("empty rejected", code == 422, str(empty))

    code, too_long = req(
        "PUT",
        f"/api/v1/listings/{listing_id}/user-intent",
        token=token,
        body={"raw_intent_text": "x" * 281},
    )
    check("over limit rejected", code == 422, str(too_long))

    phrase1 = "  Продаю КамАЗ  "
    code, put1 = req(
        "PUT",
        f"/api/v1/listings/{listing_id}/user-intent",
        token=token,
        body={"raw_intent_text": phrase1},
    )
    fp1 = put1.get("intent_fingerprint") if isinstance(put1, dict) else None
    ver1 = put1.get("intent_version") if isinstance(put1, dict) else None
    check(
        "PUT phrase1 provided",
        code == 200
        and isinstance(put1, dict)
        and put1.get("intent_status") == "provided"
        and put1.get("raw_intent_text") == "Продаю КамАЗ"
        and fp1
        and ver1 == 1,
        str(put1),
    )

    code, get1 = req("GET", f"/api/v1/listings/{listing_id}/user-intent", token=token)
    check(
        "GET after phrase1",
        code == 200
        and isinstance(get1, dict)
        and get1.get("raw_intent_text") == "Продаю КамАЗ",
        str(get1),
    )

    code, put_idem = req(
        "PUT",
        f"/api/v1/listings/{listing_id}/user-intent",
        token=token,
        body={"raw_intent_text": "Продаю КамАЗ"},
    )
    check(
        "same text idempotent",
        code == 200
        and isinstance(put_idem, dict)
        and put_idem.get("intent_version") == ver1
        and put_idem.get("intent_fingerprint") == fp1,
        str(put_idem),
    )

    code, put2 = req(
        "PUT",
        f"/api/v1/listings/{listing_id}/user-intent",
        token=token,
        body={"raw_intent_text": "Предлагаю грузоперевозки"},
    )
    fp2 = put2.get("intent_fingerprint") if isinstance(put2, dict) else None
    ver2 = put2.get("intent_version") if isinstance(put2, dict) else None
    check(
        "PUT phrase2 revision bump",
        code == 200
        and isinstance(put2, dict)
        and ver2 == (ver1 or 0) + 1
        and fp2
        and fp2 != fp1,
        str(put2),
    )

    code, listing_after = req("GET", f"/api/v1/listings/{listing_id}", token=token)
    cat_after = listing_after.get("category_id") if isinstance(listing_after, dict) else "?"
    check(
        "category unchanged",
        cat_after == initial_category,
        f"before={initial_category} after={cat_after}",
    )

    req("DELETE", f"/api/v1/listings/{listing_id}", token=token)

    print("\n--- SUMMARY ---")
    print("\n".join(results))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
