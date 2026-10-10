# AGENTS.md

Instructions for AI assistants and agents working with code in this
repository. Human contributors should read [CONTRIBUTING.md](CONTRIBUTING.md)
first. Everything there applies here too.

After writing or modifying code, self-review it before presenting it.
Review as a human PR reviewer would: Is the reasoning behind each line
sound? Is this line actually needed? Where did this code come from? Will
this be hard to maintain? What if this will need to be changed later?
Make every line of code, comments, and commit messages clear and
well-reasoned. Evaluate each line. Remove or change any line that
lacks a strong justification. Don't invent justifications.

Do not present code you cannot explain. When generating substantial
algorithms or logic, note this to the human so they can disclose it.

## Checks

```bash
pre-commit run --all-files
```

## Conventions

- Write "GRASS", never "GRASS GIS".
- Data is organized in projects (formerly called locations) and mapsets.
- Follow the GRASS
  [AGENTS.md](https://github.com/OSGeo/grass/blob/main/AGENTS.md) coding
  conventions.
- Acknowledge larger AI use in the commit message or PR description, not as
  a co-author.
- Keep each change to one topic and include its tests.

## Invariants

Rules each change must not break. Each entry is added by the pull request
that introduces the code it protects.
