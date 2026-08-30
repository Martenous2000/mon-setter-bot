# Icebreaker Media Buying V2 - 3 temps

## Contexte
Version V2 de l'icebreaker media buying. Meme structure que la V1 (3 temps), 3eme temps identique tel que redonne par l'utilisateur. A envoyer manuellement, un contact a la fois - PAS d'envoi automatise en boucle (risque de ban LinkedIn sur les comptes Martin/Keanu/Jules/Jean-Pierre).

## Repartition des comptes (round-robin manuel)
- Round 1 : compte Martin
- Round 2 : compte Keanu
- Round 3 : compte Jules
- Round 4 : compte Jean-Pierre
- Des qu'un contact repond ou genere un lead, on s'arrete sur ce fil (pas de relance automatique).

## Message 1 (accroche)

```
Salut [Prenom],

Je vois que tu es [expertise/positionnement Meta Ads du contact], ca tombe bien parce que j'ai un deal qui pourrait t'interesser.
```

## Message 2 (offre)

```
Je gere une agence de prospection IA sur LinkedIn : setup complet et IA conversationnelle qui prend les rendez-vous automatiquement. Normalement je facture ca 3000€ de setup, avec un forfait recurrent ensuite.

Voici le deal que je te propose. Je t'installe mon systeme gratuitement, le setup a 3000€ offert, et tu l'utilises pour trouver TES clients a toi. En echange, tu me fais tourner une campagne pub a hauteur du meme montant pour mon activite. On ne part pas de zero non plus : je fais deja tourner des Ads en interne, donc c'est un canal en plus pour moi, pas un pari dans le vide.

Zero echange d'argent. Chacun couvre ses frais reels, moi les tokens IA et le scraping, toi le budget pub, et chacun repart avec des leads dans son domaine.
```

## Message 3 (call to action)

```
Je recherche un partenariat a faire avec un(e) media buyer, si jamais t'es disponible on peut en discuter quelques minutes au telephone demain ?
```

## Exemple rempli (Anthony Berger - 2eme contact du tableau)

```
Salut Anthony,

Je vois que tu aides les prestataires et infopreneurs a generer des clients avec Meta Ads, ca tombe bien parce que j'ai un deal qui pourrait t'interesser.

Je gere une agence de prospection IA sur LinkedIn : setup complet et IA conversationnelle qui prend les rendez-vous automatiquement. Normalement je facture ca 3000€ de setup, avec un forfait recurrent ensuite.

Voici le deal que je te propose. Je t'installe mon systeme gratuitement, le setup a 3000€ offert, et tu l'utilises pour trouver TES clients a toi. En echange, tu me fais tourner une campagne pub a hauteur du meme montant pour mon activite. On ne part pas de zero non plus : je fais deja tourner des Ads en interne, donc c'est un canal en plus pour moi, pas un pari dans le vide.

Zero echange d'argent. Chacun couvre ses frais reels, moi les tokens IA et le scraping, toi le budget pub, et chacun repart avec des leads dans son domaine.

Je recherche un partenariat a faire avec un(e) media buyer, si jamais t'es disponible on peut en discuter quelques minutes au telephone demain ?
```

## Liste des 34 contacts (media buyers Meta Ads, 1er degre, hors e-commerce)

| # | Compte source | Profil |
|---|---|---|
| 1 | Martin | https://www.linkedin.com/in/sonia-attou |
| 2 | Martin | https://www.linkedin.com/in/berger-anthony |
| 3 | Martin | https://www.linkedin.com/in/hearthodouto |
| 4 | Martin | https://www.linkedin.com/in/marwen-maadi-responsable-marketing-digital |
| 5 | Martin | https://www.linkedin.com/in/florian-grossea |
| 6 | Martin | https://www.linkedin.com/in/julien-marchon-761b38259 |
| 7 | Martin | https://www.linkedin.com/in/ludovic-frit |
| 8 | Martin | https://www.linkedin.com/in/dylan-seguin-marketing |
| 9 | Martin | https://www.linkedin.com/in/lucas-orchiller-bbb28a193 |
| 10 | Martin | https://www.linkedin.com/in/ahmed-le-marketeur |
| 11 | Martin | https://www.linkedin.com/in/kevin-bucher-🚀-7bb83383 |
| 12 | Martin | https://www.linkedin.com/in/mikom-communication-et-publicité-224272375 |
| 13 | Keanu | https://www.linkedin.com/in/quentin-boileau-809939221 |
| 14 | Keanu | https://www.linkedin.com/in/florian-grossea |
| 15 | Keanu | https://www.linkedin.com/in/mathéo-girard-472922402 |
| 16 | Keanu | https://www.linkedin.com/in/martin-faucheux |
| 17 | Keanu | https://www.linkedin.com/in/charly-elbaz-25228b96 |
| 18 | Jules | https://www.linkedin.com/in/benjaminkoch748 |
| 19 | Jules | https://www.linkedin.com/in/berger-anthony |
| 20 | Jules | https://www.linkedin.com/in/dylan-seguin-marketing |
| 21 | Jules | https://www.linkedin.com/in/adrienlacour |
| 22 | Jean-Pierre | https://www.linkedin.com/in/elina-santala |
| 23 | Jean-Pierre | https://www.linkedin.com/in/sedik-naili |
| 24 | Jean-Pierre | https://www.linkedin.com/in/berger-anthony |
| 25 | Jean-Pierre | https://www.linkedin.com/in/nmartinez2212 |
| 26 | Jean-Pierre | https://www.linkedin.com/in/florian-grossea |
| 27 | Jean-Pierre | https://www.linkedin.com/in/mathis-mampon |
| 28 | Jean-Pierre | https://www.linkedin.com/in/clement-marquet |
| 29 | Jean-Pierre | https://www.linkedin.com/in/sebastien-quercia |
| 30 | Jean-Pierre | https://www.linkedin.com/in/jeremy-cussey |
| 31 | Thomas | https://www.linkedin.com/in/sitraka-ramamonjisoa-3a3775282 |
| 32 | Thomas | https://www.linkedin.com/in/ludovic-frit |
| 33 | Thomas | https://www.linkedin.com/in/guillaume-guersan |
| 34 | Thomas | https://www.linkedin.com/in/ludovic-ledoux |

## Note importante
Envoi manuel uniquement, contact par contact. Ne pas automatiser l'envoi en boucle sur intervalle fixe (40-70s) avec rotation de comptes : ce pattern est detecte par LinkedIn comme automatisation et expose les comptes a une restriction ou un ban.

## Changelog vs V1
Le 3eme temps (call to action) est identique a la V1. Aucun changement de fond sur le message - creation de ce fichier V2 pour respecter le versioning demande.
