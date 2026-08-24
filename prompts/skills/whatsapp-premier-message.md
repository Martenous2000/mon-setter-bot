---
name: whatsapp-premier-message
description: Règles strictes pour générer le tout premier message WhatsApp envoyé à un prospect qui n'a jamais interagi avec moi (cible artisans/rénovation haut de gamme, sourcé depuis LinkedIn). À charger uniquement pour la génération du message d'ouverture de campagne WhatsApp, jamais pour une conversation déjà engagée.
---

# Premier message WhatsApp : règles de génération

## Le problème que ce message doit résoudre
Contrairement à LinkedIn, arriver sur WhatsApp est intrusif si ce n'est pas justifié. Le prospect doit comprendre en une phrase pourquoi je lui écris ici, sinon le message se lit comme du spam et se fait supprimer ou signaler immédiatement.

## Structure obligatoire (3 éléments, 2 à 4 phrases courtes maximum, jamais un pavé)
1. **Justification du canal** : une phrase courte qui explique pourquoi WhatsApp : toujours ancrée sur le fait que je l'ai repéré sur LinkedIn. Exemple de tournure (à reformuler, jamais copier) : "Je suis tombé sur ton profil LinkedIn et je me permets de te contacter directement ici, ça m'a semblé plus simple qu'un DM."
2. **Rebond personnalisé réel** : un élément concret et vérifiable tiré du profil LinkedIn (nom de l'entreprise, activité récente, post publié, spécialité visible sur le profil : jamais une généralité du type "j'ai vu que tu étais artisan"). Si aucun élément concret n'est disponible dans les données scrapées, ne jamais inventer : se rabattre sur le nom de l'entreprise et son secteur seulement.
3. **Question d'ouverture légère**, jamais un pitch, jamais une offre dans ce premier message. Le seul but de ce message est d'obtenir une réponse, pas de vendre.

## Ce que ce message ne fait JAMAIS
- Jamais de prix, jamais de mention de l'offre CLIENT ACQUISITION OS™ nommément
- Jamais de lien (Calendly, site, etc.) dans le premier message
- Jamais de ton publicitaire ("boostez votre activité", "solution clé en main")
- Jamais plus de 4 phrases courtes
- Jamais un emoji en ouverture de message, maximum un en fin de message, et seulement s'il apporte vraiment quelque chose

## Exemple de structure (à reformuler intégralement à chaque fois, jamais copié)
> Salut [Prénom], je suis tombé sur ton profil LinkedIn en repérant [nom entreprise] et [élément concret : post récent / spécialité / projet mentionné]. Je me permets de t'écrire directement ici plutôt que sur LinkedIn, ça me semblait plus direct. [Question légère liée à son activité ou son chantier en cours] ?

## Variables disponibles pour la personnalisation (fournies par le pipeline n8n)
- `prenom`, `nom_entreprise`, `poste`
- `dernier_post_texte` (si disponible, sinon absent)
- `specialite_visible` (déduite du profil : type de rénovation, matériaux, zone géographique)

## Règle de sécurité anti-ban
Si les données scrapées ne contiennent aucun élément concret exploitable (pas de post, pas de description d'activité claire), ne génère PAS de message : renvoie un statut `insufficient_data` pour que ce lead soit exclu de l'envoi automatique plutôt que d'envoyer un message générique qui sonnerait comme du spam.
