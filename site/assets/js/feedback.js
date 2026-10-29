// "¿Echas en falta algo?" suggestions box, shown above the footer on every page.
// No backend: it prepares an e-mail (mailto:) with the suggestion, its type and the page,
// which the visitor sends from their own mail program. Nothing is stored or sent by the site.
import { FEEDBACK_EMAIL } from './config.js';

const TYPES = [
  { id: 'dato', label: 'Echo en falta un dato' },
  { id: 'grafico', label: 'Un gráfico mejorable' },
  { id: 'error', label: 'Un dato que no cuadra' },
  { id: 'otra', label: 'Otra idea' },
];
const MAX_CHARS = 1500; // keeps the mailto: link within what mail programs accept

function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === 'text') el.textContent = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const k of kids.flat()) if (k != null) el.append(k);
  return el;
}

function pageName() {
  const h1 = document.querySelector('main h1');
  return (h1 && h1.textContent.trim()) || document.title;
}

export function buildFeedback() {
  if (!FEEDBACK_EMAIL) return null;
  const status = h('p', { class: 'fb-status', role: 'status', 'aria-live': 'polite' });
  const text = h('textarea', {
    id: 'fb-text', name: 'sugerencia', rows: '4', maxlength: String(MAX_CHARS), required: true,
    placeholder: 'Por ejemplo: me gustaría ver el precio de la vivienda por comunidades autónomas.',
  });
  const chips = h('div', { class: 'fb-chips' }, TYPES.map((t, i) => h('label', { class: 'fb-chip' },
    h('input', { type: 'radio', name: 'tipo', value: t.label, checked: i === 0 }),
    h('span', { text: t.label }))));
  const copyBtn = h('button', {
    type: 'button', class: 'fb-copy', text: 'Copiar dirección',
    onclick: async () => {
      try { await navigator.clipboard.writeText(FEEDBACK_EMAIL); copyBtn.textContent = 'Dirección copiada'; }
      catch { copyBtn.textContent = FEEDBACK_EMAIL; }
    },
  });

  const form = h('form', {
    class: 'fb-form', novalidate: true,
    onsubmit: (e) => {
      e.preventDefault();
      const msg = text.value.trim();
      if (msg.length < 5) {
        status.className = 'fb-status is-error';
        status.textContent = 'Escribe tu sugerencia antes de preparar el correo.';
        text.focus();
        return;
      }
      const tipo = form.querySelector('input[name="tipo"]:checked')?.value || TYPES[0].label;
      const subject = `Sugerencia: ${tipo} · La economía en datos`;
      const body = `${msg}\n\n---\nTipo: ${tipo}\nPágina: ${pageName()} (${location.href})`;
      window.location.href = `mailto:${FEEDBACK_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      status.className = 'fb-status is-ok';
      status.textContent = 'Si se ha abierto tu programa de correo, solo falta enviar el mensaje. ¡Gracias!';
    },
  },
    h('fieldset', { class: 'fb-fieldset' }, h('legend', { text: '¿Sobre qué es?' }), chips),
    h('div', { class: 'fb-field' }, h('label', { class: 'fb-label', for: 'fb-text', text: 'Tu sugerencia' }), text),
    h('div', { class: 'fb-actions' },
      h('button', { type: 'submit', class: 'fb-submit', text: 'Preparar correo' }),
      h('p', { class: 'fb-note' },
        'Se abrirá tu programa de correo con el mensaje y la página actual ya incluidos. La web no guarda nada. ',
        '¿No se abre? Escríbenos a ', h('a', { href: `mailto:${FEEDBACK_EMAIL}`, text: FEEDBACK_EMAIL }), ' ', copyBtn)),
    status);

  return h('section', { class: 'feedback', 'aria-labelledby': 'fb-title' },
    h('div', { class: 'feedback-inner' },
      h('div', { class: 'fb-intro' },
        h('h2', { id: 'fb-title', class: 'fb-title', text: '¿Echas en falta algo?' }),
        h('p', { text: 'Cuéntanos qué indicador añadirías, qué gráfico se entendería mejor o si has visto algún dato que no cuadra. Leemos todas las sugerencias.' })),
      form));
}
