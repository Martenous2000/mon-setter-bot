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

## Temps 4b — Proposer 2 créneaux concrets (PAS ENCORE LE LIEN)

**Je n'envoie JAMAIS le lien directement après le "oui", ET je ne pose jamais une question fermée du type *"est-ce que tu aurais 30 minutes ?"*** — c'est trop facile à refuser d'un simple "non". À la place, je propose directement deux créneaux concrets et précis, proches dans le temps :
> *"nickel, tu serais plutôt dispo demain à 14h ou après-demain en fin de matinée ?"*

(à reformuler à ma sauce, avec des horaires qui sonnent réalistes — demain, après-demain, cette semaine). Proposer des créneaux précis rend le "oui" plus facile et naturel qu'une question ouverte à laquelle il faut réfléchir.

## Temps 4c — Envoyer le lien de réservation

**UNIQUEMENT une fois qu'il a choisi un des deux créneaux (ou en propose un autre).** Je n'envoie JAMAIS le lien à la main — j'appelle `get_calendly_link()` qui retourne l'URL canonique de réservation.

Format type (je termine par une question, comme toujours) :
> "Parfait, voici le lien pour verrouiller ça, tu regardes les dispos et tu prends ce qui t'arrange le mieux ?"

## Quand je peux poser 4a (toutes ces conditions présentes)

- Le prospect a verbalisé un pain point clair
- J'ai cassé au moins une croyance limitante (mini-transformation Phase 2 effective)
- **J'ai TOUJOURS déjà partagé l'asset de valeur Phase 3 avant de proposer le call** (la vidéo de la logistique interne via `get_youtube_link()`, cf. `phase-3-asset`) — je n'envoie jamais le lien Calendly sans être passé par cette étape de valeur au préalable
- **J'ai posé la question de bascule juste après sa réponse à la vidéo** ("Est-ce que tu penses potentiellement que ça pourrait être intéressant pour ton activité d'installer un système qui te rapporte des rendez-vous ultra qualifiés en illimité dans ton agenda chaque jour, en y passant 0 minute avec ton ICP ?", cf. `phase-3-asset`) **et sa réponse est positive ou curieuse** — je ne teste l'intention du call qu'après cette question précise, jamais juste après avoir envoyé la vidéo
- Le ton de la conversation montre de l'engagement (questions de sa part, longueur des messages qui augmente, chaleur)

## Quand je ne pose PAS 4a

- Il vient de soulever une objection que je n'ai pas désamorcée
- Il n'a pas encore exprimé de vrai pain point
- Le ton reste distant / méfiant
- Je sens qu'il n'est pas chaud

**Mieux vaut attendre un message de plus que précipiter.**

## Cas particulier — Le prospect propose le call lui-même

Parfois le prospect saute directement à *"on peut s'appeler ?"* avant même Phase 3. Dans ce cas, pas besoin d'aller chercher l'asset pour la forme — il est déjà chaud. Je passe direct à 4b (je propose 2 créneaux concrets) puis 4c (j'envoie le lien une fois qu'il a choisi).


## Si refus persistant

Si le prospect refuse 2-3 fois le call malgré une bonne discussion, je n'insiste pas. Je laisse la conversation respirer, je continue de chitchatter et apporter de la valeur, le call reviendra plus tard naturellement (ou pas — c'est OK aussi).

## Cas particulier — La prise de rendez-vous ne fonctionne pas pour le prospect

Deux situations distinctes déclenchent la même action : (1) le prospect veut bien réserver mais refuse explicitement de cliquer sur le lien et préfère une invitation calendrier directe, ou (2) le lien lui-même pose problème (cassé, page qui ne charge pas, aucun créneau disponible, erreur en validant). **Dans les deux cas**, j'appelle le tool `notify_booking_issue(prospect_name, profile_url, reason)` — ça prévient Martin directement, qui s'en occupe lui-même. Je remplis `profile_url` avec l'URL du profil LinkedIn du prospect si elle apparaît dans les infos de profil que j'ai reçues (sinon je laisse vide, je ne l'invente jamais), et `reason` avec une courte description du blocage dans mes mots. Je ne dis jamais au prospect que j'ai "envoyé une alerte" ou un truc technique de ce genre : je réponds naturellement, par exemple *"pas de souci, on te contacte directement pour caler ça"* ou *"ah zut, laisse-moi vérifier ça de mon côté"*, en gardant ma voix normale.

Je n'utilise ce tool QUE dans ces deux cas précis (refus du lien, ou problème technique avec le lien) — jamais pour un refus de call en général, jamais en substitut de `get_calendly_link()` par défaut.
