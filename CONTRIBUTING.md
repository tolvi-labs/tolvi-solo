# Contributing

Contributions are welcome — bug fixes, new pack templates, installer improvements, and additional vertical packs.

## Getting started

```bash
git clone https://github.com/tolvi-labs/tolvi-solo
cd tolvi-solo
```

No build step. The installer is a single bash script; packs are plain Markdown.

## Adding a pack

A pack lives at `packs/<name>/` and contains:

- `README.md` — what the pack is and when to use each template
- `templates/` — one `.md` file per template type

Use the `engineer` pack as a reference. Templates must use `tolvi-format-v1` frontmatter (see [`packs/engineer/templates/decision.md`](./packs/engineer/templates/decision.md)).

## Testing the installer

```bash
cd /tmp && mkdir test-repo && cd test-repo && git init
bash /path/to/tolvi-solo/install.sh
ls vault/
```

## Brand isolation

This project is published under the **Tolvi Labs** name. Do not reference Torres Atlantic, Covera Plus, Corvin Health, or any other Torres Atlantic product in any contributed file. The `NOTICE` file is the only place those names appear, and it must not be modified.

## License

By contributing you agree your work will be licensed under [Apache 2.0](./LICENSE).
