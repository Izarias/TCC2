# TCC2 Repository Overview

This repository contains the material used to generate, compile, and analyze the code snippets for the TCC2 experiment.

## Main flow

1. `prompts_tcc2.md` defines the 40 prompt templates used in the experiment.
2. `prompts_manifest.csv` maps each prompt to case, prompt type, prompt language, target language, model, and output filename.
3. `generate_snippets_gpt52.py` and `generate_snippets_claude.py` create the snippet dataset for each model.
4. `snippets_gpt52/` and `snippets_claude/` store the generated snippets that were analyzed.
5. `SnippetsCS/` is the small .NET project used to compile and run Sonar with Roslyn support for the C# snippets.
6. `scripts/aggregate_sonar_issues.py` joins Sonar issues with the manifest and produces analysis-ready output.

## File map

| Path | Purpose | Keep in GitHub? |
| --- | --- | --- |
| `prompts_tcc2.md` | Master prompt matrix for the experiment | Yes |
| `prompts_manifest.csv` | Canonical mapping of all 160 snippet variants | Yes |
| `generate_prompts.py` | Helper to build prompt materials | Yes |
| `generate_snippets_gpt52.py` | Snippet generator for GPT-5.2 | Yes |
| `generate_snippets_claude.py` | Snippet generator for Claude 4 | Yes |
| `snippets_gpt52/` | Generated GPT-5.2 snippets | Yes, if you want the dataset in the repo |
| `snippets_claude/` | Generated Claude snippets | Yes, if you want the dataset in the repo |
| `snippets_manifest_gpt52.csv` | Derived manifest for GPT-5.2 snippets | No, it is generated from `prompts_manifest.csv` |
| `snippets_manifest_claude.csv` | Derived manifest for Claude snippets | No, it is generated from `prompts_manifest.csv` |
| `SnippetsCS/` | C# build/analysis project | Yes |
| `requirements.txt` | Python dependency list | Yes |
| `scripts/aggregate_sonar_issues.py` | Sonar issue aggregation script | Yes |
| `sonar_issues_TestePiloto.json` | Raw Sonar issues export | Optional, but useful for traceability |
| `sonar_issues_aggregated.csv` / `sonar_issues_aggregated.json` | Derived analysis outputs | No, they can be regenerated |

## What was analyzed

The experiment has 40 unique prompts:

- 5 OWASP cases: `A01`, `A04`, `A05`, `A07`, `A10`
- 4 prompt styles: `Z`, `F`, `D`, `A`
- 2 prompt languages: `PT`, `EN`

Each prompt is expanded into 4 snippet variants:

- 2 target languages: `PY`, `CS`
- 2 models: `G5`, `C4`

That produces 160 snippets total.

## Recommended cleanup

Keep the source files, the manifest, the generators, the snippet folders, and the C# project.
Remove generated caches, build outputs, and duplicated derived files before publishing.

The files below are safe to remove because they are reproducible:

- `.scannerwork/`
- `.sonarqube/`
- `SnippetsCS/bin/`
- `SnippetsCS/obj/`
- `__pycache__/`
- `.DS_Store`
- `prompts_PY.md`
- `prompts_CS.md`
- `snippets_manifest_gpt52.csv`
- `snippets_manifest_claude.csv`
- `sonar_issues_aggregated.csv`
- `sonar_issues_aggregated.json`

## Sonar data

`sonar_issues_TestePiloto.json` is the raw response from the SonarQube issues API.
It already contains the issue list plus metadata such as pagination, total count, effort total, and the `components` section.
It does not represent all possible Sonar information; it is the result of one specific API query.
