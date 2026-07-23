# Règles strictes — Icebreakers (2 types uniquement, jamais un troisième format)

Document de garde-fou. À consulter obligatoirement avant d'écrire ou d'envoyer un icebreaker, quel que soit le contexte (compte, urgence, absence de données complètes). Il n'existe QUE ces deux formats — aucun hybride, aucune improvisation.

## Règle 0 — un icebreaker est réservé au tout premier message, jamais si une conversation existe déjà

Avant même de choisir entre Type 1 et Type 2, vérifier qu'AUCUNE conversation n'existe déjà avec ce prospect sur le compte LinkedIn concerné. Un icebreaker (Type 1 ou Type 2) ne s'envoie que si c'est le tout premier message échangé avec cette personne. Dès qu'un message — peu importe lequel, peu importe qui l'a envoyé — existe déjà dans l'historique, ce n'est plus un icebreaker : passer en mode reprise/relance de conversation, jamais renvoyer un Type 1 ou Type 2.

Méthode de vérification fiable (obligatoire) : paginer intégralement `/chats?account_id=X&limit=100` en suivant le `cursor` jusqu'à `null`, puis matcher sur le champ `attendee_provider_id` des résultats retournés. Les filtres query params `attendee_id`/`attendee_provider_id` passés directement à `/chats` sont PEU FIABLES et silencieusement ignorés par l'API (retournent toujours le même lot des ~100 chats les plus récents, indépendamment du filtre) — ne jamais s'y fier seul, toujours repasser par la pagination complète + matching local.

## Type 1 — un post récent pertinent existe

Fichier source : `evo_system_type1_post_pertinent.txt`

Condition d'usage : le prospect a un post récent (moins de 2 mois) qui correspond à un des types prioritaires (événement, plainte/coup de gueule justifié, réaction/opinion tranchée). Jamais un post "de valeur" pur (conseil, framework) — ce type de post est à éviter en priorité.

Format obligatoire (Variante 2, comportement par défaut) :
- "Helllo [prénom]"
- Courte phrase d'ouverture qui annonce la réaction au post (reformulée à chaque fois)
- Réaction/observation courte alignée sur le type de post (accord sincère si plainte/réaction — ne JAMAIS contredire — intérêt si événement)
- Question courte et spécifique qui rebondit sur le post, obligatoire en fin de message
- 2-3 lignes maximum, jamais de PS, jamais de signature

## Type 2 — aucun post récent pertinent

Fichiers source : `evo_system_type2_pas_de_post_pertinent.txt` / `type2_system_final.txt`

Condition d'usage : pas de post récent exploitable, ou seulement des posts anciens (plus de 2 mois) ou uniquement des posts "de valeur"/promotionnels.

Format obligatoire, exactement 4 blocs séparés par une ligne vide :
1. "Helllo [prénom]"
2. Durée EXACTE + nom d'entreprise EXACT tirés du profil réel — jamais approximés, jamais inventés (ex: "depuis 2006", pas "bientôt 20 ans"). Cas particulier indépendant/salarié non-fondateur : reformuler autour du métier, jamais "tu as lancé [Self-employed]".
3. Question sur le ciblage/l'audience du prospect selon son profil.
4. PS obligatoire, dans cet ordre de priorité strict :
   - (a) Bannière disponible → détail visuel RÉEL et précis observé dans l'image
   - (b) Pas de bannière mais photo de profil disponible → détail visuel réel de la photo
   - (c) Ni l'un ni l'autre → fallback "PS je me permets de te tutoyer ahah :)"

## Règles communes aux deux types

- 1 seul emoji maximum, jamais l'emoji 😄 (banni sous aucun prétexte), préférer 😉 si besoin, dans le doute mieux vaut n'en mettre aucun
- Jamais de symboles type "+", "&", "/", "->", "=" dans le corps du message
- Tous les accents français corrects, vérifiés mot par mot
- Jamais de tiret cadratin/demi-cadratin
- Jamais de guillemets autour du message final complet
- Jamais de formule de politesse générique ("merci pour la connexion", "j'espère que tu vas bien")
- Tutoiement tout du long

## Erreur constatée à ne plus jamais reproduire (2026-07-23)

Sur un lot de 15 icebreakers, 7 ont été écrits directement "à la main" dans la conversation, sans repasser par les fichiers de règles ci-dessus, produisant un troisième format hybride non documenté : une seule ligne continue au lieu des 4 blocs du Type 2, sans PS, avec une durée approximée au lieu de la durée exacte du profil ("bientôt 20 ans" au lieu de "depuis 2006").

Cause racine : générer un icebreaker de mémoire au lieu de vérifier explicitement, pour CHAQUE prospect et AVANT d'écrire quoi que ce soit :
1. Existe-t-il un post récent (moins de 2 mois) qui correspond à un type prioritaire (événement/plainte/réaction) ? → si oui, Type 1, structure Variante 2.
2. Si non → Type 2, les 4 blocs, avec la durée et le nom d'entreprise EXACTS relevés sur le profil, jamais estimés.

Correctif permanent : avant tout envoi d'icebreaker, vérifier explicitement laquelle des deux conditions s'applique et respecter le format correspondant à la lettre — ne jamais produire un troisième format, même sous contrainte de temps ou de volume (ex: rounds d'envoi échelonnés, lots de 10+, urgence perçue).

## 2e occurrence de l'erreur et cause racine technique (2026-07-23, plus tard le même jour)

Récidive sur 5 icebreakers pour les 2 en Type 2 (aucun post pertinent) : le bloc 2 obligatoire (durée EXACTE + nom d'entreprise EXACT) a été purement et simplement OMIS — le message passait directement de "Helllo [prénom]" au bloc 3 (question de ciblage), sautant le bloc central.

Cause racine technique identifiée, différente de la 1ère occurrence : l'endpoint Unipile `GET /api/v1/users/{public_id}?account_id=...` **ne renvoie PAS** le champ `work_experience` par défaut — seulement headline, follower_count, location, bannière/photo, etc. La durée exacte et le nom d'entreprise réels sont donc invisibles avec cet appel basique. Au lieu de le signaler ou de chercher la donnée ailleurs, le bloc 2 a été silencieusement sauté.

**Fix technique permanent** : pour tout lookup individuel Unipile en vue d'un icebreaker Type 2, TOUJOURS ajouter le paramètre `linkedin_sections=experience` à l'URL :
`GET /api/v1/users/{public_id}?account_id=...&linkedin_sections=experience`
Cela débloque le champ `work_experience` (tableau avec `company`, `position`, `start`, `end` au format `M/D/YYYY`) — c'est la seule source fiable de la durée exacte et du nom d'entreprise pour un lookup individuel hors scraping Apify. Ne jamais construire un bloc 2 sans avoir d'abord vérifié ce champ.

Si même avec `linkedin_sections=experience` le poste actuel n'a pas de nom d'entreprise clair ou de date de début (ex: rôle salarié générique, freelance sans structure nommée), appliquer les cas particuliers déjà documentés dans `evo_system_type2_pas_de_post_pertinent.txt` (reformulation autour du métier) — ne jamais laisser le bloc 2 vide ou l'omettre.
