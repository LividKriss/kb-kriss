# kb-kriss

Kriss's personal knowledge base and the home of his email assistant (Kjell Odne). Private repo.

- **Content:** [`kb/`](kb/index.md) — people, voice, email rules, areas, notes.
- **Conventions:** [`AGENTS.md`](AGENTS.md), on top of livid-kb's AGENTS.md (sibling folder `../livid-kb`).
- **Format:** OKF v0.2 with the extensions in [`schema/`](schema/).

```
python3 tools/validate.py       # format, schema, kb:// links, unique emails, no secrets/phone numbers
python3 tools/build_index.py    # regenerate index.md files
```

Auto-sync: launchd job `no.livid.kb-kriss-autosync`, log `~/Library/Logs/kb-kriss-autosync.log`.
Secrets and raw mail never live here: OAuth client in `~/Library/Application Support/kb-kriss/`, token in the Keychain, cache in `~/Library/Application Support/kb-kriss/cache/`.
