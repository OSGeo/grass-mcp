# Contributing

There is more than one way of contributing to grass-mcp.
Here we will focus on contributions centered
around the grass-mcp source code.
You can also report issues, plan new features,
or explore <https://grass.osgeo.org/get-involved/>.

## AI use policy

AI tools are part of modern development workflows and
contributors may use them. However, all contributions must meet
GRASS quality standards regardless of how they were created.

### Guidelines

AI-assisted development is acceptable when used responsibly.
Contributors must:

- **Test all code thoroughly.** Submit only code you have verified works correctly.
- **Understand your contributions.** You need to be able to explain the code changes
  you submit.
- **Write clear, concise PR descriptions** in your own words.
- **Use your own voice** in GitHub issues and PR discussions.
- **Take responsibility** for code quality, correctness, and maintainability.
  Self-review AI-generated code before submitting. Question whether each
  change is justified and remove what is not.

### Disclosure

Disclose AI assistance when substantial algorithms or logic were AI-generated,
or when uncertain about licensing or copyright implications.
Be honest if a reviewer asks about code origins.

### Unacceptable submissions

Pull requests may be closed without review if they contain:

- Untested code
- Verbose AI-generated descriptions
- Evidence the contributor doesn't understand the submission

Using AI to assist learning and development is encouraged.
Using it to bypass understanding or submit work you cannot explain is not.

## Changing code and documentation

To contribute changes to the grass-mcp GitHub repository, use a
"fork and pull request" workflow. The GRASS
[GitHub guide](https://github.com/OSGeo/grass/blob/main/doc/development/github_guide.md)
leads you through a first time setup and shows how to create a pull request.
Replace `grass` with `grass-mcp` in the repository URLs.

To contribute effectively, please familiarize yourself with the GRASS
[Programming Style Guide](https://github.com/OSGeo/grass/blob/main/doc/development/style_guide.md).

If you use an AI assistant or agent, see [`AGENTS.md`](./AGENTS.md) for
project-specific instructions and conventions.

Before creating a PR, please test your changes.
Every change in behavior needs a test.
Once you create a PR, a series of automated checks will run on your pull request.
This is a part of the standard iterative process of integrating
changes into the main code, so if that happens,
just see the error messages, go back to your code and try again.
If you are not sure what to do, let others know in a pull request comment.

In addition to testing, please use [pre-commit](https://pre-commit.com/)
to apply standardized formatting:

```bash
pre-commit install
pre-commit run --all-files
```

## About source code

grass-mcp is written in Python. It runs GRASS tools, so working on it
requires a GRASS installation.
