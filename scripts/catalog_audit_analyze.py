"""Analyze catalog audit dump."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8-sig")
data = json.loads(next(l for l in text.splitlines() if l.strip().startswith("{")))
cats = data["categories"]
by_id = {c["id"]: c for c in cats}
children: dict[int | None, list[dict]] = defaultdict(list)
for c in cats:
    children[c["parent_id"]].append(c)

for lst in children.values():
    lst.sort(key=lambda x: (x["sort_order"], x["id"]))


def print_tree(node_id: int, indent: int = 0, max_depth: int | None = None) -> None:
    c = by_id[node_id]
    if max_depth is not None and c["depth"] > max_depth:
        return
    meta = (
        f"id={c['id']} slug={c['slug']} active={c['is_active']} "
        f"core={c['core_n']} opt={c['opt_n']} filt={c['filter_n']} rules={c['rule_n']}"
    )
    print("  " * indent + f"- {c['name']} ({meta})")
    for ch in children[node_id]:
        print_tree(ch["id"], indent + 1, max_depth)


print("STATS", json.dumps(data["stats"], ensure_ascii=False))
print("\n=== L1 depth summary ===")
for r in children[None]:
    branch_ids = set()

    def collect(nid: int) -> None:
        branch_ids.add(nid)
        for ch in children[nid]:
            collect(ch["id"])

    collect(r["id"])
    branch = [by_id[i] for i in branch_ids]
    depths = defaultdict(int)
    for c in branch:
        depths[c["depth"]] += 1
    print(
        f"{r['slug']}: total={len(branch)} L2={len(children[r['id']])} "
        f"max_depth={max(c['depth'] for c in branch)} depth_counts={dict(sorted(depths.items()))}"
    )

slug = sys.argv[2] if len(sys.argv) > 2 else "transport"
root = next(c for c in cats if c["slug"] == slug)
print(f"\n=== TREE {slug} (depth<=3) ===")
print_tree(root["id"], max_depth=3)

# readiness
print("\n=== READINESS SAMPLE ===")
for slug_prefix in [
    "transport-car-sale",
    "transport-cargo",
    "transport-special-equipment",
    "services-santehnika",
    "services-elektrika",
    "real-estate-kvartiry",
    "transport-cars",
]:
    c = next((x for x in cats if x["slug"] == slug_prefix), None)
    if c:
        print(
            f"{slug_prefix}: depth={c['depth']} leaf={c['is_leaf']} "
            f"core={c['core_n']} filt={c['filter_n']} active={c['is_active']}"
        )
    else:
        print(f"{slug_prefix}: NOT IN DB")
