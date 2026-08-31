# Icebreaker Media Buying V3 - message LinkedIn fixe avec numero WhatsApp

## Contexte
Message envoye via DM LinkedIn (pas WhatsApp direct) a des media buyers 1er degre connectes sur les comptes Unipile. Structure fixe en 2 blocs :
1. Accroche personnalisee sur un fait concret et verifie du profil du contact (resultat chiffre, client notable, specificite).
2. Proposition de partenariat + numero WhatsApp en signature pour que CE SOIT LE CONTACT qui recontacte s'il est interesse (pas d'envoi WhatsApp direct par nous).

Le corps du message est TOUJOURS LE MEME dans sa structure - seule la phrase d'accroche change par contact. Le numero WhatsApp de contact reste fixe : +33 7 86 66 35 03.

## Structure du message

```
Salut [Prenom], [fait concret et verifie sur le profil du contact], c'est un sacre palmares / c'est exactement le type de profil que je recherche. Je recherche un partenariat à faire avec une personne spécialisée dans le media buying, si jamais t'es disponible on peut en discuter quelques minutes au téléphone.

Je te laisse le numéro WhatsApp à joindre si jamais t'es intéressé : +33 7 86 66 35 03.
```

## Regles de personnalisation
- [Prenom] : prenom exact du contact.
- Accroche : UNIQUEMENT un fait verifie sur le profil reel du contact (headline, chiffres, clients cites, resultats). Ne jamais inventer un post ou un resultat non verifie.
- Le corps du message (proposition de partenariat + phrase WhatsApp) ne change jamais - seule l'accroche personnalisee varie.
- Le numero WhatsApp +33 7 86 66 35 03 est fixe pour tous les envois.

## Exemples de reference (a suivre exactement pour le ton et la structure)

### Exemple 1 - Valentin Carougeat
```
Salut Valentin,

Trident et ses plus de 100 clients accompagnés (Submagic, Studeria, Livestorm...), c'est un sacré palmarès. Je recherche un partenariat avec une personne spécialisée dans le media buying, si jamais t'es disponible on peut en discuter quelques minutes au téléphone.

Je te laisse le numéro WhatsApp à joindre si jamais t'es intéressé : +33 7 86 66 35 03.
```

### Exemple 2 - Sébastien Quercia
```
Salut Sébastien, ton rôle chez Scale Lab sur l'acquisition Meta Ads pour accompagner les entrepreneurs, c'est exactement le type de profil que je recherche. Je recherche un partenariat à faire avec une personne spécialisée dans le media buying, si jamais t'es disponible on peut en discuter quelques minutes au téléphone.

Je te laisse le numéro WhatsApp à joindre si jamais t'es intéressé : +33 7 86 66 35 03.
```

### Exemple 3 - Florian Lampart
```
Salut Florian, +31 entreprises accompagnées sur Google Ads et +120 apprenants formés au SEO/SEA, c'est un sacré palmarès. Je recherche un partenariat à faire avec une personne spécialisée dans le media buying, si jamais t'es disponible on peut en discuter quelques minutes au téléphone.

Je te laisse le numéro WhatsApp à joindre si jamais t'es intéressé : +33 7 86 66 35 03.
```

## Processus d'envoi (canal LinkedIn, pas WhatsApp direct)
- Ce message est envoye en DM LinkedIn a des media buyers deja connectes 1er degre sur un compte Unipile (Martin, Keanu, Jules, Jean-Pierre, Thomas...).
- Avant chaque envoi : verifier qu'il n'existe pas deja une conversation avec ce contact sur le compte utilise (skip si historique/refus existant).
- Encodage : toujours envoyer via fichier texte UTF-8 (pas de variable shell inline) pour eviter la corruption des accents.
- Espacement : 1 a 2 minutes minimum entre deux envois sur le MEME compte LinkedIn. Jamais d'envoi simultane sur un meme compte.
- Rotation de comptes : Martin -> Keanu -> Jules -> Jean-Pierre -> Thomas, un contact a la fois.
- Objectif du message : que le media buyer recontacte lui-meme sur le numero WhatsApp +33 7 86 66 35 03 s'il est interesse - pas d'envoi WhatsApp direct depuis notre cote vers son numero.
- Envoi manuel/valide au fur et a mesure, pas de boucle automatisee sans supervision.

## Liste des contacts avec numero de telephone deja identifies (pour rappel si le contact repond sur WhatsApp)

| Nom | Telephone | Expertise |
|---|---|---|
| Marwen Maadi | +216 55 861 469 | Responsable Marketing Digital, Meta Ads, Digital Acquisition |
| Sébastien Quercia | 06 82 07 43 09 | Acquisition Meta Ads (Scale Lab) |
| Valentin Carougeat | 06 78 64 03 10 | Fondateur Trident, agence Paid, +100 clients |
| Gexan Duhalde | 06 68 19 16 51 | Meta Ads |
| Thibault Fayol | 06 78 45 02 51 | Consultant SEA, 4M€ pilotés, 140k leads |
| Florian Lampart | 06 25 35 69 42 | Expert & formateur Google Ads/Facebook Ads |
| Damien Plutino | 06 50 12 43 94 | Funnels/sales, €29M+ générés (à requalifier) |
| Vincent Colleu | +230 5476 6824 | Pub PME, +4M€ pilotés (Bioderma, Withings) |
| Sébastien Rech | 07 56 81 89 89 | Media Buying, 11M€+ investis en publicité |
| Roxane M. | 06 14 10 27 18 | Media Buyer, Meta & Google Ads |
| Martial Etcheverry | 06 06 77 16 14 | Tunnels de vente & Meta Ads |

## Changelog
- V1 : template long avec deal 3000€ detaille + CTA "15 minutes" + lien profil.
- V2 : structure identique a l'icebreaker habituel, CTA final change en proposition de partenariat.
- V3 (version actuelle) : message court et fixe, accroche factuelle personnalisee + proposition de partenariat + numero WhatsApp en signature pour que le contact recontacte lui-meme. C'est le template de reference a utiliser desormais pour tous les envois.
