# Règles strictes — Icebreakers (Type 1 uniquement, toujours, toujours, toujours)

Document de garde-fou. À consulter obligatoirement avant d'écrire ou d'envoyer un icebreaker, quel que soit le contexte (compte, urgence, absence de données complètes).

## ⚠️ Règle absolue (2026-08-24) : Type 2 désactivé, Type 1 obligatoire dans tous les cas

**Le Type 2 (icebreaker "4 blocs" basé sur la durée/entreprise du profil, sans référence à un post) n'est PLUS UTILISÉ, dans AUCUN cas, même si le prospect n'a aucun post visible.** Le format n'est pas supprimé de la documentation (conservé plus bas à titre d'historique), mais il ne doit plus jamais être choisi pour un envoi.

L'icebreaker doit TOUJOURS, TOUJOURS, TOUJOURS rebondir sur un des derniers posts du prospect, même si aucun de ces posts n'est parfaitement "pertinent" au sens strict de l'ancienne règle (événement/plainte/réaction). Rebondir sur un post, quel qu'il soit, est toujours jugé plus pertinent que le format Type 2. En pratique :
1. Regarder les derniers posts du prospect (pas seulement le tout dernier).
2. Choisir celui qui se prête le mieux à une réaction authentique — même un post "de valeur"/promotionnel ou un post ancien peut servir de point d'accroche, du moment que la réaction reste sincère et que la question rebondit vraiment dessus.
3. Si le profil semble n'avoir vraiment aucun post après vérification complète (cas rarissime), ne pas basculer sur le Type 2 : élargir la recherche (reposts commentés, pagination plus profonde) avant de conclure. Le Type 2 reste desactivé même dans ce cas — remonter le cas plutôt que d'envoyer un Type 2.

Raison : le rebond sur un post réel donne un taux de réponse largement supérieur à un icebreaker générique basé sur le profil, même quand le post disponible n'est pas un cas d'école (événement/plainte). Mieux vaut un Type 1 imparfait qu'un Type 2, quelle que soit la situation.

## Règle 0 — un icebreaker est réservé au tout premier message, jamais si une conversation existe déjà

Avant même d'écrire un icebreaker, vérifier qu'AUCUNE conversation n'existe déjà avec ce prospect sur le compte LinkedIn concerné. Un icebreaker ne s'envoie que si c'est le tout premier message échangé avec cette personne. Dès qu'un message — peu importe lequel, peu importe qui l'a envoyé — existe déjà dans l'historique, ce n'est plus un icebreaker : passer en mode reprise/relance de conversation, jamais renvoyer un icebreaker.

Méthode de vérification fiable (obligatoire) : paginer intégralement `/chats?account_id=X&limit=100` en suivant le `cursor` jusqu'à `null`, puis matcher sur le champ `attendee_provider_id` des résultats retournés. Les filtres query params `attendee_id`/`attendee_provider_id` passés directement à `/chats` sont PEU FIABLES et silencieusement ignorés par l'API (retournent toujours le même lot des ~100 chats les plus récents, indépendamment du filtre) — ne jamais s'y fier seul, toujours repasser par la pagination complète + matching local.

## Type 1 — seul format utilisé (aucune limite d'ancienneté sur le post)

Fichier source : `evo_system_type1_post_pertinent.txt`

Condition d'usage : toujours rebondir sur un des derniers posts du prospect. Il n'y a pas de fenêtre de fraîcheur : un post d'il y a 4 mois, 8 mois ou plus reste utilisable tant qu'il permet une réaction sincère. Priorité aux posts de type événement, plainte/coup de gueule justifié, ou réaction/opinion tranchée quand ils existent — mais un post "de valeur" (conseil, framework) ou un post plus promotionnel peut aussi servir de point d'accroche si aucun post prioritaire n'est disponible : mieux vaut réagir sincèrement à ce post-là que de ne pas rebondir du tout.

Format obligatoire (Variante 2, comportement par défaut) :
- "Helllo [prénom]"
- Courte phrase d'ouverture qui annonce la réaction au post (reformulée à chaque fois)
- Réaction/observation courte alignée sur le type de post (accord sincère si plainte/réaction — ne JAMAIS contredire — intérêt si événement ou post de valeur)
- Question courte et spécifique qui rebondit sur le post, obligatoire en fin de message
- 2-3 lignes maximum, jamais de PS, jamais de signature

## Type 2 — DÉSACTIVÉ, conservé ici uniquement à titre historique/documentaire

⚠️ Ce format ne doit plus être utilisé, dans aucun cas, depuis le 2026-08-24 (voir règle absolue en tête de document). Conservé ci-dessous uniquement pour mémoire.

Fichiers source (historiques) : `evo_system_type2_pas_de_post_pertinent.txt` / `type2_system_final.txt`

Ancien format (4 blocs séparés par une ligne vide) :
1. "Helllo [prénom]"
2. Durée EXACTE + nom d'entreprise EXACT tirés du profil réel — jamais approximés, jamais inventés (ex: "depuis 2006", pas "bientôt 20 ans"). Cas particulier indépendant/salarié non-fondateur : reformuler autour du métier, jamais "tu as lancé [Self-employed]".
3. Question sur le ciblage/l'audience du prospect selon son profil.
4. PS obligatoire, dans cet ordre de priorité strict :
   - (a) Bannière disponible → détail visuel RÉEL et précis observé dans l'image
   - (b) Pas de bannière mais photo de profil disponible → détail visuel réel de la photo
   - (c) Ni l'un ni l'autre → fallback "PS je me permets de te tutoyer ahah :)"

## Règles communes

- 1 seul emoji maximum, jamais l'emoji 😄 (banni sous aucun prétexte), préférer 😉 si besoin, dans le doute mieux vaut n'en mettre aucun
- Jamais de symboles type "+", "&", "/", "->", "=" dans le corps du message
- Tous les accents français corrects, vérifiés mot par mot
- Jamais de tiret cadratin/demi-cadratin
- Jamais de guillemets autour du message final complet
- Jamais de formule de politesse générique ("merci pour la connexion", "j'espère que tu vas bien")
- Tutoiement tout du long

## Erreur constatée à ne plus jamais reproduire (2026-07-23)

Sur un lot de 15 icebreakers, 7 ont été écrits directement "à la main" dans la conversation, sans repasser par les fichiers de règles ci-dessus, produisant un troisième format hybride non documenté. Cause racine : générer un icebreaker de mémoire au lieu de vérifier explicitement le contenu réel des posts du prospect avant d'écrire quoi que ce soit.

Correctif permanent : avant tout envoi d'icebreaker, vérifier explicitement les posts disponibles et respecter le format Type 1 à la lettre — ne jamais produire un troisième format, même sous contrainte de temps ou de volume (ex: rounds d'envoi échelonnés, lots de 10+, urgence perçue).

## Changement de règle (2026-08-21) — suppression de la fenêtre de 2 mois sur le Type 1

Le Type 1 est le cas par défaut et prioritaire, sans aucune limite d'ancienneté sur le post — un post pertinent (événement, plainte/réaction justifiée) reste exploitable en Type 1 quel que soit son âge (2 mois, 6 mois, 1 an...).

## Changement de règle (2026-08-24) — Type 2 désactivé définitivement

Le Type 2 est désactivé dans tous les cas, y compris en l'absence apparente de tout post pertinent. Voir la règle absolue en tête de document. Toujours privilégier un rebond sur un post existant, même imparfait, plutôt que le format 4-blocs basé sur le profil seul.
