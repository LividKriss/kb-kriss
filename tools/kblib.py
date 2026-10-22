"""Shared helpers for the kb-kriss tools (copied from livid-kb/tools, extended for
owners, categories and kb:// cross-repo links). Reads all config from schema/."""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "kb"
SCHEMA = ROOT / "schema"
RESERVED = {"index.md", "log.md"}
GEN_MARKER = "<!-- generated:start -->"
TZ = dt.timezone(dt.timedelta(hours=0))


def load_types() -> dict:
    return yaml.safe_load((SCHEMA / "types.yaml").read_text(encoding="utf-8"))


def resolve_kb_url(url: str, types_cfg: dict):
    """Resolve kb://<name>/<path> to a Path. Returns (path | None, status) where status is
    'ok' | 'not-kb' | 'unknown-kb' | 'root-missing'."""
    m = re.match(r"^kb://([a-z0-9-]+)/(.*)$", str(url).strip())
    if not m:
        return None, "not-kb"
    roots = types_cfg.get("kb_roots") or {}
    if m.group(1) not in roots:
        return None, "unknown-kb"
    root = (ROOT / roots[m.group(1)]).resolve()
    if not root.is_dir():
        return None, "root-missing"
    return root / m.group(2).split("#", 1)[0], "ok"


def load_domains() -> dict:
    data = yaml.safe_load((SCHEMA / "domains.yaml").read_text(encoding="utf-8")) or {}
    data.setdefault("foundations", {})
    data["domains"] = data.get("domains") or {}
    return data


DOMAINS_HEADER = (
    "# Generated and edited by tools/new_domain.py — do not hand-edit domains.\n"
    "# foundations: shared top-level folders every domain refers to.\n"
    "# domains: business areas (max depth: domain/sub-domain).\n"
)


def save_domains(data: dict) -> None:
    body = yaml.safe_dump(
        {"foundations": data["foundations"], "domains": data["domains"] or {}},
        sort_keys=False, allow_unicode=True, width=100,
    )
    (SCHEMA / "domains.yaml").write_text(DOMAINS_HEADER + body, encoding="utf-8")


FM_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)


def split_frontmatter(text: str):
    """Return (frontmatter dict | None, body, error | None)."""
    m = FM_RE.match(text)
    if not m:
        return None, text, None
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        return None, text[m.end():], f"unparseable YAML frontmatter: {e}"
    if not isinstance(fm, dict):
        return None, text[m.end():], "frontmatter is not a mapping"
    return fm, text[m.end():], None


def rel(path: Path) -> str:
    return path.relative_to(KB).as_posix()


def area_of(relpath: str, domains: dict):
    """Classify a kb-relative path. Returns (kind, name) where kind is
    'domain' | 'foundation' | 'root' | None."""
    parts = relpath.split("/")
    if len(parts) == 1:
        return "root", ""
    dirpath = "/".join(parts[:-1])
    best = None
    for d in domains["domains"]:
        if dirpath == d or dirpath.startswith(d + "/"):
            if best is None or len(d) > len(best):
                best = d
    if best:
        return "domain", best
    if parts[0] in domains["foundations"]:
        return "foundation", parts[0]
    return None, parts[0]


def default_tier(kind: str, name: str, domains: dict):
    if kind == "domain":
        return domains["domains"][name].get("tier")
    if kind == "foundation":
        return domains["foundations"][name].get("tier")
    return None


def parse_when(value):
    """Parse a YAML date/datetime/string into an aware datetime (UTC if no offset)."""
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        return value if value.tzinfo else value.replace(tzinfo=TZ)
    if isinstance(value, dt.date):
        return dt.datetime(value.year, value.month, value.day, tzinfo=TZ)
    try:
        v = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return v if v.tzinfo else v.replace(tzinfo=TZ)
    except ValueError:
        return None


def parse_duration(s: str) -> dt.timedelta:
    m = re.fullmatch(r"(\d+)([dwmy])", str(s).strip())
    if not m:
        raise ValueError(f"bad duration {s!r} (use e.g. 90d, 12w, 6m, 1y)")
    n, u = int(m.group(1)), m.group(2)
    return dt.timedelta(days=n * {"d": 1, "w": 7, "m": 30, "y": 365}[u])


def iter_docs():
    for p in sorted(KB.rglob("*.md")):
        if any(part.startswith(".") for part in p.relative_to(KB).parts):
            continue
        yield p


def add_log_entry(text: str, kind: str = "Update", log_path: Path | None = None) -> None:
    """Insert a bullet under today's date heading in kb/log.md (newest first)."""
    log_path = log_path or KB / "log.md"
    today = dt.date.today().isoformat()
    entry = f"- **{kind}** {text}"
    if not log_path.exists():
        log_path.write_text(f"# Change log\n\n## {today}\n\n{entry}\n", encoding="utf-8")
        return
    lines = log_path.read_text(encoding="utf-8").splitlines()
    heading = f"## {today}"
    if heading in lines:
        i = lines.index(heading) + 1
        while i < len(lines) and lines[i].strip() == "":
            i += 1
        lines.insert(i, entry)
    else:
        i = next((n for n, l in enumerate(lines) if l.startswith("## ")), len(lines))
        lines[i:i] = [heading, "", entry, ""]
    log_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
