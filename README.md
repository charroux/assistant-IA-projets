# Assistant IA aux projets

Outil facultatif de cohérence documentaire pour les Engineering Projects. Il
relie le besoin, le cadrage, les décisions, la conception, les preuves et les
productions sans se substituer au mentor, à l'expert, au déposant ni au jury.

## Deux dépôts distincts

Le dépôt de l'outil et le dépôt étudiant sont séparés :

```text
espace-de-travail/
├── assistant-IA-projets/   outil cloné une fois
│   └── .venv/              environnement Python local, jamais partagé
└── projet-fictif/          dépôt partagé du projet étudiant
```

L'outil s'installe depuis `assistant-IA-projets`. Les commandes `coherence`
s'exécutent ensuite depuis `projet-fictif`, ou avec `--root` suivi de son chemin.

## Ce que font les commandes d'installation

| Commande | Fonction | Appel IA |
| --- | --- | --- |
| `python -m venv .venv` | Crée un Python isolé pour l'outil | Non |
| activation de `.venv` | Fait utiliser ce Python par le terminal courant | Non |
| `python -m pip install .` | Installe la commande `coherence` | Non |
| `coherence init` | Copie le modèle de projet | Non |

Ces commandes doivent être exécutées séparément. L'environnement `.venv` est
jetable, propre à chaque ordinateur et ne doit jamais être ajouté à Git.

## Installation pour un étudiant

Python 3.11 ou plus récent est requis.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install .
```

Si PowerShell interdit l'activation pour la session courante :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Windows — Invite de commandes `cmd.exe`

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install .
```

### Git Bash sous Windows

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install .
```

### Linux ou macOS — Bash/Zsh

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

Sous certaines distributions Linux, le paquet système `python3-venv` doit être
installé. L'activation est facultative : on peut appeler directement
`.venv/bin/coherence` sous Linux ou `.venv\Scripts\coherence.exe` sous Windows.

## Créer un projet étudiant séparé

Depuis le dépôt de l'outil, après installation :

```powershell
coherence init ..\projet-fictif --campus paris --title "Projet fictif"
cd ..\projet-fictif
coherence start
coherence check
```

Sous Linux, remplacer `..\projet-fictif` par `../projet-fictif`.

`coherence start` explique quoi faire ensuite sans appeler d'IA. Le dépôt généré
est autonome sur le plan documentaire : une IA autorisée à le lire peut aussi
utiliser directement `PROMPT_DEMARRAGE.md`.

## Quand une IA est-elle appelée ?

| Commande | Fonction | Appel IA | Écriture |
| --- | --- | --- | --- |
| `coherence start` | Oriente l'étudiant selon la phase | Non | Non |
| `coherence check` | Vérifie la structure et les relations | Non | Non |
| `coherence impact EXG-001` | Explore les références | Non | Non |
| `coherence report` | Produit un rapport déterministe | Non | Oui, rapport local |
| `coherence ask "..."` | Répond à partir du dépôt | Oui | Non |
| `coherence propose "..."` | Prépare un fichier de changements | Oui | Proposition locale seulement |
| `coherence apply fichier.json` | Applique une proposition examinée | Non | Oui, transactionnelle |
| `coherence audit` | Produit un audit documentaire indépendant | Oui | Non, sauf `--save` |

Avant `ask`, `propose` ou `audit` :

1. vérifier les autorisations dans `confidentialite.yml` ;
2. ne conserver que les chemins autorisés ;
3. définir la clé API dans l'environnement, jamais dans Git.

PowerShell :

```powershell
$env:OPENAI_API_KEY = "..."
```

Invite de commandes Windows :

```bat
set OPENAI_API_KEY=...
```

Linux ou macOS :

```bash
export OPENAI_API_KEY="..."
```

Le modèle est configurable par `OPENAI_MODEL`, `--model` ou
`confidentialite.yml`.

## Trois niveaux d'utilisation

### 1. Commencer sans IA

```text
coherence start
coherence check
```

### 2. Poser une question en lecture seule

```text
coherence ask "Je suis un étudiant qui commence. Par où commencer ?"
```

L'IA ne reçoit que les fichiers autorisés, les secrets potentiels bloquent l'envoi
et aucun fichier n'est modifié.

### 3. Proposer puis appliquer une modification

```text
coherence propose "Structure le besoin initial"
coherence apply "ecarts/propositions/proposition-....json"
```

`propose` enregistre une proposition qui doit être lue. `apply` n'appelle pas
l'IA, contrôle les chemins, refuse une promotion automatique vers `valide`,
exécute les vérifications et annule l'opération si elles échouent.

Le commit reste optionnel :

```text
coherence apply "ecarts/propositions/proposition-....json" --commit
```

## Utiliser directement une IA ayant accès au dépôt

La CLI n'est pas obligatoire pour une conversation en lecture seule. Le projet
généré contient `PROMPT_DEMARRAGE.md`, que l'étudiant peut donner à une IA déjà
autorisée à lire son dossier.

Le prompt interne `src/assistant_ia_projets/prompts/assistant.md` n'est pas un
prompt à saisir par l'étudiant. Il encadre `coherence propose` : limites de rôle,
résistance aux instructions présentes dans les documents, interdiction de
valider, de supprimer ou de sortir du projet, et format structuré des changements.

## Partage Git du projet étudiant

### Partageable, sous réserve des autorisations

- `projet.yml` et les guides ;
- cadrage, exigences, risques et critères ;
- décisions et conception ;
- index de preuves expurgé ;
- écarts relus ;
- rapport et soutenance Quarto ;
- `usage_ia.yml`, sans contenu confidentiel ;
- code et démonstrateur lorsque leur partage est autorisé.

### À ne jamais partager par défaut

- `.venv/`, caches et résultats de construction ;
- `.env`, clés API et secrets ;
- données personnelles ou données d'entreprise non autorisées ;
- preuves brutes confidentielles ;
- propositions et rapports IA non relus.

Le modèle génère un `.gitignore` adapté. Il réduit les erreurs courantes mais ne
remplace pas la politique du projet. Monday reste la référence pour les actions,
responsables, échéances, comptes rendus et alertes. Un accès du mentor au dépôt
est un choix institutionnel et ne doit pas servir à mesurer les contributions par
le nombre de commits.

## Principes de responsabilité

- Le cadre documentaire et les contrôles déterministes fonctionnent sans IA.
- Les étudiants vérifient les productions générées et déclarent leurs usages.
- Une IA ne certifie ni vérité métier, ni validité scientifique ou technique.
- Une validation de statut reste humaine.
- L'audit IA est consultatif, indépendant et en lecture seule.

## Développement de l'outil

Cette section concerne les contributeurs de `assistant-IA-projets`, pas les
étudiants qui l'utilisent.

```powershell
python -m pip install -e ".[dev]"
python -m compileall src
pytest
```

Les tests d'intégration OpenAI sont simulés : ils n'envoient aucune donnée et ne
consomment aucun crédit.

Voir [l'architecture](docs/architecture.md) et la
[politique de contribution](CONTRIBUTING.md).
