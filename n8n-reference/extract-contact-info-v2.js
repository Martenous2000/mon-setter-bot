let body = $input.first().json.body || $input.first().json;
// Handle form-encoded body (Unipile sends as x-www-form-urlencoded)
if (body && typeof body === 'object') {
  const bodyKeys = Object.keys(body);
  const jsonKey = bodyKeys.find(k => k.startsWith('{'));
  if (jsonKey) {
    const raw = Object.entries(body).map(([k, v]) => k + '=' + v).join('&');
    try {
      body = JSON.parse(raw);
    } catch (e) {
      const extract = (field) => {
        const re = new RegExp('"' + field + '":"([^"]*)"');
        const m = raw.match(re);
        return m ? m[1] : '';
      };
      body = {
        account_id: extract('account_id'),
        user_provider_id: extract('user_provider_id'),
        user_full_name: extract('user_full_name'),
        user_public_identifier: extract('user_public_identifier'),
        user_profile_url: extract('user_profile_url'),
      };
    }
  }
}
const data = body.data || body.object || body;
let accountId = body.account_id || data.account_id || '';
const providerId = String(data.user_provider_id || data.provider_id || data.id || '');
let name = data.user_full_name || data.name || data.display_name || '';
const publicId = data.user_public_identifier || data.public_identifier || '';
let profileUrl = data.user_profile_url || data.public_profile_url || data.profile_url || '';
if (!profileUrl && publicId) profileUrl = 'https://www.linkedin.com/in/' + publicId;
if (!profileUrl && providerId) profileUrl = 'https://www.linkedin.com/in/' + providerId;
let prenom = '';
if (name) prenom = name.split(/\s+/)[0] || '';
if (prenom) prenom = prenom.charAt(0).toUpperCase() + prenom.slice(1).toLowerCase();
if (!accountId) {
  try {
    const resp = await this.helpers.httpRequest({ method: 'GET', url: 'https://api34.unipile.com:16428/api/v1/accounts', headers: { 'X-API-KEY': '<UNIPILE_API_KEY>', 'accept': 'application/json' }, json: true });
    const items = resp.items || resp || [];
    const lkd = Array.isArray(items) ? items.find(a => a.type === 'LINKEDIN') : null;
    if (lkd) accountId = lkd.id;
  } catch(e) {}
}
let headline = '';
let companyName = '';
let dureeReelle = '';
let coverPictureUrl = '';
try {
  const userResp = await this.helpers.httpRequest({ method: 'GET', url: 'https://api34.unipile.com:16428/api/v1/users/' + encodeURIComponent(providerId) + '?account_id=' + accountId + '&linkedin_sections=experience', headers: { 'X-API-KEY': '<UNIPILE_API_KEY>', 'accept': 'application/json' }, json: true });
  headline = userResp.headline || userResp.title || userResp.position || '';
  if (!name && userResp.name) name = userResp.name;
  if (!prenom && name) { prenom = name.split(/\s+/)[0] || ''; if (prenom) prenom = prenom.charAt(0).toUpperCase() + prenom.slice(1).toLowerCase(); }
  coverPictureUrl = userResp.background_picture_url || userResp.cover_picture_url || '';
  // Duree reelle de l'activite principale, calculee depuis work_experience (jamais devinee par l'IA)
  // Format precis en mois/annees, jamais arrondi ("1 an et 10 mois", pas "plus de 1 an").
  const exp = (userResp.work_experience || [])
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
if (!accountId || !providerId) throw new Error('Donnees webhook incompletes: accountId=' + accountId + ', providerId=' + providerId);
return [{ json: { accountId, providerId, name, prenom, headline, profileUrl, companyName, dureeReelle, coverPictureUrl } }];
