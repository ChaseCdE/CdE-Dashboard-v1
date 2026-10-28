// Comparativa UE: España frente a la UE-27 (Eurostat).
import { mountLayout } from '../layout.js';
import { kpiGrid, lineChart, barChart } from '../charts.js';

mountLayout({ active: 'ue' });
const $ = (id) => document.getElementById(id);
const ES = (ds, f) => ({ dataset: 'eurostat.' + ds, series: 'es', field: f });
const EU = (ds, f) => ({ dataset: 'eurostat.' + ds, series: 'eu27', field: f });
const pair = (ds, f) => [ES(ds, f), EU(ds, f)];

kpiGrid($('kpis'), [
  { dataset: 'eurostat.gdp_growth', series: 'es', field: 'qoq', title: 'PIB, variación trimestral, España', positiveIsGood: true },
  { dataset: 'eurostat.gdp_growth', series: 'eu27', field: 'qoq', title: 'PIB, variación trimestral, UE-27', positiveIsGood: true },
  { dataset: 'eurostat.unemployment', series: 'es', field: 'value', title: 'Tasa de paro, España', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'eurostat.unemployment', series: 'eu27', field: 'value', title: 'Tasa de paro, UE-27', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'eurostat.hicp', series: 'es', field: 'yoy', title: 'Inflación armonizada (IPCA), España', positiveIsGood: false },
  { dataset: 'eurostat.hicp', series: 'eu27', field: 'yoy', title: 'Inflación armonizada (IPCA), UE-27', positiveIsGood: false },
  { dataset: 'eurostat.government_debt', series: 'es', field: 'value', title: 'Deuda pública, % del PIB, España', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
  { dataset: 'eurostat.government_debt', series: 'eu27', field: 'value', title: 'Deuda pública, % del PIB, UE-27', change: { field: 'yoy_pp', label: 'interanual' }, positiveIsGood: false },
]);

// Convergencia con Europa
const peers = (ds, keys) => keys.map((k) => ({ dataset: 'eurostat.' + ds, series: k, field: 'value' }));
kpiGrid($('kpis-conv'), [
  { dataset: 'eurostat.gdp_per_capita_pps', series: 'es', field: 'value', title: 'PIB per cápita en PPA, España (UE-27 = 100)', positiveIsGood: true },
  { dataset: 'eurostat.labour_productivity_pps', series: 'es', field: 'value', title: 'Productividad por hora en PPA, España (UE-27 = 100)', positiveIsGood: true },
]);
lineChart($('conv-gdppc'), { title: 'PIB per cápita en paridad de poder adquisitivo', series: peers('gdp_per_capita_pps', ['es', 'de', 'fr', 'it', 'pt']), range: { default: 'max' }, ref: { y: 100, label: 'Media UE-27' } });
lineChart($('conv-prod'), { title: 'Productividad por hora trabajada en paridad de poder adquisitivo', series: peers('labour_productivity_pps', ['es', 'de', 'fr', 'it', 'pt']), range: { default: 'max' }, ref: { y: 100, label: 'Media UE-27' } });
lineChart($('conv-rd'), { title: 'Gasto en I+D sobre PIB, España y principales economías', series: peers('rd_expenditure', ['es', 'eu27', 'de', 'fr', 'it']), range: { default: 'max' } });

// Crecimiento
barChart($('gdp-growth'), { title: 'Crecimiento trimestral del PIB, España y UE-27', series: pair('gdp_growth', 'qoq'), range: { default: '5A' } });
lineChart($('gdp-index'), {
  title: 'PIB real: España, UE-27 y grandes economías',
  series: [ES('gdp_index', 'value'), EU('gdp_index', 'value'),
    { dataset: 'eurostat.gdp_index', series: 'de', field: 'value' },
    { dataset: 'eurostat.gdp_index', series: 'fr', field: 'value' },
    { dataset: 'eurostat.gdp_index', series: 'it', field: 'value' }],
  range: { default: '5A' },
});

// Mercado de trabajo
lineChart($('unemp'), { title: 'Tasa de paro, España y UE-27', series: pair('unemployment', 'value'), range: { default: '5A' } });
lineChart($('participation'), { title: 'Tasa de actividad, España y UE-27', series: pair('labor_participation', 'value'), range: { default: '5A' } });
lineChart($('emp-growth'), { title: 'Crecimiento trimestral del empleo, España y UE-27', series: pair('employment_growth', 'qoq'), range: { default: '5A' }, ref: { y: 0 } });
lineChart($('youth'), { title: 'Paro juvenil (menores de 25 años), España y UE-27', series: pair('youth_unemployment', 'value'), range: { default: '5A' } });
lineChart($('longterm'), { title: 'Paro de larga duración, España y UE-27', series: pair('long_term_unemployment', 'value'), range: { default: '5A' } });

// Precios
lineChart($('hicp'), { title: 'Inflación armonizada, España y UE-27', series: pair('hicp', 'yoy'), range: { default: '5A' }, ref: { y: 2, label: 'Objetivo BCE 2 %' } });
lineChart($('core'), { title: 'Inflación subyacente, España y UE-27', series: pair('core_inflation', 'yoy'), range: { default: '5A' }, ref: { y: 2, label: 'Objetivo BCE 2 %' } });
lineChart($('ppi'), { title: 'Precios industriales, variación interanual', series: pair('producer_prices', 'yoy'), range: { default: '5A' }, ref: { y: 0 } });

// Finanzas públicas
lineChart($('debt'), { title: 'Deuda pública sobre PIB, España y UE-27', series: pair('government_debt', 'value'), range: { default: 'max' } });
lineChart($('deficit'), { title: 'Déficit público sobre PIB, España y UE-27', series: pair('budget_deficit', 'value'), range: { default: 'max' }, markers: true, ref: { y: 0 } });

// Actividad y demanda
lineChart($('ipi'), { title: 'Producción industrial, variación interanual', series: pair('industrial_production', 'yoy'), range: { default: '5A' }, ref: { y: 0 } });
lineChart($('retail'), { title: 'Comercio minorista, variación interanual', series: pair('retail_trade', 'yoy'), range: { default: '5A' }, ref: { y: 0 } });
lineChart($('house'), { title: 'Precios de la vivienda, variación interanual', series: pair('house_prices', 'yoy'), range: { default: 'max' }, ref: { y: 0 } });

// Sentimiento
lineChart($('esi'), { title: 'Indicador de sentimiento económico, España y UE-27', series: pair('economic_sentiment', 'value'), range: { default: '5A' }, ref: { y: 100, label: 'Media de largo plazo' } });
lineChart($('conf'), { title: 'Confianza del consumidor, España y UE-27', series: pair('consumer_confidence', 'value'), range: { default: '5A' } });

// Comercio exterior (solo España)
barChart($('trade-bal'), { title: 'Saldo comercial de bienes, España', series: [ES('trade_balance', 'balance')], colorBySign: true, range: { default: '5A' } });
lineChart($('trade-flows'), { title: 'Exportaciones e importaciones de bienes, España', series: [ES('trade_balance', 'exports'), ES('trade_balance', 'imports')], range: { default: '5A' } });
