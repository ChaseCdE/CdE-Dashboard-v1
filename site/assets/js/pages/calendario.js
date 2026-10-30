// Calendario de publicaciones: lista por semanas con filtros (assets/js/calendar.js).
import { mountLayout } from '../layout.js';
import { calendarPage } from '../calendar.js';

mountLayout({ active: 'calendario' });
calendarPage(document.getElementById('calendar'));
