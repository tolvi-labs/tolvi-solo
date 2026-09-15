#!/usr/bin/env python3
"""Validate a .vault-meta.json against the published tolvi-format-v2 shape.

Mirrors spec/schemas/vault-meta.json from the tolvi repo: additionalProperties
is false, and only the ^x- namespace is open. The duplication is deliberate,
since a standalone clone cannot read the sibling repo's schema. Prints one line
per problem and exits non-zero when it finds any.
"""
import json
import sys

REQUIRED = {"workspace", "embedding_model", "schema_version"}
ALLOWED = REQUIRED | {"repo", "product"}


def problems(path):
    try:
        meta = json.load(open(path))
    except Exception as exc:  # unreadable or malformed
        return [f"unparseable: {exc}"]

    found = []
    for field in sorted(REQUIRED - set(meta)):
        found.append(f"missing required field: {field}")
    for key in sorted(set(meta) - ALLOWED):
        if not key.startswith("x-"):
            found.append(f"field {key!r} is neither a spec field nor an x- extension")
    if meta.get("schema_version") != 2:
        found.append(f"schema_version is {meta.get('schema_version')!r}, want 2")
    return found


if __name__ == "__main__":
    found = problems(sys.argv[1])
    for line in found:
        print(line)
    sys.exit(1 if found else 0)
