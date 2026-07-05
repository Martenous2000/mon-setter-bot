# PROMPT 4 — Relances automatiques LinkedIn (post-installation)
# (documentation du workflow n8n "LinkedIn - Relances automatiques", ajouté après le PROMPT 3)

Ce workflow relance automatiquement les prospects qui ont **vu** un message de Jean-Pierre sans y
répondre. Il tourne à côté du `LinkedIn DM Setter [Template]` (PROMPT 3) mais est totalement indépendant :
il ne modifie rien à la conversation en cours, il se contente d'envoyer un message de relance quand les
conditions sont réunies.

## Règles exactes

1. **Déclenchement** : toutes les heures (Schedule Trigger), le workflow scanne les conversations LinkedIn
   de Jean-Pierre dont la dernière activité date d'entre 24h et 30 jours.
2. **Condition stricte de relance 1** : le **dernier message de la conversation doit avoir été envoyé par
   nous**, ET LinkedIn doit indiquer qu'il a été **vu (`seen: 1` + `seen_by` avec un horodatage)**, ET ça
   fait **plus de 24h** que ce message a été vu. Si le prospect n'a pas encore ouvert le message, ou s'il a
   déjà répondu, aucune relance n'est envoyée.
   - Message envoyé : `"{Prénom} ?"` (ex : `"Jean ?"`)
3. **Relance 2** : si la relance 1 est restée sans réponse pendant **3 jours**, un second message est
   envoyé : `"J'espère que tu n'es pas trop sous l'eau 🙏"`.
4. **Pas de 3e relance.** Après la relance 2 sans réponse, le workflow arrête définitivement de relancer
   cette conversation (philosophie "less is more" du persona).
5. **Remise à zéro automatique** : dès que le prospect répond (même après une relance), le compteur de
   relance de cette conversation est réinitialisé — s'il redevient silencieux plus tard, le cycle
   recommence à zéro.
6. **Espacement des envois** : si plusieurs relances sont dues au même passage (ex : 25 conversations),
   elles ne partent JAMAIS toutes en même temps — chaque envoi est espacé aléatoirement de **30 à 60
   secondes** du précédent, pour rester crédible aux yeux de LinkedIn.

## Sécurité : mode `dry_run`

Le nœud **Config** contient un champ booléen `dry_run` :
- `dry_run = true` (valeur par défaut à l'installation) : le workflow simule tout le raisonnement
  (candidats trouvés, message qui aurait été envoyé) mais **n'envoie rien de réel**. Le résultat est stocké
  dans les données statiques du workflow (`dryRunPreview`, visible dans les logs d'exécution n8n) et un
  résumé est envoyé sur Telegram après chaque passage.
- `dry_run = false` : les relances sont réellement envoyées via l'API Unipile.

**Ne jamais activer `dry_run = false` sans avoir d'abord vérifié plusieurs passages en `dry_run = true`.**

## Où sont stockées les données de suivi

Le workflow utilise les **static data** internes de n8n (`$getWorkflowStaticData('global')`), pas de
Google Sheet ni de base externe. Pour chaque `chatId` en cours de relance, on stocke :
`{ stage: 0|1|2, relance1SentAt, relance2SentAt }`. Cet état vit uniquement dans ce workflow n8n — si le
workflow est supprimé, l'historique des relances déjà envoyées est perdu (mais ça n'a pas d'impact sur les
conversations LinkedIn elles-mêmes).

## Alerte en cas d'erreur

Comme les autres workflows du projet, celui-ci est branché sur le workflow d'erreur commun
(`LinkedIn DM Setter - Alerte erreur`, Telegram) : toute erreur technique déclenche une notification
immédiate.

## Fichier workflow

Le JSON exporté du workflow est dans `n8n/linkedin-relances.workflow.json`. Pour le réimporter dans un
nouvel environnement n8n : Workflows → Import from File, puis remplir les clés Unipile dans le nœud
**Config** (même logique que le nœud **Set Keys** du DM Setter, PROMPT 3).

## Limite connue

Le statut "vu" (`seen`) dépend de ce que LinkedIn expose à Unipile — si le prospect a désactivé les accusés
de lecture ou si LinkedIn ne remonte pas l'info pour un profil donné, la relance 1 ne se déclenchera jamais
pour cette conversation (ce n'est pas un bug, c'est une limite de la donnée source).
