# job-scraper-opportunities — README

Workflow n8n qui détecte des offres d'emploi commerciales sur LinkedIn (via Unipile),
les qualifie, identifie le décideur pertinent, génère un brouillon de premier message,
et notifie sur Telegram pour validation humaine avant tout envoi.

## Import

1. Importer `job-scraper-opportunities.workflow.json` dans n8n (Workflows > Import from File).
2. Créer les deux Data Tables natives n8n référencées par le workflow (voir schémas ci-dessous). Ce sont des Data Tables n8n, pas une base externe.
3. Configurer les credentials : `Unipile API Key (X-API-KEY)` (header auth), `Anthropic API Key`, `Telegram Alert Bot`.
4. Renseigner les variables d'environnement n8n : `UNIPILE_DSN`, `CLAUDE_MODEL`, `TELEGRAM_ALERT_CHAT_ID` (8723535937 côté Martin), `QUALIFICATION_PROMPT`, `MESSAGE_GENERATION_PROMPT`, `PRINCIPES_SETTING`, et une variable `PERSONA_<persona_key>` par compte actif (contenu du fichier `prompts/personas/<persona_key>.md` correspondant).
5. Remplir manuellement la Data Table `job_scraper_config` avec au moins une ligne (recommandé : Enzo en premier, car son persona qualifie déjà explicitement le signal "offre d'emploi active" comme le plus fort).
6. Laisser le workflow **inactif** (`"active": false` dans le JSON) le temps de valider un premier cycle manuel avant d'activer le Schedule Trigger.

> Pourquoi des variables d'environnement pour charger les prompts plutôt qu'un appel HTTP vers GitHub à chaque run : évite une dépendance réseau supplémentaire et une latence par exécution. À l'inverse d'un appel GitHub raw, il faut penser à mettre à jour la variable n8n après toute modification des fichiers `prompts/job-scraper/*.md` ou `prompts/personas/*.md` dans le repo — c'est un compromis, pas une contrainte technique : si l'utilisateur préfère la fraîcheur automatique au prix d'un appel HTTP de plus par run, remplacer les nodes LLM par un appel préalable `HTTP Request` vers `raw.githubusercontent.com/Martenous2000/mon-setter-bot/main/prompts/...`.

## Schéma `job_scraper_config` (Data Table)

| Colonne | Type | Description |
|---|---|---|
| `account_label` | string | Identifiant lisible du compte (ex. `enzo`) |
| `unipile_account_id` | string | ID du compte LinkedIn côté Unipile (`GET /api/v1/accounts`) |
| `persona_key` | string | Doit correspondre à un fichier `prompts/personas/<persona_key>.md` existant |
| `target_geographies` | json array | Ex. `["US","CA"]`, passé tel quel au filtre `location` d'Unipile jobs |
| `target_languages` | json array | Informatif pour le prompt de génération de message |
| `keywords_rotation` | json array | Rotation de requêtes jobs (BDR, SDR, Head of Sales, etc.) |
| `decision_maker_roles` | json array | IDs/rôles LinkedIn ciblés pour `category=people` (Founder, CEO, Head of Sales...), alignés sur l'ICP du persona |
| `active` | bool | Le compte est inclus dans les runs tant que `true` |

## Schéma `job_opportunities` (Data Table)

`unipile_job_id` + `account_label` = clé de dédoublonnage (upsert). Colonnes : `unipile_job_id`,
`account_label`, `company_name`, `company_unipile_id`, `job_title`, `job_url`, `job_posted_at`,
`location`, `job_description_excerpt`, `relevance_reasons`, `score`, `commercial_angle`,
`decision_maker_name`, `decision_maker_profile_url`, `decision_maker_role`,
`decision_maker_source` (`people` | `hiring_team_fallback` | `none`), `draft_message`,
`status` (`détecté` → `qualifié` → `décideur identifié` → `message généré` → `en attente de
validation` → `envoyé` → `répondu` → `perdu`), `created_at`, `updated_at`.

## Pourquoi `category=people` avant `hiring_team` pour le décideur

Décision explicite de l'utilisateur : `hiring_team` (issu du détail de l'offre) pointe
souvent vers un recruteur ou un membre RH ayant publié l'annonce, rarement le décideur
budgétaire réel pour une prestation externalisée. La recherche `category=people` filtrée
sur les rôles de direction (`decision_maker_roles` de la config du compte) est donc
toujours tentée en premier ; `hiring_team` sert uniquement de filet de sécurité si aucun
décideur business n'apparaît dans les résultats `people`, pour ne pas perdre l'opportunité
totalement. Dans ce cas, `decision_maker_source: "hiring_team_fallback"` change aussi
l'angle du message généré (voir `prompts/job-scraper/message-generation.md`).

## Quand et pourquoi activer le fallback Apify

Le node `[FALLBACK DÉSACTIVÉ] Apify: scraping offres` est présent dans le workflow mais
`disabled: true` par défaut, et n'est câblé vers aucune suite. Il ne doit être activé (retirer
`disabled`, brancher sa sortie vers le node de dédoublonnage, ajouter `APIFY_API_TOKEN` et
`APIFY_ACTOR_RUN_URL`, choisir un acteur Apify de scraping LinkedIn Jobs ou jobboard sur le
marketplace) que si l'un de ces cas est constaté en usage réel, pas de façon préventive :

1. **Résultats Unipile jobs anormalement pauvres** : le node `Unipile: recherche offres (jobs)` renvoie 0 ou très peu d'items sur plusieurs runs consécutifs pour un compte donné, alors que les mots-clés de rotation sont larges et le compte actif.
2. **Erreur 403** `subscription_required` ou `feature_not_subscribed` : la fonctionnalité de recherche jobs n'est pas disponible pour ce compte Unipile/LinkedIn (ex. restriction du plan LinkedIn du compte).
3. **Erreur 401** `disconnected_account` ou `expired_credentials` : le compte Unipile est déconnecté et la recherche échoue systématiquement, le temps de reconnecter le compte.
4. **Besoin de couvrir des sources hors LinkedIn** : si l'utilisateur souhaite élargir à d'autres jobboards non couverts par Unipile.

Ce n'est jamais un remplacement par défaut d'Unipile : Unipile reste la source principale
pour tous les comptes tant qu'aucun de ces cas n'est constaté, pour rester cohérent avec le
reste du système de prospection déjà bâti sur Unipile.

## Limites connues de l'API Unipile utilisées ici

- `category=jobs` (Classic) : 50 résultats par page maximum, pagination par `cursor`.
- La réponse de **recherche** liste (`POST /linkedin/search`, `category=jobs`) ne contient
  **pas** le texte complet de l'offre (`description`). Il faut l'appel complémentaire
  `GET /linkedin/jobs/{job_id}?service=CLASSIC&account_id=...` (node "Unipile: détail offre"),
  qui renvoie `description`, `hiring_team`, `seniority`, `skills`, `salary`, `workplace`.
- `category=companies` avec les filtres avancés (`recent_activities`, `technologies`,
  `headcount_growth`) nécessite `api: "sales_navigator"`, donc un abonnement Sales Navigator
  actif sur le compte Unipile utilisé. Sans cet abonnement, ces champs sont simplement absents
  de l'enrichissement (dégradation silencieuse, pas d'échec du run) — voir node "Unipile:
  enrichissement entreprise".
- Aucun rate limit (429) documenté sur cet endpoint ; les erreurs à surveiller sont 400
  (paramètres invalides), 401 (compte déconnecté/credentials expirés) et 403 (permissions/
  abonnement insuffisant).

## Ce qui reste volontairement hors de ce workflow

- Aucun envoi LinkedIn automatique. Le pipeline s'arrête à la notification Telegram et à
  l'écriture en statut `en attente de validation`. L'envoi effectif (changement de statut
  vers `envoyé`) reste une action humaine, réalisée en dehors de ce workflow.
- Pas de rotation d'index persistée en Data Table pour `keywords_rotation` en V1 (le node
  "Choisir mot-clé de rotation" utilise un index dérivé du timestamp du run, suffisant pour
  répartir les mots-clés dans le temps sans état supplémentaire à maintenir). À améliorer si
  une répartition plus stricte est nécessaire.
