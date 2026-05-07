/* ============================================================
   AI-Powered LinkedIn Outreach Assistant — Script
   ============================================================ */

// ---- Configuration ----
const API_BASE = 'http://localhost:8000';
const ENDPOINTS = {
  find: `${API_BASE}/find`,
  regenerate: `${API_BASE}/regenerate`,
};

// ---- Mock Data ----
const MOCK_DATA = [
  {
    name: "Rahul Sharma",
    headline: "Senior Technical Recruiter at Infosys",
    company: "Infosys",
    focus: "backend",
    message: "Hi Rahul, I noticed you hire backend engineers at Infosys. I have strong C++ and Node.js experience and would love to connect about opportunities.",
    url: "https://linkedin.com/in/example",
    source: "mock"
  },
  {
    name: "Priya Nair",
    headline: "Campus Recruiter | Hiring Interns | Bangalore",
    company: "Wipro",
    focus: "internship",
    message: "Hi Priya, I saw you're hiring interns at Wipro. I'm a CS student with React and DSA skills and would love to connect.",
    url: "https://linkedin.com/in/example2",
    source: "mock"
  },
  {
    name: "Ankit Verma",
    headline: "Frontend Engineering Recruiter at Flipkart",
    company: "Flipkart",
    focus: "frontend",
    message: "Hi Ankit, I came across your profile and saw you recruit frontend engineers at Flipkart. I specialize in React, TypeScript, and UI/UX and would love to explore opportunities.",
    url: "https://linkedin.com/in/example3",
    source: "mock"
  },
  {
    name: "Megha Reddy",
    headline: "Tech Talent Partner — Full Stack Roles | TCS",
    company: "TCS",
    focus: "fullstack",
    message: "Hi Megha, I noticed you're hiring full-stack developers at TCS. With experience in Node.js, React, and PostgreSQL, I'd love to discuss how I can contribute.",
    url: "https://linkedin.com/in/example4",
    source: "mock"
  },
  {
    name: "Siddharth Joshi",
    headline: "AI/ML Talent Acquisition Lead at Google DeepMind",
    company: "Google DeepMind",
    focus: "ai_ml",
    message: "Hi Siddharth, I'm excited to see you lead AI/ML hiring at Google DeepMind. I have published research in NLP and hands-on PyTorch experience — would love to connect.",
    url: "https://linkedin.com/in/example5",
    source: "mock"
  }
];

// ---- DOM refs ----
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const searchForm = $('#searchForm');
const roleInput = $('#roleInput');
const locationInput = $('#locationInput');
const skillsInput = $('#skillsInput');
const searchBtn = $('#searchBtn');
const searchBtnText = $('#searchBtnText');
const searchSection = $('#searchSection');
const resultsSection = $('#resultsSection');
const resultsGrid = $('#resultsGrid');
const resultsCountNum = $('#resultsCountNum');
const filterSelect = $('#filterSelect');
const loadingSection = $('#loadingSection');
const skeletonGrid = $('#skeletonGrid');
const emptyState = $('#emptyState');
const emptyRetryBtn = $('#emptyRetryBtn');
const errorState = $('#errorState');
const errorMessage = $('#errorMessage');
const errorRetryBtn = $('#errorRetryBtn');
const demoToggle = $('#demoToggle');
const toastContainer = $('#toastContainer');

// ---- State ----
let currentResults = [];
let lastSearchParams = {};
let demoMode = false;

// ---- Helpers ----
function show(el) { el.style.display = ''; }
function hide(el) { el.style.display = 'none'; }

function getInitials(name) {
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

const FOCUS_MAP = {
  backend: { cls: 'badge--backend', label: 'Backend' },
  frontend: { cls: 'badge--frontend', label: 'Frontend' },
  fullstack: { cls: 'badge--fullstack', label: 'Full Stack' },
  internship: { cls: 'badge--internship', label: 'Internship' },
  ai_ml: { cls: 'badge--ai_ml', label: 'AI / ML' },
  general: { cls: 'badge--general', label: 'General' },
};

function focusInfo(key) {
  return FOCUS_MAP[key] || FOCUS_MAP.general;
}

// ---- Toast System ----
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.setAttribute('role', 'status');

  const icons = {
    success: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>`,
    error: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
    info: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
  };

  toast.innerHTML = `${icons[type] || icons.info}<span>${message}</span>`;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('toast--exit');
    toast.addEventListener('animationend', () => toast.remove());
  }, 3000);
}

// ---- Skeleton Rendering ----
function renderSkeletons(count = 6) {
  skeletonGrid.innerHTML = '';
  for (let i = 0; i < count; i++) {
    const el = document.createElement('div');
    el.className = 'skeleton-card';
    el.setAttribute('aria-hidden', 'true');
    el.innerHTML = `
      <div class="skeleton-row">
        <div class="skeleton-line skeleton-line--circle"></div>
        <div style="flex:1;display:flex;flex-direction:column;gap:6px">
          <div class="skeleton-line skeleton-line--md"></div>
          <div class="skeleton-line skeleton-line--sm"></div>
        </div>
      </div>
      <div class="skeleton-line skeleton-line--sm" style="width:50%"></div>
      <div class="skeleton-line skeleton-line--full"></div>
      <div class="skeleton-actions">
        <div class="skeleton-line skeleton-line--btn"></div>
        <div class="skeleton-line skeleton-line--btn"></div>
        <div class="skeleton-line skeleton-line--btn"></div>
      </div>
    `;
    skeletonGrid.appendChild(el);
  }
}

// ---- Card Rendering ----
function buildCardHTML(rec, index) {
  const fi = focusInfo(rec.focus);
  const initials = getInitials(rec.name);
  const delay = index * 80;

  return `
    <article class="card" role="listitem"
      data-focus="${rec.focus}"
      data-index="${index}"
      style="animation-delay:${delay}ms">
      <div class="card__header">
        <div class="card__identity">
          <div class="card__avatar">${initials}</div>
          <div class="card__name-group">
            <span class="card__name">${escapeHTML(rec.name)}</span>
            <span class="card__headline">${escapeHTML(rec.headline)}</span>
          </div>
        </div>
        <span class="badge ${fi.cls}">${fi.label}</span>
      </div>

      <div class="card__company">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="4" y="2" width="16" height="20" rx="2" ry="2" />
          <path d="M9 22v-4h6v4" />
          <path d="M8 6h.01" /><path d="M16 6h.01" />
          <path d="M8 10h.01" /><path d="M16 10h.01" />
          <path d="M8 14h.01" /><path d="M16 14h.01" />
        </svg>
        ${escapeHTML(rec.company)}
      </div>

      <div class="card__message-section">
        <span class="card__message-label">AI Message</span>
        <div class="card__message-box" id="msg-${index}">${escapeHTML(rec.message)}</div>
      </div>

      <div class="card__actions">
        <button class="btn-action btn-copy" data-index="${index}" aria-label="Copy message">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
          </svg>
          <span>Copy</span>
        </button>

        <a class="btn-action btn-profile" href="${escapeAttr(rec.url)}" target="_blank"
          rel="noopener noreferrer" aria-label="Open LinkedIn profile of ${escapeAttr(rec.name)}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
            <polyline points="15 3 21 3 21 9" />
            <line x1="10" y1="14" x2="21" y2="3" />
          </svg>
          <span>Open Profile</span>
        </a>

        <button class="btn-action btn-regen" data-index="${index}" aria-label="Regenerate message">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 4 23 10 17 10" />
            <polyline points="1 20 1 14 7 14" />
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10" />
            <path d="M20.49 15a9 9 0 0 1-14.85 3.36L1 14" />
          </svg>
          <span>Regenerate</span>
        </button>
      </div>
    </article>
  `;
}

function renderCards(data) {
  currentResults = data;
  resultsCountNum.textContent = data.length;
  resultsGrid.innerHTML = data.map((r, i) => buildCardHTML(r, i)).join('');
  attachCardListeners();
  applyFilter();
}

function applyFilter() {
  const val = filterSelect.value;
  const cards = resultsGrid.querySelectorAll('.card');
  let visibleCount = 0;
  cards.forEach(card => {
    const match = val === 'all' || card.dataset.focus === val;
    card.style.display = match ? '' : 'none';
    if (match) visibleCount++;
  });
  resultsCountNum.textContent = visibleCount;
}

// ---- Card Event Listeners ----
function attachCardListeners() {
  resultsGrid.querySelectorAll('.btn-copy').forEach(btn => {
    btn.addEventListener('click', handleCopy);
  });
  resultsGrid.querySelectorAll('.btn-regen').forEach(btn => {
    btn.addEventListener('click', handleRegenerate);
  });
}

async function handleCopy(e) {
  const btn = e.currentTarget;
  const idx = parseInt(btn.dataset.index, 10);
  const text = currentResults[idx]?.message || '';
  try {
    await navigator.clipboard.writeText(text);
    const span = btn.querySelector('span');
    const orig = span.textContent;
    span.textContent = 'Copied!';
    btn.classList.add('btn-action--copied');
    showToast('Message copied to clipboard', 'success');
    setTimeout(() => {
      span.textContent = orig;
      btn.classList.remove('btn-action--copied');
    }, 2000);
  } catch {
    showToast('Failed to copy', 'error');
  }
}

async function handleRegenerate(e) {
  const btn = e.currentTarget;
  const idx = parseInt(btn.dataset.index, 10);
  const rec = currentResults[idx];
  if (!rec) return;

  const card = btn.closest('.card');
  const allBtns = card.querySelectorAll('.btn-action');
  const msgBox = card.querySelector('.card__message-box');
  const span = btn.querySelector('span');

  allBtns.forEach(b => b.disabled = true);
  const origLabel = span.textContent;
  span.innerHTML = '<span class="spinner spinner--small"></span>';
  showToast('Regenerating message…', 'info');

  try {
    if (demoMode) {
      await new Promise(r => setTimeout(r, 1200));
      rec.message = `Hi ${rec.name.split(' ')[0]}, just reaching out again — I'd love to explore new opportunities at ${rec.company}. Let's connect!`;
      msgBox.classList.add('fade-out');
      await sleep(300);
      msgBox.textContent = rec.message;
      msgBox.classList.remove('fade-out');
      msgBox.classList.add('fade-in');
      showToast('Message regenerated!', 'success');
    } else {
      const skillsArray = lastSearchParams.user_skills
        ? lastSearchParams.user_skills.split(',').map(s => s.trim()).filter(s => s)
        : [];

      const res = await fetch(ENDPOINTS.regenerate, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recruiter_url: rec.url,
          recruiter_data: rec,
          user_skills: skillsArray.join(','),
        }),
      });

      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      rec.message = data.message || data.msg || rec.message;
      msgBox.classList.add('fade-out');
      await sleep(300);
      msgBox.textContent = rec.message;
      msgBox.classList.remove('fade-out');
      msgBox.classList.add('fade-in');
      showToast('Message regenerated!', 'success');
    }
  } catch (err) {
    showToast('Regeneration failed, try again', 'error');
  } finally {
    span.textContent = origLabel;
    allBtns.forEach(b => b.disabled = false);
  }
}

// ---- Search ----
async function performSearch() {
  const role = roleInput.value.trim();
  const location = locationInput.value.trim();
  const skills = skillsInput.value.trim();

  if (!role || !location) {
    if (!role) roleInput.focus();
    else locationInput.focus();
    showToast('Please fill in both role and location', 'error');
    return;
  }

  lastSearchParams = { role, location, user_skills: skills };

  setSearchLoading(true);
  hide(resultsSection);
  hide(emptyState);
  hide(errorState);
  show(loadingSection);
  renderSkeletons();

  try {
    let data;

    if (demoMode) {
      await new Promise(r => setTimeout(r, 1500));
      data = MOCK_DATA;
    } else {
      const res = await fetch(ENDPOINTS.find, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role,
          location,
          user_skills: skills ? skills.split(',').map(s => s.trim()).filter(s => s) : []
        }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || body.detail || `Request failed (${res.status})`);
      }

      data = await res.json();
      if (data.results && Array.isArray(data.results)) data = data.results;
      if (!Array.isArray(data)) throw new Error('Unexpected response format');
    }

    hide(loadingSection);
    setSearchLoading(false);

    if (data.length === 0) {
      show(emptyState);
    } else {
      filterSelect.value = 'all';
      show(resultsSection);
      renderCards(data);
    }
  } catch (err) {
    hide(loadingSection);
    setSearchLoading(false);

    if (!demoMode && err instanceof TypeError && err.message.includes('fetch')) {
      demoMode = true;
      demoToggle.classList.add('active');
      demoToggle.setAttribute('aria-pressed', 'true');
      showToast('API unreachable — switched to Demo mode', 'info');
      return performSearch();
    }

    errorMessage.textContent = err.message || 'Something went wrong.';
    show(errorState);
  }
}

function setSearchLoading(loading) {
  searchBtn.disabled = loading;
  if (loading) {
    searchBtnText.innerHTML = '<span class="spinner"></span> Searching…';
  } else {
    searchBtnText.textContent = 'Find Recruiters';
  }
}

// ---- UI Resets ----
function resetToSearch() {
  hide(resultsSection);
  hide(emptyState);
  hide(errorState);
  hide(loadingSection);
  searchSection.scrollIntoView({ behavior: 'smooth' });
  roleInput.focus();
}

// ---- Utility ----
function escapeHTML(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function escapeAttr(str) {
  return str.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// ---- Event Listeners ----
searchForm.addEventListener('submit', (e) => {
  e.preventDefault();
  performSearch();
});

filterSelect.addEventListener('change', applyFilter);
emptyRetryBtn.addEventListener('click', resetToSearch);
errorRetryBtn.addEventListener('click', resetToSearch);

demoToggle.addEventListener('click', () => {
  demoMode = !demoMode;
  demoToggle.classList.toggle('active', demoMode);
  demoToggle.setAttribute('aria-pressed', String(demoMode));
  showToast(demoMode ? 'Demo mode enabled' : 'Demo mode disabled', 'info');
});

// ---- Init ----
(function init() {
  renderSkeletons();
})();