# AGENTS.md

Instructions for AI assistants and agents working with code in this
repository. Human contributors should read [CONTRIBUTING.md](CONTRIBUTING.md)
first. Everything there applies here too.

After writing or modifying code, self-review it as a human pull request
reviewer would. Is each line needed? Is the reasoning behind it sound? Will
it be hard to maintain? Remove or change any line that lacks a strong
justification. Do not present code you cannot explain. When generating
substantial algorithms or logic, tell the human so they can disclose it.

## Checks

```bash
pre-commit run --all-files
```

## Conventions

- Write "GRASS", never "GRASS GIS".
- Data is organized in projects (formerly called locations) and mapsets.
- Follow the GRASS
  [AGENTS.md](https://github.com/OSGeo/grass/blob/main/AGENTS.md) for GRASS
  Python and comment conventions.
- Keep each change to one topic and include its tests.

## Invariants

Rules each change must not break. Each entry is added by the pull request
that introduces the code it protects.
