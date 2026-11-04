"""Parse catalog audit JSON."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8-sig")
data = None
for line in text.splitlines():
    if line.strip().startswith("{"):
        data = json.loads(line)
        break
if data is None:
    data = json.loads(text)

cats = data["categories"]
by_id = {c["id"]: c for c in cats}
children: dict[int, list[dict]] = defaultdict(list)
for c in cats:
    if c["parent_id"]:
        children[c["parent_id"]].append(c)

print("=== STATS ===")
print(json.dumps(data["stats"], indent=2))

roots = sorted(children.get(None, []), key=lambda x: (x["sort_order"], x["id"]))
print("\n=== L1 ===")
for r in roots:
    print(f"id={r['id']} slug={r['slug']} name={r['name']} active={r['is_active']}")

# depth per L1 branch
print("\n=== DEPTH BY L1 ===")
for r in roots:
    branch = [c for c in cats if _in_branch(c, r["id"], by_id, children)]
    depths = [c["depth"] for c in branch]
    l2 = len(children[r["id"]])
    print(
        f"{r['slug']}: nodes={len(branch)} L2={l2} max_depth={max(depths)} "
        f"leaves={sum(1 for c in branch if c['is_leaf'])}"
    )


def _in_branch(c, root_id, by_id, children):
    cur = c["id"]
    while cur:
        if cur == root_id:
            return True
        pid = by_id[cur]["parent_id"]
        if pid is None:
            return False
        cur = pid
    return False


def print_tree(node_id, indent=0):
    c = by_id[node_id]
    meta = f"id={c['id']} slug={c['slug']} active={c['is_active']} depth={c['depth']} core={c['core_n']} filt={c['filter_n']}"
    print("  " * indent + f"- {c['name']} ({meta})")
    for ch in sorted(children[node_id], key=lambda x: (x["sort_order"], x["id"])):
        print_tree(ch["id"], indent + 1)


# transport
print("\n=== TRANSPORT TREE ===")
transport = next(c for c in cats if c["slug"] == "transport")
print_tree(transport["id"])

# services
print("\n=== SERVICES TREE ===")
services = next(c for c in cats if c["slug"] == "services")
print_tree(services["id"])

# filter readiness summary
print("\n=== FILTER/FIELD SUMMARY (leaves with counts) ===")
for c in sorted(cats, key=lambda x: (x["depth"], x["slug"])):
    if c["is_leaf"]:
        status = []
        if c["core_n"]:
            status.append(f"core={c['core_n']}")
        if c["opt_n"]:
            status.append(f"opt={c['opt_n']}")
        if c["filter_n"]:
            status.append(f"filters={c['filter_n']}")
        if c["rule_n"]:
            status.append(f"rules={c['rule_n']}")
        print(f"{c['slug']}: {'; '.join(status) if status else 'NO_FIELDS_NO_FILTERS'}")
