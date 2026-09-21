# prompts/job-scraper/

Prompts versionnés du module de détection d'opportunités via offres d'emploi commerciales
(workflow n8n `job-scraper-opportunities.workflow.json`).

## Fichiers

- `qualification.md` : évalue une offre d'emploi détectée et produit un score 0-100 explicable, une lecture du besoin réel, un angle commercial recommandé.
- `message-generation.md` : génère le brouillon de premier message d'approche pour le décideur identifié, à partir du résultat de qualification. Reste toujours un brouillon soumis à validation humaine (jamais d'envoi automatique).

## Articulation avec le reste du repo

Ces deux prompts ne redéfinissent pas la méthodologie de setting : ils s'appuient sur
`prompts/principes.md` (méthodologie générique, rapport/déduction implicite/phases/signaux
de feu vert) et sur le persona du compte concerné dans `prompts/personas/<persona_key>.md`
(ton, langue, ICP, offre, anti-cibles). Le node LLM qui appelle `message-generation.md`
doit toujours charger le persona du compte en plus de ce prompt, comme le fait déjà le
brain (`main.py`) pour les conversations de setting classiques.

`qualification.md` lit aussi le persona du compte pour appliquer les anti-critères durs
propres à ce compte (ex. filtre géographique strict chez Enzo) sans les généraliser aux
autres comptes.

## Pourquoi des fichiers séparés plutôt que du texte dans le workflow n8n

Comme le reste du repo (personas, principes, icebreakers), ces prompts sont versionnés en
Markdown pour être lisibles, diffables et modifiables sans toucher au JSON du workflow.
Le node LLM du workflow les charge par HTTP (raw GitHub) ou par copier-coller dans le node,
selon la méthode déjà utilisée ailleurs dans `n8n/` pour charger `prompts/`.
