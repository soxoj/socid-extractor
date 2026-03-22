# Developer documentation

Technical notes for working on **socid_extractor**: how extraction works, where code lives, and how tests and CI are organized.

For installation and CLI usage, see the [root README](../README.md). For the list of supported sites and extraction methods, see [METHODS.md](../METHODS.md). For contributing new methods, see [CONTRIBUTING.md](../CONTRIBUTING.md).

## Contents

| Document | Description |
| -------- | ----------- |
| [architecture.md](architecture.md) | Request flow: `parse`, `mutate_url`, `extract`, schemes, and post-processors. |
| [modules.md](modules.md) | Package layout and responsibility of each module. |
| [testing-and-ci.md](testing-and-ci.md) | End-to-end tests, pytest markers, local commands, GitHub Actions, and `revision.py`. |
