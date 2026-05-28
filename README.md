# TCC2 Repository Overview

This repository contains the material used to generate, compile, and analyze the code snippets for the TCC2 experiment.

## Main flow

1. `prompts_tcc2.md` defines the 40 prompt templates used in the experiment.
2. `prompts_manifest.csv` maps each prompt to case, prompt type, prompt language, target language, model, and output filename.
3. `generate_snippets_gpt52.py` and `generate_snippets_claude.py` create the snippet dataset for each model.
4. `snippets_gpt52/` and `snippets_claude/` store the generated snippets that were analyzed.
5. `SnippetsCS/` is the small .NET project used to compile and run Sonar with Roslyn support for the C# snippets.
6. `scripts/aggregate_sonar_issues.py` joins Sonar issues with the manifest and produces analysis-ready output.


## What was analyzed

The experiment has 40 unique prompts:

- 5 OWASP cases: `A01`, `A04`, `A05`, `A07`, `A10`
- 4 prompt styles: `Z`, `F`, `D`, `A`
- 2 prompt languages: `PT`, `EN`

Each prompt is expanded into 4 snippet variants:

- 2 target languages: `PY`, `CS`
- 2 models: `G5`, `C4`

That produces 160 snippets total.

