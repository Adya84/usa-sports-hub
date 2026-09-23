const SPORTS = {
  nfl: { label: 'NFL', icon: '🏈', background: 'background-nfl.png', accent: '#c8102e', detail: 'Quarter · Clock · Possession · Down & distance' },
  nba: { label: 'NBA', icon: '🏀', background: 'background-nba.png', accent: '#d8232a', detail: 'Quarter · Clock · Leaders · Box score' },
  mlb: { label: 'MLB', icon: '⚾', background: '', accent: '#d71920', detail: 'Inning · Count · Bases · Pitch-by-pitch' },
  nhl: { label: 'NHL', icon: '🏒', background: '', accent: '#1565c0', detail: 'Period · Shots · Power play · Game centre' },
  mls: { label: 'MLS', icon: '⚽', background: '', accent: '#d71920', detail: 'Fixtures · Scores · Standings · Teams' },
  more: { label: 'More Sports', icon: '⭐', background: '', accent: '#1565c0', detail: 'WNBA · NCAA · F1 · UFC coming soon' },
};

const TABS = ['Overview', 'Live', 'Fixtures', 'Results', 'Standings', 'Teams', 'Players', 'News', 'My Team'];

class UsaSportsHubPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.sport = localStorage.getItem('usa_sports_hub_selected_sport') || 'nfl';
    this.tab = localStorage.getItem(`usa_sports_hub_${this.sport}_tab`) || 'Overview';
  }

  set hass(value) { this._hass = value; this.render(); }
  connectedCallback() { this.render(); }

  selectSport(sport) {
    this.sport = sport;
    this.tab = localStorage.getItem(`usa_sports_hub_${sport}_tab`) || 'Overview';
    localStorage.setItem('usa_sports_hub_selected_sport', sport);
    this.render();
  }

  selectTab(tab) {
    this.tab = tab;
    localStorage.setItem(`usa_sports_hub_${this.sport}_tab`, tab);
    this.render();
  }

  render() {
    const sport = SPORTS[this.sport] || SPORTS.nfl;
    const sportBackground = sport.background ? `url('/usa_sports_hub/${sport.background}')` : `radial-gradient(circle at 84% 16%, ${sport.accent}66, transparent 28%), linear-gradient(135deg,#06142a,#102d55)`;
    const sportButtons = Object.entries(SPORTS).map(([id, item]) => `<button class="sport ${id === this.sport ? 'selected' : ''}" data-sport="${id}"><span>${item.icon}</span>${item.label}</button>`).join('');
    const tabButtons = TABS.map((tab) => `<button class="tab ${tab === this.tab ? 'selected' : ''}" data-tab="${tab}">${tab}</button>`).join('');
    const donation = `<section class="donation" style="--donation-image:url('/usa_sports_hub/${sport.background}')"><span class="donation-icon">${sport.icon}</span><div><small>SUPPORT ${sport.label}</small><h3>Keep USA Sports Hub in play</h3><p>Help support new ${sport.label} data, features, and live game coverage.</p></div><div class="donation-actions"><a href="https://ko-fi.com/ady1984" target="_blank" rel="noopener noreferrer">Support via Ko-fi</a><a href="https://paypal.me/graffidoodle" target="_blank" rel="noopener noreferrer">PayPal</a></div></section>`;
    const page = this.tab === 'Overview' ? `
      <section class="hero-card"><p>USA SPORTS HUB · ${sport.label}</p><h2>${sport.label} Central</h2><span>${sport.detail}</span><div class="hero-stats"><b>LIVE DATA</b><b>FIXTURES</b><b>STANDINGS</b><b>NEWS</b></div></section>
      <section class="grid"><article><small>LIVE CENTRE</small><h3>Game-day information</h3><p>Live scores and detailed match events will appear here.</p></article><article><small>UP NEXT</small><h3>Schedules & fixtures</h3><p>Upcoming games, results and team form.</p></article><article><small>LEAGUE TABLE</small><h3>Standings</h3><p>Conference and division views for ${sport.label}.</p></article></section>${donation}` : `
      <section class="page"><p>${sport.label} · ${this.tab.toUpperCase()}</p><h2>${this.tab}</h2><span>${sport.detail}</span><div class="placeholder">${this.tab} data for ${sport.label} will load here from its dedicated provider.</div></section>`;
    this.shadowRoot.innerHTML = `<style>
      :host{display:block;color:#f7f9ff;font-family:Inter,system-ui,sans-serif}.shell{min-height:100vh;background:linear-gradient(180deg,#020812c9,#020812ed),${sportBackground} center/cover fixed;padding-bottom:32px}.header{display:flex;align-items:center;gap:16px;padding:22px clamp(18px,4vw,60px);background:#061327e6;border-bottom:1px solid #ffffff1f}.badge{width:64px;height:64px;object-fit:contain;border-radius:12px}.title h1{font-size:1.45rem;margin:0}.title span{color:#aab9d3;font-size:.86rem}.sports,.tabs{display:flex;gap:9px;overflow:auto;padding:14px clamp(18px,4vw,60px);background:#07162be8}.sport,.tab{white-space:nowrap;border:1px solid #ffffff29;background:#ffffff0d;color:#fff;border-radius:999px;padding:10px 15px;font-weight:800;cursor:pointer}.sport.selected,.tab.selected{background:${sport.accent};border-color:#fff}.sport span{margin-right:7px}.tabs{padding-top:0;background:#07162bbd;border-bottom:1px solid #ffffff1a}.content{max-width:1180px;margin:auto;padding:28px 18px}.hero-card,.page,article{background:#07172adb;border:1px solid #ffffff24;border-radius:20px;padding:28px;box-shadow:0 18px 50px #0007}.hero-card p,.page p,article small{color:#9bb6df;letter-spacing:.12em;font-weight:800}.hero-card h2,.page h2{font-size:clamp(2rem,5vw,4rem);margin:8px 0}.hero-stats{display:flex;flex-wrap:wrap;gap:12px;margin-top:28px}.hero-stats b{background:#ffffff16;padding:10px 13px;border-radius:10px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:16px}.grid h3{margin:8px 0}.grid p{color:#cbd6e9;line-height:1.5}.donation{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:18px;margin-top:16px;padding:24px;border:1px solid #ffffff38;border-radius:20px;background:linear-gradient(90deg,#06142af2,#06142abb),var(--donation-image) center/cover;color:#fff}.donation-icon{font-size:3rem}.donation small{font-weight:900;letter-spacing:.1em;color:#9fc7ff}.donation h3{margin:4px 0}.donation p{margin:0;color:#d7e4f8}.donation-actions{display:flex;gap:8px}.donation a{padding:10px 12px;border-radius:10px;background:#d71920;color:#fff;text-decoration:none;font-weight:800;white-space:nowrap}.placeholder{margin-top:28px;padding:36px;border:1px dashed #ffffff47;border-radius:14px;color:#cbd6e9;background:#02091594}@media(max-width:700px){.grid{grid-template-columns:1fr}.header{padding:16px}.badge{width:52px;height:52px}.content{padding:18px 12px}.donation{grid-template-columns:1fr}.donation-actions{flex-wrap:wrap}}
    </style><div class="shell"><header class="header"><img class="badge" src="/usa_sports_hub/icon.png" alt="USA Sports Hub"><div class="title"><h1>USA Sports Hub</h1><span>All your American sports in one place</span></div></header><nav class="sports" aria-label="Sports">${sportButtons}</nav><nav class="tabs" aria-label="${sport.label} sections">${tabButtons}</nav><main class="content">${page}</main></div>`;
    this.shadowRoot.querySelectorAll('[data-sport]').forEach((button) => button.addEventListener('click', () => this.selectSport(button.dataset.sport)));
    this.shadowRoot.querySelectorAll('[data-tab]').forEach((button) => button.addEventListener('click', () => this.selectTab(button.dataset.tab)));
  }
}

customElements.define('usa-sports-hub-panel', UsaSportsHubPanel);
