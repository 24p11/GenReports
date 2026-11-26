# GenReports

Application de génération de comptes rendus d'hospitalisation synthétiques à partir de scénarios produits par [GenPatientProfile](https://github.com/24p11/GenPatientProfile) et de modèles de langage.

![Python](https://img.shields.io/badge/python-3.13+-blue)
[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-green.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

## Rôle du projet

La chaîne est répartie entre deux projets :

```text
GenPatientProfile                         GenReports
données + référentiels                    clients LLM
        ↓                                      ↓
profils → scénarios → prompts  ───────→  comptes rendus → Parquet
```

GenReports :

- appelle GenPatientProfile pour construire les scénarios et les prompts ;
- exécute les générations avec Ollama, Claude ou Mistral ;
- prend en charge le mode direct et le mode batch Mistral ;
- prend en charge la génération `profile_generation` en une ou deux étapes ;
- rassemble les résultats dans des fichiers Parquet.

GenReports n'est pas publié sur PyPI. Il s'utilise depuis ce dépôt.

## Installation

```bash
git clone https://github.com/24p11/GenReports.git
cd GenReports
uv sync
```

La dépendance `GenPatientProfile` est installée depuis PyPI selon la version verrouillée dans `uv.lock`.

## Configuration

Copier le fichier d'exemple :

```bash
cp config/servers.example.yaml config/servers.yaml
```

Le fichier `config/servers.yaml` contient les chemins locaux, les paramètres de génération et les accès aux modèles. Il est ignoré par Git.

Exemple pour `profile_generation` :

```yaml
pipelines:
  profile_generation:
    data:
      input: "data/profile_generation"
      referentials: "data/profile_generation/referentials"
      output: "reports/profile_generation"

    generation:
      mode: "mistral_batch"
      workflow: "two_stage"
      prompt_set: "old"
      poll_interval_seconds: 1
      mistral_batch_size: 1000

      one_stage:
        model: "mistral-large-latest"
        max_tokens: 128000

      two_stage:
        summary:
          model: "mistral-large-latest"
          max_tokens: 8000
        report:
          model: "mistral-large-latest"
          max_tokens: 128000

servers:
  ollama:
    host: "http://localhost:11434"
    model: "mistral"

  claude:
    api_key: ""
    model: "claude-sonnet-4-6"
    verify: true

  mistral:
    api_key: ""
    model: "mistral-large-latest"
    verify: true
```

Un jeu de prompts externe peut être sélectionné avec `generation.prompt_dir`. Dans ce cas, ne pas définir simultanément un autre `prompt_set` que sa valeur par défaut.

## Utilisation

Afficher l'aide :

```bash
uv run genreports --help
```

Générer avec Ollama :

```bash
uv run genreports profile_generation --client ollama --n-sejours 20
```

Générer avec Claude :

```bash
uv run genreports profile_generation --client claude --n-sejours 20
```

Générer avec Mistral :

```bash
uv run genreports profile_generation --client mistral --n-sejours 20
```

Pour `pmsi_sampling` :

```bash
uv run genreports pmsi_sampling --client mistral --n-sejours 500 \
  --n-ccam 3 --n-das 4
```

La commande accepte également `--ghm5` pour filtrer les GHM et `--batch-size` pour régler la taille des écritures intermédiaires en mode direct.

## Modes de génération

| Mode | Workflow | Client | Jeux de prompts compatibles |
|---|---|---|---|
| `direct` | `one_stage` | Ollama, Claude ou Mistral | `default`, `old` ou externe |
| `mistral_batch` | `one_stage` | Mistral | `default`, `old` ou externe |
| `mistral_batch` | `two_stage` | Mistral | `old` ou externe compatible |

Le jeu `default` prend uniquement en charge `one_stage`. Le jeu `old` prend en charge les deux workflows.

### Mode direct

Chaque scénario est envoyé au client sélectionné. Les résultats sont écrits progressivement selon `--batch-size`.

### Batch Mistral en une étape

Les requêtes sont réparties en jobs de `generation.mistral_batch_size` requêtes, avec une valeur par défaut de 1000. Les réponses sont rassemblées dans un seul fichier Parquet.

### Batch Mistral en deux étapes

Tous les résumés sont générés en premier. Les comptes rendus sont ensuite générés à partir des résumés réussis. Une ligne dont le résumé échoue est conservée avec l'erreur correspondante et n'est pas envoyée à la seconde étape.

Les transferts de fichiers et le suivi des jobs sont retentés en cas d'erreur réseau. La création d'un job n'est pas répétée automatiquement afin d'éviter les doublons.

## Données et référentiels

Les données PMSI et les référentiels CIM-10/CCAM/GHM ne sont pas versionnés dans ce dépôt. Ils doivent être placés dans les chemins indiqués par `data.input` et `data.referentials`.

Les fichiers et colonnes attendus sont définis dans le [contrat de données de GenPatientProfile](https://github.com/24p11/GenPatientProfile/blob/main/docs/input-data-contract.md).

Sont également exclus de Git :

- `data/` ;
- `reports/` ;
- `config/servers.yaml` ;
- les environnements virtuels et fichiers temporaires.

Le dépôt contient seulement le code, les tests, les fichiers de configuration sans secret et les prompts génériques propres à GenReports.

## Sorties

Les scénarios préparés par GenPatientProfile sont sauvegardés avant l'appel au modèle. GenReports écrit ensuite les comptes rendus dans le répertoire `data.output` configuré.

Exemples :

```text
reports/profile_generation/profile_generation_scenarios_<nombre>_<horodatage>.parquet
reports/profile_generation/medical_reports_<lot>_<horodatage>.parquet
reports/profile_generation/profile_generation_mistral_batch_reports_<nombre>_<horodatage>.parquet
reports/profile_generation/profile_generation_mistral_batch_two_stage_reports_<nombre>_<horodatage>.parquet
```

Les sorties contiennent notamment l'identifiant de génération, le scénario, le compte rendu, le modèle, les compteurs de tokens et les erreurs éventuelles. Le workflow en deux étapes ajoute le résumé intermédiaire et ses métadonnées.

## Architecture

```text
GenReports/
├── cli.py                         # commande genreports
├── runner.py                      # orchestration GenPatientProfile + LLM
├── core/
│   ├── clients.py                 # Ollama, Claude, Mistral et batch Mistral
│   ├── config.py                  # lecture YAML
│   └── logger.py
├── pipelines/
│   ├── pipeline.py                # interface commune
│   ├── report.py                  # génération directe et persistance
│   ├── pmsi_sampling/
│   │   └── report.py              # formulation PMSI sampling
│   └── profile_generation/
│       ├── pipeline.py            # sélection direct/batch et one/two stage
│       └── report.py              # construction et assemblage des batchs
└── config/
    ├── prompts.yaml
    └── servers.example.yaml
```

## Tests et intégration continue

```bash
uv run pytest
```

La CI GitHub exécute automatiquement les tests à chaque push sur `main` et pour chaque pull request. Elle ne publie aucun paquet sur PyPI.

## Licence

Ce projet est distribué sous la licence [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](LICENCE.md).
