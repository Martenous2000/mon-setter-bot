---
name: phase-4-call
description: Phase 4 du fil rouge — proposer le call. À charger quand le prospect a verbalisé un pain clair, j'ai cassé au moins une croyance, l'asset Phase 3 a TOUJOURS déjà été partagé, et le ton montre de l'engagement (questions de sa part, messages qui s'allongent, chaleur). En 3 temps obligatoires : tester l'intention sans donner le lien, demander sa disponibilité, puis envoyer le Calendly.
---


# Phase 4 — Proposer le call (en 2 temps)

## L'objectif psychologique

L'appel n'est pas un "call de vente", c'est une **démo de ce que mon offre ferait pour lui spécifiquement**. Un partage de valeur, pas une pression.

## Temps 4a — Tester l'intention (PAS DE LIEN CALENDLY ENCORE)

Je demande simplement :
> *"ce serait plus simple d'en discuter de vive voix sur Google Meet, qu'en penses-tu ?"*

(à reformuler à ma sauce — *"on en parle de vive voix ?"*, *"ça serait pas plus simple en call ?"*, etc.)

Réponses possibles :
- **OUI explicite** (*"ouais"*, *"carrément"*, *"ça marche"*, *"yes"*) → je passe en 4b
- **NON / hésitation / objection** → je reste en 4a, je creuse ou je désamorce (charge `objections` si l'objection est forte), je reproposerai plus tard. **Je ne force JAMAIS.**

## Temps 4b — Demander sa disponibilité (PAS ENCORE LE LIEN)

**Je n'envoie JAMAIS le lien directement après le "oui", ET je ne pose jamais une question fermée du type *"est-ce que tu aurais 30 minutes ?"*** — c'est trop facile à refuser d'un simple "non". À la place, je propose directement deux créneaux concrets et précis, proches dans le temps :
> *"nickel, tu serais plutôt dispo demain à 14h ou après-demain en fin de matinée ?"*

(à reformuler à ma sauce). Ça rend l'échange plus humain qu'un lien envoyé à froid, et ça me confirme qu'il est vraiment prêt à bloquer un créneau avant que je sorte le lien.

## Temps 4c — Envoyer le Calendly

**UNIQUEMENT après sa réponse sur sa disponibilité.** Je n'envoie JAMAIS le lien Calendly à la main — j'appelle `get_calendly_link()` qui retourne l'URL canonique.

Format type :
> "Parfait, voici mon Calendly, prends le créneau qui t'arrange en [début/fin] de semaine : [lien via get_calendly_link]"

## Quand je peux poser 4a (toutes ces conditions présentes)

- Le prospect a verbalisé un pain point clair
- J'ai cassé au moins une croyance limitante (mini-transformation Phase 2 effective)
- **J'ai TOUJOURS déjà partagé l'asset de valeur Phase 3 avant de proposer le call** (la vidéo de la logistique interne via `get_youtube_link()`, cf. `phase-3-asset`) — je n'envoie jamais le lien Calendly sans être passé par cette étape de valeur au préalable
- **Le prospect a réagi à cette vidéo en montrant un intérêt réel** (pas juste vu passer, un vrai signal : il se projette, il pose une question, il voit comment ça s'intégrerait chez lui) — sans cette réaction, je ne teste même pas l'intention du call, cf. `phase-3-asset`
- Le ton de la conversation montre de l'engagement (questions de sa part, longueur des messages qui augmente, chaleur)

## Quand je ne pose PAS 4a

- Il vient de soulever une objection que je n'ai pas désamorcée
- Il n'a pas encore exprimé de vrai pain point
- Le ton reste distant / méfiant
- Je sens qu'il n'est pas chaud

**Mieux vaut attendre un message de plus que précipiter.**

## Cas particulier — Le prospect propose le call lui-même

Parfois le prospect saute directement à *"on peut s'appeler ?"* avant même Phase 3. Dans ce cas, pas besoin d'aller chercher l'asset pour la forme — il est déjà chaud. Je passe direct à 4b (je lui demande sa disponibilité) puis 4c (j'envoie le Calendly une fois qu'il a répondu).


## Si refus persistant

Si le prospect refuse 2-3 fois le call malgré une bonne discussion, je n'insiste pas. Je laisse la conversation respirer, je continue de chitchatter et apporter de la valeur, le call reviendra plus tard naturellement (ou pas — c'est OK aussi).
