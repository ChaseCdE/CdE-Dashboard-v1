// Site shell: skip link, header (logo, title, nav), footer (sources, Círculo link, data date).
// Usage in a page:  <script type="module"> import { mountLayout } from './assets/js/layout.js';
//                   mountLayout({ active: 'portada' }); </script>
import { SITE_ROOT, IMG_ROOT } from './config.js';
import { loadManifest } from './data.js';
import { fmtDateLong } from './format.js';

export const NAV = [
  { id: 'portada', label: 'Portada', path: 'index.html' },
  { id: 'actividad', label: 'Actividad', path: 'pages/actividad.html' },
  { id: 'precios', label: 'Precios', path: 'pages/precios.html' },
  { id: 'laboral', label: 'Mercado laboral', path: 'pages/laboral.html' },
  { id: 'credito', label: 'Crédito y tipos', path: 'pages/credito.html' },
  { id: 'mercados', label: 'Mercados', path: 'pages/mercados.html' },
  { id: 'ue', label: 'Comparativa UE', path: 'pages/ue.html' },
  { id: 'consumo', label: 'Consumo', path: 'pages/consumo.html' },
];

const SOURCES = [
  { name: 'INE', url: 'https://www.ine.es' },
  { name: 'Eurostat', url: 'https://ec.europa.eu/eurostat' },
  { name: 'Banco de España', url: 'https://www.bde.es' },
  { name: 'Yahoo Finance', url: 'https://finance.yahoo.com' },
];

const CIRCULO_URL = 'https://circulodeempresarios.org';

function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') el.className = v; else if (k === 'text') el.textContent = v; else el.setAttribute(k, v === true ? '' : v);
  }
  for (const c of kids.flat()) if (c !== null && c !== undefined) el.append(c.nodeType ? c : document.createTextNode(String(c)));
  return el;
}

function buildHeader(active) {
  const navId = 'site-nav';
  const toggle = h('button', { class: 'nav-toggle', type: 'button', 'aria-expanded': 'false', 'aria-controls': navId },
    h('span', { class: 'nav-toggle-bars', 'aria-hidden': 'true' }), h('span', { class: 'sr-only', text: 'Menú' }));
  const list = h('ul', { class: 'nav-list' }, NAV.map((n) => h('li', {},
    h('a', { href: SITE_ROOT + n.path, class: 'nav-link', 'aria-current': n.id === active ? 'page' : null, text: n.label }))));
  const nav = h('nav', { id: navId, class: 'site-nav', 'aria-label': 'Secciones' }, list);
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') === 'true';
    toggle.setAttribute('aria-expanded', String(!open));
    nav.classList.toggle('is-open', !open);
  });
  nav.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && nav.classList.contains('is-open')) { toggle.click(); toggle.focus(); }
  });
  return h('div', { class: 'header-inner' },
    h('a', { class: 'brand', href: SITE_ROOT + 'index.html', 'aria-label': 'La economía en datos, portada' },
      h('img', { class: 'brand-logo', src: IMG_ROOT + 'logo-circulo.png', alt: 'Círculo de Empresarios', width: '489', height: '127' }),
      h('span', { class: 'brand-title', text: 'La economía en datos' })),
    toggle, nav);
}

function buildFooter() {
  const upd = h('span', { class: 'foot-updated', id: 'foot-updated' });
  return h('div', { class: 'footer-inner' },
    h('div', { class: 'footer-col' },
      h('p', { class: 'footer-head', text: 'Fuentes' }),
      h('p', {}, SOURCES.flatMap((s, i) => [i ? ', ' : null, h('a', { href: s.url, target: '_blank', rel: 'noopener noreferrer', text: s.name })])),
      h('p', { class: 'footer-small' }, 'Datos públicos procesados automáticamente. ', upd)),
    h('div', { class: 'footer-col' },
      h('p', { class: 'footer-head', text: 'Círculo de Empresarios' }),
      h('p', {}, h('a', { href: CIRCULO_URL, target: '_blank', rel: 'noopener noreferrer', text: 'circulodeempresarios.org' })),
      h('p', { class: 'footer-small', text: 'Think tank empresarial fundado en 1977.' })));
}

/** Mounts skip link, header and footer. Returns after the (non-blocking) data-date lookup is started. */
export function mountLayout({ active } = {}) {
  const main = document.querySelector('main');
  if (main && !main.id) main.id = 'contenido';
  if (!document.querySelector('.skip-link')) {
    document.body.prepend(h('a', { class: 'skip-link', href: '#' + (main ? main.id : 'contenido'), text: 'Saltar al contenido' }));
  }
  const header = document.getElementById('site-header') || document.querySelector('header.site-header');
  if (header) { header.className = 'site-header'; header.replaceChildren(buildHeader(active)); }
  const footer = document.getElementById('site-footer') || document.querySelector('footer.site-footer');
  if (footer) {
    footer.className = 'site-footer';
    footer.replaceChildren(buildFooter());
    loadManifest().then((m) => {
      const el = document.getElementById('foot-updated');
      if (el && m.generated_at) el.textContent = `Datos actualizados el ${fmtDateLong(m.generated_at)}.`;
    }).catch(() => { /* the page's own charts report the problem */ });
  }
}
