const invData = $('IF Has Invitations').first().json;
const staticData = $getWorkflowStaticData('global');

// Scrape Profile now calls Unipile GET /users/{id}?linkedin_sections=experience directly (flat object, not an array)
let profile = {};
try {
  const raw = $input.first().json.data;
  if (raw && typeof raw === 'string') profile = JSON.parse(raw);
  else profile = $input.first().json;
  if (!profile || typeof profile !== 'object') profile = {};
} catch(e) { profile = {}; }

const loc = profile.location || '';
const locationText = typeof loc === 'string' ? loc : '';
const countryCode = '';
const headline = profile.headline || invData.description || '';
const about = profile.summary || '';
const coverPictureUrl = profile.background_picture_url || profile.cover_picture_url || '';

const africaCodes = new Set(['DZ','AO','BJ','BW','BF','BI','CV','CM','CF','TD','KM','CG','CD','DJ','EG','GQ','ER','SZ','ET','GA','GM','GH','GN','GW','CI','KE','LS','LR','LY','MG','MW','ML','MR','MU','MA','MZ','NA','NE','NG','RW','ST','SN','SC','SL','SO','ZA','SS','SD','TZ','TG','TN','UG','ZM','ZW']);

// Duree reelle de l'activite principale, calculee depuis work_experience (jamais devinee par l'IA)
// Format precis en mois/annees, jamais arrondi.
let companyName = '';
let dureeReelle = '';
try {
  const exp = (profile.work_experience || [])
    .filter(w => w.start)
    .sort((a, b) => new Date(b.start) - new Date(a.start))[0];
  if (exp) {
    companyName = exp.company || '';
    const start = new Date(exp.start);
    const now = new Date();
    const totalMonths = (now.getFullYear() - start.getFullYear()) * 12 + (now.getMonth() - start.getMonth());
    if (totalMonths < 12) {
      dureeReelle = totalMonths + ' mois';
    } else {
      const years = Math.floor(totalMonths / 12);
      const remMonths = totalMonths % 12;
      if (remMonths === 0) dureeReelle = years + (years > 1 ? ' ans' : ' an');
      else dureeReelle = years + ' an' + (years > 1 ? 's' : '') + ' et ' + remMonths + ' mois';
    }
  }
} catch(e) {}

if (countryCode && africaCodes.has(countryCode)) {
  staticData.declinedCount = (staticData.declinedCount || 0) + 1;
  return [{ json: { ...invData, headline, about, locationText, countryCode, companyName, dureeReelle, coverPictureUrl, action: 'decline', reason: 'afrique' } }];
}

const bio = headline + (about ? '\n' + about : '');
let icpResult = 'non';

try {
  const prompt = 'Tu es un expert en qualification de leads LinkedIn B2B.\n\nReponds OUI uniquement si la bio montre CLAIREMENT une de ces activites :\n- Coach (business, vie, sport, sante, bien-etre, mindset, amour...)\n- Consultant, formateur, infopreneur\n- Freelance (copywriter, media buyer, closer, designer, dev, CM...)\n- Createur de contenu / influenceur avec une audience significative\n- Trader, investisseur, education financiere\n- Entrepreneur, fondateur, CEO, gerant d\'entreprise\n- Prestataire de service (agence, SaaS, marketing...)\n- Immobilier (agent, investisseur, formation)\n- E-commerce, dropshipping\n\nReponds OUI si la personne a un pouvoir de decision ou est independante :\n- Entrepreneur, fondateur, CEO, gerant, president, co-fondateur\n- Directeur, responsable, head of, manager, VP, C-level\n- Coach, consultant, formateur, infopreneur\n- Freelance (copywriter, media buyer, closer, designer, dev senior, CM...)\n- Createur de contenu, influenceur\n- Trader, investisseur, education financiere\n- Prestataire de service, agence, SaaS\n- Immobilier, e-commerce, dropshipping\n- Tout profil avec un titre de decision (responsable de X, directeur de X, head of X...)\n\nReponds NON si la personne est un simple salarie executant sans pouvoir de decision :\n- Community manager employe, assistant, stagiaire\n- Developpeur junior employe, simple employe\n- Particulier sans activite pro visible\n- Etudiant sans business\n- Artiste, musicien, sportif amateur\n- Compte de marque ou media\n\nEn cas de doute, si la bio suggere une activite entrepreneuriale ou un poste de decision, reponds OUI.\n\nIMPORTANT : Si la bio suggere une activite entrepreneuriale, de coaching, de business en ligne avec un focus probable sur une offre high ticket, reponds OUI.\n\nReponds UNIQUEMENT par OUI ou NON. Rien d\'autre.';
  const resp = await this.helpers.httpRequest({
    method: 'POST',
    url: 'https://openrouter.ai/api/v1/chat/completions',
    headers: { 'Authorization': 'Bearer <OPENROUTER_API_KEY>', 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: 'anthropic/claude-opus-4', messages: [{ role: 'system', content: prompt }, { role: 'user', content: 'Nom: ' + invData.name + '\nBio/Headline: ' + bio }], temperature: 0.1, max_tokens: 10 }),
    json: true
  });
  const answer = (resp.choices[0].message.content || '').trim().toUpperCase();
  icpResult = answer.includes('OUI') ? 'oui' : 'non';
} catch(e) {
  icpResult = 'non';
}

if (icpResult === 'non') {
  staticData.skippedCount = (staticData.skippedCount || 0) + 1;
  return [{ json: { ...invData, headline, about, locationText, countryCode, companyName, dureeReelle, coverPictureUrl, action: 'skip', reason: 'non ICP' } }];
}

staticData.acceptedCount = (staticData.acceptedCount || 0) + 1;
return [{ json: { ...invData, headline, about, locationText, countryCode, companyName, dureeReelle, coverPictureUrl, action: 'accept' } }];
