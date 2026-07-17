const contactData = $('Evaluate Chat').first().json;
const prenom = contactData.prenom || '';
const accountId = contactData.accountId;
const providerId = contactData.providerId;
const profileUrl = contactData.profileUrl || '';
const headline = contactData.headline || contactData.description || '';
const name = contactData.name || '';
const companyName = contactData.companyName || '';
const dureeReelle = contactData.dureeReelle || '';
const coverPictureUrl = contactData.coverPictureUrl || '';
const profilePictureUrl = contactData.profilePictureUrl || '';

// Parse posts coming from Scrape Posts (HTTP node, text responseFormat)
let posts = [];
try {
  const raw = $input.first().json.data;
  if (raw && typeof raw === 'string') posts = JSON.parse(raw);
  else if (Array.isArray($input.first().json)) posts = $input.first().json;
  if (!Array.isArray(posts)) posts = [];
} catch(e) { posts = []; }

// Seuil "post recent" : 2 mois (60 jours), pas 14 jours.
const twoMonthsAgo = Date.now() - 60 * 86400000;
const parseDate = (v) => {
  if (!v) return 0;
  if (typeof v === 'object') return v.timestamp || (v.date ? new Date(v.date).getTime() : 0);
  return new Date(v).getTime();
};
const recentPosts = posts.filter(p => {
  if (p.type === 'reaction' || p.type === 'comment') return false;
  const dateMs = parseDate(p.postedAt) || parseDate(p.publishedAt) || parseDate(p.date);
  if (!dateMs) return false;
  const text = (p.text || p.content || '').trim();
  return dateMs > twoMonthsAgo && text.length > 20;
}).slice(0, 1);

const hasPosts = recentPosts.length > 0;
// Detection "independant sans societe" : le nom d'entreprise scrape est en fait un statut, pas une raison sociale.
const SELF_EMPLOYED_PATTERN = /^(self[- ]?employed|freelance|ind[ée]pendant|auto[- ]?entrepreneur)$/i;
const isSelfEmployed = companyName && SELF_EMPLOYED_PATTERN.test(companyName.trim());
const hasUsableBio = (companyName && dureeReelle) || headline.trim().length > 15;

if (!hasPosts && !hasUsableBio) {
  return [{ json: { accountId, providerId, prenom, headline, profileUrl, icebreaker: '', hasPosts, name, skip: true } }];
}

let systemPrompt, userContent;

if (hasPosts) {
  // TYPE 1 — reaction au dernier post (post detecte dans les 2 derniers mois, quelle que soit la date exacte a l'interieur de cette fenetre).
  const postText = (recentPosts[0].text || recentPosts[0].content || '').substring(0, 800);
  systemPrompt = "Tu ecris un message LinkedIn complet en reaction au dernier post de cette personne. Message direct, avec un vrai point de vue perso et tranchant, jamais un compliment vide, comme un pote qui reagit a chaud a ce qu'il vient de lire.\n\nIMPORTANT - orthographe : tu ecris en francais avec tous les accents corrects (e, e, a, u, o, c, i, etc.), exactement comme en francais standard. Ne retire jamais les accents d'un mot.\n\nREGLE ABSOLUE : tu es TOUJOURS d'accord avec la personne et tu vas TOUJOURS dans son sens. Tu ne contredis jamais son post, tu ne releves jamais une contradiction ou une incoherence chez elle, tu n'objectes jamais. Le point de vue tranchant sert a RENFORCER ou PROLONGER son idee (avec un angle perso, un exemple, une nuance qui va dans le meme sens), jamais a la remettre en question.\n\nFORMAT (obligatoire, un seul message, une seule fois) :\n\"Helllo [prenom] \" suivi directement (sans virgule) d'une reaction d'accord avec le post, genre \"assez d'accord avec ton post\" / \"carrement d'accord avec ton post\" / \"grave d'accord avec ton post\" / \"a fond d'accord avec ton post\" (varie la formule, mais toujours dans le sens de l'accord), puis l'idee centrale du post entre guillemets, puis \"...\", puis une phrase qui renforce ou prolonge son point de vue avec une vraie observation personnelle et tranchante qui va dans SON sens (pas une reformulation plate, un vrai ajout de valeur, quitte a etre direct/cash, mais jamais un argument contraire), puis OBLIGATOIREMENT une question courte et specifique en lien avec le post ou son activite pour relancer la conversation (le message ne doit JAMAIS se terminer sur l'opinion seule, toujours finir par une question).\n\nEXEMPLE (style cible exact, a adapter a chaque post, ne jamais copier tel quel) :\nPrenom \"Marc\", Post \"Le design ne fait pas la conversion\"\n->\nHelllo Marc assez d'accord avec ton post \"le design ne fait pas la conversion\"... c'est souvent l'offre et le message qui fait tout le boulot, le reste c'est du bullshit. Tu le vois comment toi, c'est quoi le vrai levier selon toi ?\n\nCONTRE-EXEMPLE A NE JAMAIS FAIRE (contredit la personne, interdit) :\nPost \"you don't need to hire a content agency\"\n-> \"pas sur d'etre d'accord... tu vends litteralement un service d'agence de contenu en disant qu'on n'a pas besoin d'agence de contenu\" (INTERDIT : ceci pointe une contradiction chez la personne au lieu d'aller dans son sens).\n\nINTERDIT :\n- Contredire, objecter, nuancer contre le post ou relever une incoherence chez la personne : va TOUJOURS dans son sens.\n- Terminer le message sans question : une question est OBLIGATOIRE a la fin.\n- \"Merci pour la connexion\", toute formule de politesse, tout \"j'espere que tu vas bien\".\n- Tout compliment vague (\"super post\", \"bien joue\", \"chapeau\", \"j'adore\").\n- Tiret cadratin \"—\" ou \"–\".\n- Plus d'un point d'exclamation dans tout le message.\n- Tout \"PS\" ou signature en fin de message.\n- Guillemets autour du message final complet (les guillemets internes autour du titre du post restent, eux, obligatoires).\n- Retirer les accents francais du texte.\n\nTu peux ponctuellement glisser un petit \"haha\" ou \":)\" si ca sonne naturel, jamais plus d'un.\nTutoie tout du long.\n\nReponds UNIQUEMENT avec le message final complet, en une seule fois, rien d'autre.";
  userContent = 'Prenom : ' + (prenom || '(aucun)') + '\nDernier post LinkedIn (publie dans les 2 derniers mois) :\n' + postText;
} else {
  // TYPE 2 — pas de post recent, on se base sur la bio / duree reelle / entreprise, avec PS sur une image reelle du profil (banniere puis photo de profil en repli).
  systemPrompt = "Tu ecris un message LinkedIn complet pour une premiere prise de contact, quand la personne n'a aucun post recent (moins de 2 mois) a commenter. Message chaleureux, naturel, jamais commercial, comme si un pote t'ecrivait.\n\nIMPORTANT - orthographe : tu ecris en francais avec tous les accents corrects (e, e, a, u, o, c, i, etc.), exactement comme en francais standard. Le seul caractere que tu evites reste l'apostrophe typographique (utilise l'apostrophe droite normale). Ne simplifie jamais un mot en retirant ses accents (ecris \"cree\", \"derniere\", \"annee\", jamais leurs versions sans accent).\n\nOn te donne la duree EXACTE et REELLE depuis laquelle la personne a lance son entreprise/activite (calculee a partir de la date de debut reelle sur son profil LinkedIn), le nom exact de l'entreprise, et une ou deux images de son profil LinkedIn si elles sont disponibles (banniere et/ou photo de profil). Tu dois utiliser CETTE duree et CE nom exacts, ne jamais en inventer d'autres, ne jamais les modifier.\n\nCAS PARTICULIER — personne independante sans societe nommee (le champ entreprise vaut litteralement \"Self-employed\", \"Freelance\", \"Independant\" ou equivalent, sans nom de societe reel derriere) : dans ce cas, le bloc 2 ne doit JAMAIS dire \"tu as lance [Self-employed]\" (ca ne veut rien dire). A la place, reformule autour du METIER/TITRE fourni dans la bio : \"Je vois que ca fait [duree exacte] que tu accompagnes [reformulation courte de l'activite depuis la bio] en independant, c'est trop bien !\" — toujours avec la duree exacte fournie, jamais de nom d'entreprise invente.\n\nFORMAT (obligatoire, exactement 4 blocs separes par une ligne vide, calque au maximum sur ce gabarit exact) :\n1. \"Helllo [prenom]\" (utilise le prenom fourni, sans virgule apres, avec tous ses accents).\n2. Cas normal (societe nommee) : \"Je vois que ca fait [duree exacte fournie] que tu as lance [nom_entreprise fourni], c'est trop bien !\". Cas independant (voir ci-dessus) : gabarit alternatif decrit plus haut. Un seul point d'exclamation autorise dans tout le message, et c'est ici.\n3. Exactement sur ce modele : \"Tu cibles exclusivement [cible sur son profil], car tu connais bien cette cible ou pour une autre raison ?\" - remplace [cible sur son profil] par la cible/audience reelle de la personne d'apres sa bio. Ne pose jamais une question generique sur le produit/la methode, la question doit toujours porter sur le ciblage/l'audience selon ce gabarit.\n4. Le PS renvoie TOUJOURS sur une image reelle du profil, jamais sur autre chose, selon cet ordre de priorite strict :\n   (a) Une image de BANNIERE (photo de couverture) est fournie -> tu observes un detail VISUEL REEL et PRECIS dans CETTE image (une couleur dominante, un style, un element graphique specifique que tu vois vraiment) et tu le formules dans le style \"PS : tres sympa ton branding, le [couleur/element observe] ca claque !\" ou une remarque equivalente et naturelle sur ce meme detail reel, jamais un compliment vague ou invente.\n   (b) Aucune banniere n'est fournie, mais une image de PHOTO DE PROFIL est fournie -> tu observes un detail VISUEL REEL et PRECIS de cette photo de profil a la place (un vetement, un decor, une expression, un accessoire, une couleur dominante) et tu le formules dans un style similaire et naturel, toujours factuel sur ce que tu vois vraiment.\n   (c) Ni banniere ni photo de profil exploitable n'est fournie -> tu remplaces ce bloc par : \"PS : je me permets de te tutoyer ahah :)\"\n\nTutoie tout du long.\n\nINTERDIT :\n- Plus d'un point d'exclamation dans tout le message.\n- Tiret cadratin ou tiret simple comme ponctuation.\n- Compliment vague ou generique sur l'image (jamais \"beau design\", \"joli visuel\" sans preciser QUOI precisement).\n- Dire \"tu as lance Self-employed\" ou toute variante ou le nom d'entreprise n'est pas une vraie raison sociale : utiliser le gabarit independant a la place.\n- S'ecarter du gabarit des blocs 2 et 3 ci-dessus.\n- Inventer une duree, un nom d'entreprise, ou un detail visuel differents de ceux fournis.\n- Guillemets autour du message.\n- Retirer les accents francais du texte : chaque mot doit garder son orthographe correcte avec accents.\n\nReponds UNIQUEMENT avec le message final complet (les 4 blocs, sauts de ligne inclus), rien d'autre.";

  let bloc2Context = '';
  if (isSelfEmployed) {
    bloc2Context = 'Statut : independant sans societe nommee (champ entreprise = "' + companyName + '")\nDuree exacte reelle : ' + (dureeReelle || '(inconnue)') + '\nActivite / titre (bio) : ' + (headline || '(vide)');
  } else if (companyName && dureeReelle) {
    bloc2Context = 'Nom entreprise/activite : ' + companyName + '\nDuree exacte reelle depuis le lancement : ' + dureeReelle;
  } else {
    bloc2Context = 'Aucune duree/entreprise exacte scrapee. Bio / Headline LinkedIn : ' + (headline || '(vide)');
  }

  let imageNote = '(Ni banniere ni photo de profil disponible pour le PS)';
  if (coverPictureUrl) imageNote = '(Une image de banniere est fournie en piece jointe pour le PS)';
  else if (profilePictureUrl) imageNote = '(Aucune banniere disponible, mais une photo de profil est fournie en piece jointe pour le PS)';

  userContent = 'Prenom : ' + (prenom || '(aucun)') + '\n' + bloc2Context + '\nBio / Headline LinkedIn : ' + (headline || '(vide)') + '\n' + imageNote;
}

let aiOutput = '';
try {
  const messageContent = [{ type: 'text', text: userContent }];
  // Cascade image pour le PS (uniquement cas "pas de post") : banniere en priorite, sinon photo de profil, sinon rien.
  if (!hasPosts) {
    const imageUrlToUse = coverPictureUrl || profilePictureUrl || '';
    if (imageUrlToUse) {
      try {
        const imgResp = await this.helpers.httpRequest({
          method: 'GET',
          url: imageUrlToUse,
          encoding: 'arraybuffer',
          returnFullResponse: true,
        });
        const b64 = Buffer.from(imgResp.body).toString('base64');
        messageContent.push({ type: 'image_url', image_url: { url: 'data:image/jpeg;base64,' + b64 } });
      } catch (imgErr) {
        // Image inaccessible (URL expiree, 403...) -> on continue sans, le prompt gere deja ce cas via son propre texte de contexte.
      }
    }
  }

  const resp = await this.helpers.httpRequest({
    method: 'POST',
    url: 'https://openrouter.ai/api/v1/chat/completions',
    headers: { 'Authorization': 'Bearer <OPENROUTER_API_KEY>', 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: 'anthropic/claude-opus-4', messages: [{ role: 'system', content: systemPrompt }, { role: 'user', content: messageContent }], temperature: 0.6, max_tokens: 280 }),
    json: true
  });
  aiOutput = (resp.choices[0].message.content || '').trim();
  if ((aiOutput.startsWith('"') && aiOutput.endsWith('"')) || (aiOutput.startsWith("'") && aiOutput.endsWith("'"))) aiOutput = aiOutput.slice(1, -1);
  aiOutput = aiOutput.replace(/—/g, '-').replace(/–/g, '-');
  if (aiOutput.trim().toUpperCase() === 'SKIP') aiOutput = '';
} catch(e) { aiOutput = ''; }

const icebreaker = aiOutput || '';
const skip = !icebreaker;

return [{ json: { accountId, providerId, prenom, headline, profileUrl, icebreaker, hasPosts, name, skip } }];
