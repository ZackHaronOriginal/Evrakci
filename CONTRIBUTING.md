# Contributing

Thanks for helping! Chambers, developers and interns are all welcome.

## Before your first pull request: sign the CLA

All contributors must sign the [Contributor License Agreement](CLA.md). When you open your first
pull request, a bot posts a comment explaining how. To sign, reply with:

```
I have read the CLA Document and I hereby sign the CLA
```

You only sign once. You keep the copyright in your work. The CLA lets the maintainer keep the
project sustainable, for example by offering commercial licenses, support and a hosted version,
while the code stays open source under AGPL-3.0.

## Rules

1. **No real documents, ever.** Use synthetic samples only. Pull requests that contain real
   member data will be closed and purged from history.
2. Open an issue before starting a large change.
3. Run `ruff check .` and `pytest` before opening a pull request.
4. UI text and the guide are written in Turkish first. Code and code comments are in English.
5. Before adding a new dependency, check its license against
   [docs/dependency-licenses.md](docs/dependency-licenses.md).

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
evrakci
```
