// Página Sectores: industria, servicios, construcción y vivienda, y turismo, cada uno en su sección.
// Each sector's charts live in their own module (element ids prefixed ind-, ser-, con-, tur-).
import { mountLayout } from '../layout.js';

mountLayout({ active: 'sectores' });
await Promise.all(['./industria.js', './servicios.js', './construccion.js', './turismo.js'].map((m) => import(m)));
