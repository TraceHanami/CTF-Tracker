/* ─── CTF & Hackathon Tracker — Frontend JS ─────────────── */

const API = '';   // same-origin

// State
let allEvents = [];
let filters = {
  search:   '',
  mode:     'all',
  source:   'all',
  type:     'all',
  urgency:  'all',
  new_only: false,
};

// ─── Init ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initChips();
  initSearch();
  initStatCards();
  loadEvents();

  document.getElementById('btnRefresh').addEventListener('click', () => {
    loadEvents(true);
  });

  document.getElementById('btnExport').addEventListener('click', exportJSON);
});

// ─── Chip filters ───────────────────────────────────────
function initChips() {
  document.querySelectorAll('.chip-group').forEach(group => {
    const id = group.id;
    group.querySelectorAll('.chip').forEach(chip => {
      chip.addEventListener('click', () => {
        group.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        const val = chip.dataset.val;
        if (id === 'modeChips')    filters.mode    = val;
        if (id === 'sourceChips')  filters.source  = val;
        if (id === 'typeChips')    filters.type    = val;
        if (id === 'urgencyChips') filters.urgency = val;
        renderEvents();
      });
    });
  });
}

// ─── Search ─────────────────────────────────────────────
function initSearch() {
  const input = document.getElementById('searchInput');
  const clear = document.getElementById('searchClear');
  let timer;

  input.addEventListener('input', () => {
    clearTimeout(timer);
    filters.search = input.value.trim().toLowerCase();
    clear.classList.toggle('visible', filters.search.length > 0);
    timer = setTimeout(renderEvents, 200);
  });

  clear.addEventListener('click', () => {
    input.value = '';
    filters.search = '';
    clear.classList.remove('visible');
    renderEvents();
  });
}

// ─── Stat card clicks ───────────────────────────────────
function initStatCards() {
  document.querySelectorAll('.stat-card[data-filter]').forEach(card => {
    card.addEventListener('click', () => {
      const filterKey = card.dataset.filter;
      const val       = card.dataset.value;

      document.querySelectorAll('.stat-card').forEach(c => c.classList.remove('active'));
      card.classList.add('active');

      if (filterKey === 'mode')    { filters.mode = val; syncChip('modeChips', val); }
      if (filterKey === 'urgency') { filters.urgency = val; syncChip('urgencyChips', val); }
      if (filterKey === 'new_only') { filters.new_only = (val === 'true'); }

      renderEvents();
    });
  });
}

function syncChip(groupId, val) {
  const group = document.getElementById(groupId);
  if (!group) return;
  group.querySelectorAll('.chip').forEach(c => {
    c.classList.toggle('active', c.dataset.val === val);
  });
}

// ─── Load events from API ───────────────────────────────
async function loadEvents(forceRefresh = false) {
  showLoading(true);
  try {
    const qs = forceRefresh ? '?refresh=true' : '';
    const res = await fetch(`${API}/api/events${qs}`);
    const data = await res.json();
    if (!data.success) throw new Error(data.error || 'Unknown error');

    allEvents = data.events || [];
    await loadStats();
    renderEvents();
    if (forceRefresh) toast(`✓ Refreshed — ${allEvents.length} events loaded`);
  } catch (err) {
    showError('Failed to load events: ' + err.message);
  } finally {
    showLoading(false);
  }

  const btn = document.getElementById('btnRefresh');
  btn.classList.remove('spinning');
}

async function loadStats() {
  try {
    const res = await fetch(`${API}/api/stats`);
    const d = await res.json();
    if (!d.success) return;
    setText('statTotal',   d.total_events);
    setText('statWeek',    d.this_week);
    setText('statOnline',  d.online_count);
    setText('statOffline', d.offline_count);
    setText('statNew',     d.new_events);
  } catch (_) {}
}

// ─── Client-side filtering ──────────────────────────────
function applyFilters(events) {
  return events.filter(e => {
    if (filters.mode === 'online'  && !e.online)  return false;
    if (filters.mode === 'offline' &&  e.online)  return false;

    if (filters.source !== 'all') {
      if (e.source.toLowerCase() !== filters.source) return false;
    }
    if (filters.type !== 'all') {
      if (!e.type.toLowerCase().includes(filters.type)) return false;
    }
    if (filters.urgency !== 'all') {
      if (e.urgency !== filters.urgency) return false;
    }
    if (filters.search) {
      const hay = [e.title, e.description, e.source, e.location, e.type].join(' ').toLowerCase();
      if (!hay.includes(filters.search)) return false;
    }
    return true;
  });
}

// ─── Render ─────────────────────────────────────────────
function renderEvents() {
  const grid      = document.getElementById('eventsGrid');
  const emptyState = document.getElementById('emptyState');
  const meta       = document.getElementById('resultsMeta');

  const filtered = applyFilters(allEvents);

  meta.textContent = `Showing ${filtered.length} of ${allEvents.length} events`;

  if (filtered.length === 0) {
    grid.innerHTML = '';
    emptyState.style.display = 'block';
    return;
  }
  emptyState.style.display = 'none';

  grid.innerHTML = filtered.map((e, i) => buildCard(e, i)).join('');

  // Staggered animation delays
  grid.querySelectorAll('.event-card').forEach((card, i) => {
    card.style.animationDelay = `${Math.min(i * 40, 400)}ms`;
  });
}

function buildCard(e, i) {
  const srcKey = e.source.toLowerCase().replace(/[^a-z]/g, '');
  const modeBadge = e.online
    ? `<span class="badge badge-online">🌐 Online</span>`
    : `<span class="badge badge-offline">📍 ${e.location || 'Offline'}</span>`;

  const urgencyBadge = e.urgency === 'today'
    ? `<span class="badge badge-today">TODAY</span>`
    : e.urgency === 'this_week'
    ? `<span class="badge badge-week">This Week</span>`
    : '';

  const newBadge = e.is_new ? `<span class="badge badge-new">★ NEW</span>` : '';

  const daysText = formatDays(e.days_until);
  const daysClass = e.days_until <= 3 ? 'very-soon' : e.days_until <= 7 ? 'soon' : '';

  const desc = e.description
    ? `<div class="meta-row"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg><span>${truncate(e.description, 80)}</span></div>` : '';

  const teamSize = e.team_size && e.team_size !== '—'
    ? `<div class="meta-row">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        <strong>${e.team_size}</strong>
      </div>` : '';

  const participants = e.participants
    ? `<div class="meta-row">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10 15 15 0 0 1-4-10 15 15 0 0 1 4-10z"/></svg>
        <strong>${e.participants.toLocaleString()}</strong> registered
      </div>` : '';

  return `
  <article class="event-card" data-source="${srcKey}" onclick="openModal(${i})" data-idx="${i}">
    <div class="card-top">
      <div class="card-title">${escHtml(e.title)}</div>
      <div class="card-badges">
        <span class="badge badge-source" data-s="${srcKey}">${e.source}</span>
        ${modeBadge}
        ${newBadge}
        ${urgencyBadge}
      </div>
    </div>

    <div class="card-meta">
      <div class="meta-row">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        <strong>${formatDate(e.date)}</strong>
        ${e.end_date && e.end_date !== 'TBD' ? ` <span style="color:var(--muted)">→ ${formatDate(e.end_date)}</span>` : ''}
      </div>
      <div class="meta-row">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
        <span>${escHtml(e.location || (e.online ? 'Online' : 'TBD'))}</span>
      </div>
      ${teamSize}
      ${participants}
      ${desc}
    </div>

    <div class="card-tags">
      <span class="tag">${escHtml(e.type || 'Event')}</span>
      <span class="tag">Free</span>
      ${e.format && e.format !== e.type ? `<span class="tag">${escHtml(e.format)}</span>` : ''}
      ${e.weight ? `<span class="tag">⚖ ${e.weight.toFixed(1)}</span>` : ''}
    </div>

    <div class="card-footer">
      <a class="card-link" href="${e.url}" target="_blank" rel="noopener" onclick="event.stopPropagation()">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
        Register
      </a>
      <span class="days-pill ${daysClass}">${daysText}</span>
    </div>
  </article>`;
}

// ─── Modal ──────────────────────────────────────────────
const filteredCache = [];

function openModal(idx) {
  const filtered = applyFilters(allEvents);
  const e = filtered[idx] || allEvents[idx];
  if (!e) return;

  const srcKey = e.source.toLowerCase().replace(/[^a-z]/g, '');

  document.getElementById('modalBody').innerHTML = `
    <div class="card-badges" style="margin-bottom:14px; flex-wrap:wrap; display:flex; gap:6px;">
      <span class="badge badge-source" data-s="${srcKey}">${e.source}</span>
      ${e.online ? `<span class="badge badge-online">🌐 Online</span>` : `<span class="badge badge-offline">📍 Offline</span>`}
      ${e.is_new ? `<span class="badge badge-new">★ NEW</span>` : ''}
    </div>
    <div class="modal-title">${escHtml(e.title)}</div>

    <div class="modal-grid">
      <div class="modal-field">
        <div class="modal-field-label">Start Date</div>
        <div class="modal-field-value">${formatDate(e.date)}</div>
      </div>
      <div class="modal-field">
        <div class="modal-field-label">End Date</div>
        <div class="modal-field-value">${e.end_date && e.end_date !== 'TBD' ? formatDate(e.end_date) : '—'}</div>
      </div>
      <div class="modal-field">
        <div class="modal-field-label">Location</div>
        <div class="modal-field-value">${escHtml(e.location || (e.online ? 'Online' : 'TBD'))}</div>
      </div>
      <div class="modal-field">
        <div class="modal-field-label">Mode</div>
        <div class="modal-field-value">${e.online ? '🌐 Online' : '📍 In-Person'}</div>
      </div>
      <div class="modal-field">
        <div class="modal-field-label">Type</div>
        <div class="modal-field-value">${escHtml(e.type || '—')}</div>
      </div>
      <div class="modal-field">
        <div class="modal-field-label">Cost</div>
        <div class="modal-field-value" style="color:var(--green)">✓ Free</div>
      </div>
      <div class="modal-field">
        <div class="modal-field-label">Team Size</div>
        <div class="modal-field-value">${escHtml(e.team_size || '—')}</div>
      </div>
      <div class="modal-field">
        <div class="modal-field-label">Registered</div>
        <div class="modal-field-value">${e.participants ? e.participants.toLocaleString() : '—'}</div>
      </div>
    </div>

    ${e.description ? `<div class="modal-desc">${escHtml(e.description)}</div>` : ''}

    <div class="modal-actions">
      <a class="modal-btn primary" href="${e.url}" target="_blank" rel="noopener">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
        Register / View Event
      </a>
      <button class="modal-btn" onclick="copyLink('${e.url}')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        Copy Link
      </button>
    </div>
  `;
  document.getElementById('modalOverlay').classList.add('open');
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});

// ─── Helpers ────────────────────────────────────────────
function formatDate(d) {
  if (!d || d === 'TBD') return 'TBD';
  try {
    const dt = new Date(d + 'T00:00:00Z');
    return dt.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
  } catch (_) { return d; }
}

function formatDays(n) {
  if (n === undefined || n === null || n >= 999) return '';
  if (n < 0)  return 'Past';
  if (n === 0) return 'Today!';
  if (n === 1) return 'Tomorrow';
  return `${n}d left`;
}

function truncate(s, n) {
  if (!s) return '';
  return s.length <= n ? s : s.slice(0, n) + '…';
}

function escHtml(s) {
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function showLoading(on) {
  document.getElementById('loadingScreen').style.display = on ? 'flex' : 'none';
  if (on) {
    document.getElementById('eventsGrid').innerHTML = '';
    document.getElementById('emptyState').style.display = 'none';
  }
  if (on) {
    document.getElementById('btnRefresh').classList.add('spinning');
  }
}

function showError(msg) {
  const banner = document.getElementById('errorBanner');
  document.getElementById('errorMsg').textContent = msg;
  banner.style.display = 'flex';
}

function toast(msg, duration = 3000) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), duration);
}

function copyLink(url) {
  navigator.clipboard.writeText(url).then(() => {
    toast('✓ Link copied!');
  }).catch(() => {
    toast('⚠ Could not copy — try manually');
  });
}

function exportJSON() {
  window.location.href = `${API}/api/export/json`;
}

function resetFilters() {
  filters = { search: '', mode: 'all', source: 'all', type: 'all', urgency: 'all', new_only: false };
  document.getElementById('searchInput').value = '';
  document.getElementById('searchClear').classList.remove('visible');
  document.querySelectorAll('.chip-group .chip').forEach(c => {
    c.classList.toggle('active', c.dataset.val === 'all');
  });
  renderEvents();
}
