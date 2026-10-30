// Site shell: skip link, header (logo, title, nav), suggestions box, footer (sources, Círculo link, data date).
// Usage in a page:  <script type="module"> import { mountLayout } from './assets/js/layout.js';
//                   mountLayout({ active: 'portada' }); </script>
import { SITE_ROOT, IMG_ROOT } from './config.js';
import { loadManifest } from './data.js';
import { fmtDateLong } from './format.js';
import { buildFeedback } from './feedback.js';

// `sections` are the h2 anchors of each page (tests/test_nav_anchors.py checks they exist).
const S = (...pairs) => pairs.map(([id, label]) => ({ id, label }));
// A section with sub-sections whose ids are `${id}-${sub id}`.
const G = (id, label, ...subs) => ({ id, label, sub: subs.map(([sid, l]) => ({ id: `${id}-${sid}`, label: l })) });
export const NAV = [
  { id: 'portada', label: 'Portada', path: 'index.html', sections: S(
    ['ultimos-datos', 'Últimos datos'], ['actividad-y-precios', 'Actividad y precios'], ['espana-frente-a-la-ue-27', 'España frente a la UE-27'],
    ['tipos-de-interes-y-mercados', 'Tipos de interés y mercados']) },
  { id: 'actividad', label: 'Actividad', path: 'pages/actividad.html', sections: S(
    ['pib-y-demanda', 'PIB y demanda'], ['coyuntura', 'Coyuntura'], ['clima-economico', 'Clima económico'],
    ['consumo-y-hogares', 'Consumo y hogares'], ['productividad-y-convergencia', 'Productividad y convergencia']) },
  // One page; each sector is an h2 section with its own sub-sections (h3, ids prefixed by the sector).
  { id: 'sectores', label: 'Sectores', path: 'pages/sectores.html', sections: [
    G('industria', 'Industria', ['produccion-industrial', 'Producción industrial'],
      ['destino-economico-y-divisiones', 'Destino económico y divisiones'],
      ['cifra-de-negocios-valor-anadido-y-capacidad', 'Cifra de negocios, valor añadido y capacidad']),
    G('servicios', 'Servicios', ['produccion', 'Producción'], ['cifra-de-negocios-y-valor-anadido', 'Cifra de negocios y valor añadido']),
    G('construccion-vivienda', 'Construcción y vivienda', ['actividad-constructora', 'Actividad constructora'],
      ['precios-de-la-vivienda', 'Precios de la vivienda'], ['compraventas-e-hipotecas', 'Compraventas e hipotecas']),
    G('turismo', 'Turismo', ['turistas-internacionales', 'Turistas internacionales'], ['alojamiento', 'Alojamiento'],
      ['balanza-de-pagos', 'Balanza de pagos']),
  ] },
  { id: 'empresas', label: 'Empresas', path: 'pages/empresas.html', sections: S(
    ['demografia-empresarial', 'Demografía empresarial'], ['ventas-y-costes', 'Ventas y costes'], ['clima-empresarial', 'Clima empresarial'],
    ['financiacion', 'Financiación de las empresas']) },
  { id: 'laboral', label: 'Mercado laboral', path: 'pages/laboral.html', sections: S(
    ['empleo', 'Empleo'], ['paro', 'Paro'], ['participacion-y-poblacion', 'Participación y población'], ['costes-laborales', 'Costes laborales']) },
  { id: 'precios', label: 'Precios', path: 'pages/precios.html', sections: S(
    ['inflacion-general-y-subyacente', 'Inflación general y subyacente'], ['composicion-del-ipc', 'Composición del IPC'],
    ['comunidades-autonomas', 'Comunidades autónomas'], ['precios-industriales', 'Precios industriales']) },
  { id: 'exterior', label: 'Sector exterior', path: 'pages/sector-exterior.html', sections: S(
    ['balanza-de-pagos', 'Balanza de pagos'], ['comercio-de-bienes', 'Comercio de bienes'],
    ['precios-del-comercio-exterior', 'Precios del comercio exterior']) },
  { id: 'publico', label: 'Sector público', path: 'pages/sector-publico.html', sections: S(
    ['deuda', 'Deuda'], ['deficit', 'Déficit'], ['coste-de-la-financiacion', 'Coste de la financiación']) },
  { id: 'credito', label: 'Crédito y tipos', path: 'pages/credito.html', sections: S(
    ['tipos-de-interes', 'Tipos de interés'], ['credito', 'Crédito'], ['endeudamiento-y-morosidad', 'Endeudamiento y morosidad']) },
  { id: 'mercados', label: 'Mercados', path: 'pages/mercados.html', sections: S(
    ['bolsas', 'Bolsas'], ['tipos-de-interes', 'Tipos de interés'], ['divisas', 'Divisas'], ['materias-primas', 'Materias primas']) },
  { id: 'ue', label: 'Comparativa UE', path: 'pages/ue.html', sections: S(
    ['situacion-actual', 'Situación actual'], ['convergencia-con-europa', 'Convergencia con Europa'], ['crecimiento', 'Crecimiento'],
    ['mercado-de-trabajo', 'Mercado de trabajo'], ['precios', 'Precios'], ['finanzas-publicas', 'Finanzas públicas'],
    ['actividad-y-demanda', 'Actividad y demanda'], ['sentimiento', 'Sentimiento'], ['comercio-exterior-de-espana', 'Comercio exterior de España']) },
];

const SOURCES = [
  { name: 'INE', url: 'https://www.ine.es' },
  { name: 'Eurostat', url: 'https://ec.europa.eu/eurostat' },
  { name: 'Banco de España', url: 'https://www.bde.es' },
  { name: 'Ministerio de Vivienda y Agenda Urbana', url: 'https://www.mivau.gob.es' },
  { name: 'Colegio de Registradores', url: 'https://www.registradores.org' },
  { name: 'Agencia Tributaria', url: 'https://sede.agenciatributaria.gob.es/Sede/estadisticas.html' },
  { name: 'Banco Central Europeo', url: 'https://data.ecb.europa.eu' },
  { name: 'Reserva Federal', url: 'https://www.federalreserve.gov' },
  { name: 'EIA', url: 'https://www.eia.gov' },
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
  const link = (n) => h('a', { href: SITE_ROOT + n.path, class: 'nav-link', 'aria-current': n.id === active ? 'page' : null, text: n.label });
  const secLink = (n, sec, cls) => h('a', { href: SITE_ROOT + n.path + '#' + sec.id, class: cls, text: sec.label });
  const secLinks = (n) => h('ul', { class: 'nav-secs' }, n.sections.map((sec) => h('li', {}, secLink(n, sec, 'nav-sec'))));
  // Sections with sub-sections (Sectores): one column per section, heading link plus its sub-sections.
  const megaLinks = (n) => h('div', { class: 'nav-mega' }, n.sections.map((sec) => h('div', { class: 'nav-mega-col' },
    secLink(n, sec, 'nav-sec nav-sec-head'), h('ul', { class: 'nav-secs' }, sec.sub.map((x) => h('li', {}, secLink(n, x, 'nav-sec')))))));
  const last = NAV.length - 1;
  // Page link; on desktop, hovering (or focusing inside) shows its sections as anchor links.
  const list = h('ul', { class: 'nav-list' }, NAV.map((n, i) => {
    const edge = i >= last - 2 ? ' nav-right' : '';
    const mega = (n.sections || []).some((sec) => sec.sub);
    return h('li', { class: 'nav-item' + edge }, link(n),
      n.sections && n.sections.length ? h('div', { class: 'nav-drop' + (mega ? ' nav-drop-mega' : '') }, mega ? megaLinks(n) : secLinks(n)) : null);
  }));
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
      h('img', { class: 'brand-logo', src: IMG_ROOT + 'logo-circulo-50.svg', alt: 'Círculo de Empresarios, 50 aniversario', width: '755', height: '206' }),
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

/**
 * Arriving at page.html#section: charts above the section render after the browser has jumped
 * there and push it down. Keep the section in view while the page grows, until the reader scrolls
 * or for a few seconds.
 */
function keepAnchorInView() {
  const id = decodeURIComponent(location.hash.slice(1));
  const target = id && document.getElementById(id);
  const main = document.querySelector('main');
  if (!target || !main || !('ResizeObserver' in window)) return;
  let done = false;
  const stop = () => { done = true; ro.disconnect(); };
  const ro = new ResizeObserver(() => { if (!done) target.scrollIntoView(); });
  ro.observe(main);
  for (const ev of ['wheel', 'touchstart', 'keydown', 'mousedown']) window.addEventListener(ev, stop, { once: true, passive: true });
  setTimeout(stop, 10000);
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
  keepAnchorInView();
  const footer = document.getElementById('site-footer') || document.querySelector('footer.site-footer');
  if (footer) {
    const fb = document.querySelector('section.feedback') ? null : buildFeedback();
    if (fb) footer.before(fb);
    footer.className = 'site-footer';
    footer.replaceChildren(buildFooter());
    loadManifest().then((m) => {
      const el = document.getElementById('foot-updated');
      if (el && m.generated_at) el.textContent = `Datos actualizados el ${fmtDateLong(m.generated_at)}.`;
    }).catch(() => { /* the page's own charts report the problem */ });
  }
}
