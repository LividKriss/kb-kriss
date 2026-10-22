#!/usr/bin/env python3
"""Regenerate every index.md under kb/ (OKF v0.2 §8).

Text above `<!-- generated:start -->` in an existing index.md is kept;
everything below it is rewritten. Safe to run any time.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kblib import GEN_MARKER, KB, RESERVED, load_domains, load_types, rel, split_frontmatter  # noqa: E402

ROOT_HEADER = """---
okf_version: "0.2"
---
# Kriss's knowledge base (kb-kriss)

Kriss's personal working knowledge: people and relationships, how he writes, email rules, his areas and notes.
Company knowledge lives in the Livid KB (`kb://livid/`). Conventions: see `AGENTS.md` at the repo root.
Change history: [log.md](log.md).

"""


def describe_dir(relpath: str, domains: dict) -> str:
    if relpath in domains["domains"]:
        return domains["domains"][relpath].get("description", "")
    if relpath in domains["foundations"]:
        return domains["foundations"][relpath].get("description", "")
    return ""


def default_header(d: Path, domains: dict) -> str:
    if d == KB:
        return ROOT_HEADER
    r = rel(d)
    name = d.name.replace("-", " ").capitalize()
    desc = describe_dir(r, domains)
    return f"# {name}\n\n" + (f"{desc}\n\n" if desc else "")


def entry_line(target: Path, d: Path) -> tuple[str, str, str]:
    """Return (group, sort key, bullet) for a doc."""
    fm, _, _ = split_frontmatter(target.read_text(encoding="utf-8"))
    fm = fm or {}
    title = fm.get("title") or target.stem.replace("-", " ").capitalize()
    desc = fm.get("description") or ""
    status = fm.get("status")
    flag = f" *({status})*" if status in ("draft", "deprecated") else ""
    link = target.relative_to(d).as_posix()
    return fm.get("type") or "Other", str(title).lower(), f"- [{title}]({link}){flag}" + (f" — {desc}" if desc else "")


def build(d: Path, domains: dict, type_order: list[str]) -> bool:
    idx = d / "index.md"
    if idx.exists():
        old = idx.read_text(encoding="utf-8")
        header = old.split(GEN_MARKER, 1)[0] if GEN_MARKER in old else default_header(d, domains)
    else:
        old, header = "", default_header(d, domains)

    lines = []
    subdirs = sorted(p for p in d.iterdir() if p.is_dir() and not p.name.startswith("."))
    if subdirs:
        lines += ["## Sections", ""]
        for s in subdirs:
            desc = describe_dir(rel(s), domains)
            lines.append(f"- [{s.name}]({s.name}/)" + (f" — {desc}" if desc else ""))
        lines.append("")

    groups = defaultdict(list)
    for f in sorted(d.glob("*.md")):
        if f.name in RESERVED:
            continue
        g, key, bullet = entry_line(f, d)
        groups[g].append((key, bullet))
    for g in sorted(groups, key=lambda x: (type_order.index(x) if x in type_order else 99, x)):
        lines += [f"## {g}", ""] + [b for _, b in sorted(groups[g])] + [""]
    if not subdirs and not groups:
        lines += ["_Nothing here yet._", ""]

    new = header.rstrip() + "\n\n" + GEN_MARKER + "\n\n" + "\n".join(lines).rstrip() + "\n"
    if new != old:
        idx.write_text(new, encoding="utf-8")
        return True
    return False


def main():
    domains = load_domains()
    type_order = list(load_types()["types"])
    changed = 0
    dirs = [KB] + sorted(p for p in KB.rglob("*") if p.is_dir() and not any(x.startswith(".") for x in p.relative_to(KB).parts))
    for d in dirs:
        changed += build(d, domains, type_order)
    print(f"{changed} index.md file(s) updated, {len(dirs)} directories scanned")


if __name__ == "__main__":
    main()
