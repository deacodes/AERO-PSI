    const $ = (selector, root = document) => root.querySelector(selector);
    const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
    const state = { summary: null, investigations: [], ranking: null, rankSort: 'score', runFilter: 'all', runCardList: [], runs: {}, currentCoag: null, coagMarks: [], currentOptical: null, opticalMarks: [], copilotSources: [], pinnedPoints: { coagulation: new Set(), optical: new Set() } };
    const escapeHTML = (value = "") => String(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
    const formatNumber = value => Number.isFinite(Number(value)) ? new Intl.NumberFormat('en-US', { maximumSignificantDigits: 4 }).format(Number(value)) : '—';
    const scientific = (value, unit = '') => Number.isFinite(Number(value)) ? `${Number(value).toExponential(3)}${unit}` : '—';
    const jsonFetch = async (url, options) => { const response = await fetch(url, options); const body = await response.json().catch(() => ({})); if (!response.ok) throw new Error(body?.error?.message || `Request failed (${response.status})`); return body.data ?? body; };
