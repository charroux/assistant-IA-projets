# Guide de l'équipe

## Responsabilité

L'équipe reste responsable du travail remis, y compris lorsqu'une IA a proposé ou
modifié un contenu. Toute production générée doit être relue et tout usage de l'IA
doit être déclaré dans `usage_ia.yml`.

## Identifiants

- `BES-xxx` : besoin ;
- `EXG-xxx` : exigence ;
- `RSQ-xxx` : risque ;
- `CRT-xxx` : critère d'acceptation ;
- `CPT-xxx` : composant de conception ;
- `DEC-xxx` : décision ;
- `PRV-xxx` : preuve ;
- `ECR-xxx` : écart ;
- `PROD-xxx` : production documentaire.

## Statuts

```text
brouillon → propose → valide → remplace
```

Seule une personne autorisée peut décider du passage à `valide`. Un écart utilise
`ouvert`, `resolu` ou `accepte`.

## Monday et Git

- Monday : actions, responsables, échéances, comptes rendus et suivi.
- Git : raisonnement, décisions détaillées, conception, preuves et productions.

Une décision importante possède un identifiant Git qui peut être référencé dans
Monday. Ne pas dupliquer une même description longue dans les deux outils.

