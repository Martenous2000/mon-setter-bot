# Règles strictes : Icebreakers (Type 1 prioritaire, Type 2 pour Martin et agences IA, Type 3 en fallback strict, Type 4 désactivé)

Document de garde-fou. À consulter obligatoirement avant d'écrire ou d'envoyer un icebreaker, quel que soit le contexte (compte, urgence, absence de données complètes).

## ⚠️ Règle absolue (mise à jour 2026-10-10) : Type 1 dès qu'il existe au moins 1 post exploitable, Type 3 uniquement si 0 post

⚠️ **Exception (2026-10-19) : pour Martin et les comptes agences IA, l'icebreaker à utiliser est le Type 2 (voir plus bas), à la place du Type 1.**

**Dès qu'il existe AU MOINS 1 post ou repost sur le profil du prospect, le Type 1 est obligatoire.** Un seul post suffit : l'IA doit s'appuyer dessus, même si ce n'est pas un post "parfait" au sens de l'ancienne règle (événement/plainte/réaction). Il n'y a pas de seuil minimum de posts à comparer entre eux : un post disponible = Type 1 utilisé.

**Le Type 3 (nouveau format ci-dessous, basé sur le rôle/l'entreprise/l'ancienneté du profil) ne s'utilise QUE quand le profil n'a vraiment AUCUN post ni repost, après vérification complète** (reposts commentés inclus, pagination suffisamment profonde avant de conclure à zéro post).

En pratique, pour choisir le type :
1. Regarder les derniers posts et reposts du prospect (pas seulement le tout dernier).
2. S'il y a au moins 1 post/repost exploitable : Type 1, toujours. Choisir celui qui se prête le mieux à une réaction authentique : même un post "de valeur"/promotionnel ou un post ancien peut servir de point d'accroche, du moment que la réaction reste sincère et que la question rebondit vraiment dessus.
3. Si le profil n'a vraiment aucun post ni repost après vérification complète (pagination profonde) : Type 3, le nouveau format basé sur le profil (ci-dessous).
4. Le Type 4 (ancien format "4 blocs", voir plus bas) reste désactivé dans tous les cas, y compris en l'absence de post : ne jamais y basculer, utiliser le Type 3 à la place.

Raison : le rebond sur un post réel donne un taux de réponse largement supérieur à un icebreaker générique basé sur le profil, même quand le post disponible n'est pas un cas d'école (événement/plainte). Le Type 3 n'est qu'un filet de sécurité pour les profils sans aucune activité visible, jamais un choix par défaut ou de confort.

## Règle 0 : un icebreaker est réservé au tout premier message, jamais si une conversation existe déjà

Avant même d'écrire un icebreaker, vérifier qu'AUCUNE conversation n'existe déjà avec ce prospect sur le compte LinkedIn concerné. Un icebreaker ne s'envoie que si c'est le tout premier message échangé avec cette personne. Dès qu'un message existe déjà dans l'historique (peu importe lequel, peu importe qui l'a envoyé), ce n'est plus un icebreaker : passer en mode reprise/relance de conversation, jamais renvoyer un icebreaker.

Méthode de vérification fiable (obligatoire) : paginer intégralement `/chats?account_id=X&limit=100` en suivant le `cursor` jusqu'à `null`, puis matcher sur le champ `attendee_provider_id` des résultats retournés. Les filtres query params `attendee_id`/`attendee_provider_id` passés directement à `/chats` sont PEU FIABLES et silencieusement ignorés par l'API (retournent toujours le même lot des ~100 chats les plus récents, indépendamment du filtre) : ne jamais s'y fier seul, toujours repasser par la pagination complète + matching local.

## Type 1 : cas par défaut dès qu'il existe au moins 1 post exploitable (aucune limite d'ancienneté sur le post)

Fichier source : `evo_system_type1_post_pertinent.txt`

Condition d'usage : toujours rebondir sur un des derniers posts du prospect dès qu'au moins 1 existe. Il n'y a pas de fenêtre de fraîcheur : un post d'il y a 4 mois, 8 mois ou plus reste utilisable tant qu'il permet une réaction sincère. Priorité aux posts de type événement, plainte/coup de gueule justifié, ou réaction/opinion tranchée quand ils existent : mais un post "de valeur" (conseil, framework) ou un post plus promotionnel peut aussi servir de point d'accroche si aucun post prioritaire n'est disponible : mieux vaut réagir sincèrement à ce post-là que de ne pas rebondir du tout.

Format obligatoire (Variante 2, comportement par défaut) :
- "Helllo [prénom]"
- Courte phrase d'ouverture qui annonce la réaction au post (reformulée à chaque fois)
- Réaction/observation courte alignée sur le type de post (accord sincère si plainte/réaction : ne JAMAIS contredire : intérêt si événement ou post de valeur)
- Question courte et spécifique qui rebondit sur le post, obligatoire en fin de message
- 2-3 lignes maximum, jamais de PS, jamais de signature

## Type 2 : icebreaker du compte Martin et des comptes agences IA (modèle fourni par le client, enregistré le 2026-10-19)

**Comptes concernés : Martin Cuisinier et les comptes qui ciblent les agences IA (groupe CLIENT ACQUISITION OS™ : Martin, Jean-Pierre, Jules, Julien, Thomas, Mathias, etc.).** Pour ces comptes, c'est ce modèle qui s'applique à la place du Type 1 générique.

Modèle exact (la partie entre crochets est toujours personnalisée, jamais laissée telle quelle) :

```
Hello [prénom], j'ai vu ton dernier post sur [courte remarque, 1 phrase]

Je ne vais pas te faire perdre ton temps : on a fait passer Baptiste Hoguet, dirigeant d'agence comme toi, de 8 à une quarantaine de rendez-vous qualifiés par mois en 4 semaines, sans qu'il prospecte lui-même.

J'ai fait une vidéo de quelques minutes qui explique ce qu'on a fait, ça t'intéresse que je te l'envoie ?
```

Exemple fourni par le client :

```
Hello Florian, j'ai vu ton dernier post, le coup du webdesigner qui n'a toujours pas son propre site, assez ironique mais tellement vrai.

Je ne vais pas te faire perdre ton temps : on a fait passer Baptiste Hoguet, dirigeant d'agence comme toi, de 8 à une quarantaine de rendez-vous qualifiés par mois en 4 semaines, sans qu'il prospecte lui-même.

J'ai fait une vidéo de quelques minutes qui explique ce qu'on a fait, ça t'intéresse que je te l'envoie ?
```

Règles :
- Tutoiement, "Hello" (pas "Helllo"), 3 paragraphes séparés par une ligne vide, dans cet ordre.
- La remarque sur le post tient en une seule phrase, spécifique au sujet exact du post (jamais une reformulation vague).
- Baptiste Hoguet est cité nommément sur LinkedIn, comme dans la version Instagram. Cela remplace l'ancienne consigne "rester anonyme sur LinkedIn".
- Le message se termine par une question (le modèle d'origine n'avait pas de point d'interrogation, ajouté pour respecter la règle "toujours finir par une question").
- Le cas où le prospect n'a aucun post n'est pas défini pour ce type par le client : à confirmer avec lui avant de l'utiliser dans ce cas (en attendant, le Type 3 reste le filet de sécurité).

## Type 3 : fallback obligatoire quand le profil a 0 post et 0 repost (ancien "Type 2", renommé Type 3 le 2026-10-19 ; l'ancien format "4 blocs" est le Type 4 désactivé ci-dessous)

⚠️ **Nouveau format, actif depuis le 2026-10-10.** À utiliser uniquement quand le profil n'a vraiment aucun post ni repost après vérification complète (voir règle absolue en tête de document).

Fichier source : à créer/référencer comme `evo_system_type2_profil_sans_post.txt` si un fichier dédié est utilisé ailleurs dans le pipeline.

Structure obligatoire, dans cet ordre, toujours identique :
1. "Salut [prénom],"
2. "je vois que tu es [rôle/titre exact tiré du profil] chez [nom d'entreprise exact] depuis [durée exacte, calculée depuis `work_experience[0].start`, jamais approximée ni inventée]."
3. Une remarque personnalisée sur son business : observer son profil LinkedIn, son activité, son offre, sa spécialisation pour formuler une remarque naturelle et pertinente montrant un intérêt réel pour son activité. Ne jamais supposer une information qui n'est pas vérifiable sur le profil.
4. Une question ouverte pour comprendre son positionnement : savoir s'il travaille uniquement avec un type de client/cible ou aussi avec d'autres profils, de façon naturelle et spécifique à son activité.

Règles de rédaction :
- Ton naturel, humain, conversationnel, comme un message spontané
- Phrases simples, fluides et directes
- La question doit être pertinente par rapport à l'activité du prospect et permettre d'obtenir une information concrète sur sa cible
- Éviter les formulations commerciales, les compliments artificiels, les phrases génériques
- Tutoiement systématique
- Un seul message prêt à être envoyé, sans introduction ni explication

### Exemple de la forme visée
```
Salut Jean-Pierre, je vois que tu es CEO chez Acquisition Pro depuis 2 ans et 3 mois. J'ai vu que tu te spécialisais à fond sur l'acquisition automatisée pour les agences IA. Et du coup je me demandais, tu travailles uniquement avec des agences IA ou aussi avec d'autres types d'agences B2B ?
```

⚠️ Cas particulier indépendant/salarié non-fondateur : reformuler autour du métier réel, jamais "tu as lancé [Self-employed]".

## Type 4 : DÉSACTIVÉ, conservé ici uniquement à titre historique/documentaire (anciennement appelé "Type 2", puis "Type 3")

⚠️ Ce format ne doit JAMAIS être utilisé, dans aucun cas, y compris en l'absence de tout post. Quand il n'y a 0 post, c'est le Type 3 ci-dessus (nouveau format rôle/entreprise/durée) qui s'applique, jamais ce Type 4. Conservé ci-dessous uniquement pour mémoire.

Fichiers source (historiques) : `evo_system_type2_pas_de_post_pertinent.txt` / `type2_system_final.txt`

Ancien format (4 blocs séparés par une ligne vide) :
1. "Helllo [prénom]"
2. Durée EXACTE + nom d'entreprise EXACT tirés du profil réel : jamais approximés, jamais inventés (ex: "depuis 2006", pas "bientôt 20 ans"). Cas particulier indépendant/salarié non-fondateur : reformuler autour du métier, jamais "tu as lancé [Self-employed]".
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
- Jamais de formule de politesse générique ("merci pour la connexion", "j'espère que tu vas bien") — s'applique au Type 1 et au Type 3 tel que rédigé ci-dessus (qui n'utilise pas cette formule)
- Tutoiement tout du long

## Erreur constatée à ne plus jamais reproduire (2026-07-23)

Sur un lot de 15 icebreakers, 7 ont été écrits directement "à la main" dans la conversation, sans repasser par les fichiers de règles ci-dessus, produisant un troisième format hybride non documenté. Cause racine : générer un icebreaker de mémoire au lieu de vérifier explicitement le contenu réel des posts du prospect avant d'écrire quoi que ce soit.

Correctif permanent : avant tout envoi d'icebreaker, vérifier explicitement les posts disponibles et respecter le format en vigueur (Type 1 si ≥1 post, Type 3 si 0 post) à la lettre : ne jamais produire un format hybride non documenté, même sous contrainte de temps ou de volume (ex: rounds d'envoi échelonnés, lots de 10+, urgence perçue).

## Changement de règle (2026-08-21) : suppression de la fenêtre de 2 mois sur le Type 1

Le Type 1 est le cas par défaut et prioritaire dès qu'au moins 1 post existe, sans aucune limite d'ancienneté sur le post : un post pertinent (événement, plainte/réaction justifiée) reste exploitable en Type 1 quel que soit son âge (2 mois, 6 mois, 1 an...).

## Changement de règle (2026-10-10) : Type 3 réactivé sous nouveau format, uniquement en fallback 0-post ; ancien Type 3 renommé Type 4 et reste désactivé

Le Type 1 reste la priorité absolue dès qu'au moins 1 post ou repost est disponible, même un seul. Quand le profil n'a vraiment aucun post ni repost après vérification complète, le nouveau Type 3 (rôle/entreprise/durée + remarque business + question de positionnement, voir ci-dessus) s'applique, à la place de l'ancien format "4 blocs" (désormais Type 4, toujours désactivé).

## Changement de règle (2026-10-19) : nouveau Type 2 pour Martin et les agences IA ; ancien Type 2 renommé Type 3 ; ancien Type 3 renommé Type 4

Le client a fourni le modèle d'icebreaker "Type 2" de Martin et des comptes agences IA (voir la section Type 2 ci-dessus). L'ancien Type 2 (fallback rôle/entreprise/durée, utilisé uniquement quand le profil n'a aucun post) devient le **Type 3**. L'ancien Type 3 (format "4 blocs", désactivé) devient le **Type 4**, toujours désactivé. Les mentions de "Type 2" et "Type 3" dans les entrées de changelog datées d'avant le 2026-10-19 ont été renumérotées en conséquence.
