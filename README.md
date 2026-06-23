# TCC2 Repository Overview

This repository contains the material used to generate, compile, and analyze the code snippets for the TCC2 experiment.

## Main flow

1. `prompts.md`: Defines the 60 prompts used in the experiment.
2. `SnippetsCS/` and `SnippetsPY/`: Store the generated code snippets for C# and Python, respectively.
3. `ResultadosSemgrep/`, `ResultadosSonarPY/` and `ResultadosSonarCS/` Store the analysis results from Semgrep and SonarQube.
4. `data_prep`: Contains the scripts used to clean and process the collected data.
5. `analysis/`: Contains the scripts used to process the data and answer the research questions.
6. `graphs/`: Stores the visual graphs generated from the analysis.

## What was analyzed

The experiment is structured around 60 unique prompt combinations, broken down by the following variables:

- 5 OWASP Categories: `A01`, `A04`, `A05`, `A07`, `A10`
- 4 Prompt Styles: `Z`, `F`, `D`, `A`
- 2 Prompt Languages: `PT`, `EN`

Each of these 60 base prompts was tested across 2 different AI models:

- `G5`
- `C4`

Total Dataset: $60 \text{ prompts} \times 2 \text{ models} = 120 \text{ generated snippets total.}$