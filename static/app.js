/* ─────────────────────────────────────────────────────────
   Aibase Web UI  ·  app.js
   ───────────────────────────────────────────────────────── */

'use strict';

// ── File-extension map for all 21 supported languages ─────
const FILE_EXT = {
  python: 'py', javascript: 'js', java: 'java', cpp: 'cpp',
  csharp: 'cs', go: 'go', rust: 'rs', typescript: 'ts',
  php: 'php', ruby: 'rb', swift: 'swift', kotlin: 'kt',
  flutter: 'dart', dart: 'dart',
  'react-native': 'tsx',
  flame: 'dart', 'flame-game': 'dart', 'flame-component': 'dart',
  'game-asset-sprite': 'dart', 'game-asset-animation': 'dart',
  'game-tilemap': 'dart',
};

// ── Toast ──────────────────────────────────────────────────
const toast = document.getElementById('toast');
let toastTimer = null;
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2200);
}

// ── Shared copy/download helpers ──────────────────────────
function attachCopyDownload(copyId, downloadId, getCode, filename) {
  const copyBtn = document.getElementById(copyId);
  const dlBtn   = document.getElementById(downloadId);
  if (!copyBtn || !dlBtn) return;

  copyBtn.addEventListener('click', async () => {
    const code = getCode();
    try {
      await navigator.clipboard.writeText(code);
    } catch (_) {
      const ta = document.createElement('textarea');
      ta.value = code; ta.style.cssText = 'position:fixed;opacity:0;';
      document.body.appendChild(ta); ta.select();
      document.execCommand('copy'); ta.remove();
    }
    showToast('✓ Copied to clipboard!');
  });

  dlBtn.addEventListener('click', () => {
    const code  = getCode();
    const fname = typeof filename === 'function' ? filename() : filename;
    const blob = new Blob([code], { type: 'text/plain' });
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), { href: url, download: fname });
    a.click(); URL.revokeObjectURL(url);
    showToast(`✓ Downloaded as ${fname}`);
  });
}

// ══════════════════════════════════════════════════════════
//   MODE: TRANSLATE
// ══════════════════════════════════════════════════════════
const form            = document.getElementById('translate-form');
const descriptionEl   = document.getElementById('description');
const languageSelect  = document.getElementById('language');
const commentsToggle  = document.getElementById('include-comments');
const generateBtn     = document.getElementById('generate-btn');
const btnLabel        = document.getElementById('btn-label');
const btnIconArrow    = document.getElementById('btn-icon-arrow');
const btnIconSpinner  = document.getElementById('btn-icon-spinner');
const outputActions   = document.getElementById('output-actions');
const outputPlaceholder = document.getElementById('output-placeholder');
const errorContainer  = document.getElementById('error-container');
const errorMessage    = document.getElementById('error-message');
const codeContainer   = document.getElementById('code-container');
const codeContent     = document.getElementById('code-content');

let currentLanguage = 'python';

// ── Fetch language list (with display names) ──────────────
async function loadLanguages() {
  try {
    const res = await fetch('/api/languages');
    if (!res.ok) return;
    const data = await res.json();
    const keys   = data.languages || [];
    const names  = data.names    || {};

    languageSelect.innerHTML = keys
      .map(lang => {
        const label = names[lang] || (lang.charAt(0).toUpperCase() + lang.slice(1));
        return `<option value="${lang}">${label}</option>`;
      })
      .join('');
  } catch (_) {
    // Keep default Python option if API unreachable
  }
}

function setLoading(on) {
  generateBtn.disabled = on;
  btnLabel.textContent = on ? 'Generating…' : 'Generate Code';
  btnIconArrow.classList.toggle('hidden', on);
  btnIconSpinner.classList.toggle('hidden', !on);
}

function showPlaceholder() {
  outputPlaceholder.classList.remove('hidden');
  codeContainer.classList.add('hidden');
  errorContainer.classList.add('hidden');
  outputActions.hidden = true;
}

function showError(msg) {
  outputPlaceholder.classList.add('hidden');
  codeContainer.classList.add('hidden');
  errorContainer.classList.remove('hidden');
  errorMessage.textContent = msg;
  outputActions.hidden = true;
}

function showCode(code) {
  outputPlaceholder.classList.add('hidden');
  errorContainer.classList.add('hidden');
  codeContainer.classList.remove('hidden');
  outputActions.hidden = false;
  codeContent.textContent = code;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const description = descriptionEl.value.trim();
  if (!description) {
    descriptionEl.focus();
    showError('Please enter a description of the code you want to generate.');
    return;
  }
  const language = languageSelect.value;
  currentLanguage = language;
  setLoading(true);
  try {
    const res = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description, language, include_comments: commentsToggle.checked }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) { showError(data.error || `Server error (HTTP ${res.status})`); return; }
    showCode(data.code);
  } catch (err) {
    showError(err instanceof TypeError
      ? 'Cannot reach the Aibase server. Make sure api_server.py is running.'
      : (err.message || 'Unexpected error. Please try again.'));
  } finally { setLoading(false); }
});

attachCopyDownload(
  'copy-btn', 'download-btn',
  () => codeContent.textContent,
  () => `generated_code.${FILE_EXT[currentLanguage] || 'txt'}`
);

// ══════════════════════════════════════════════════════════
//   MODE: FLUTTER
// ══════════════════════════════════════════════════════════
const flutterTypeSelect   = document.getElementById('flutter-type');
const flutterGenBtn       = document.getElementById('flutter-gen-btn');
const flutterBtnLabel     = document.getElementById('flutter-btn-label');
const flutterIconArrow    = document.getElementById('flutter-icon-arrow');
const flutterIconSpinner  = document.getElementById('flutter-icon-spinner');
const flutterOutputActions = document.getElementById('flutter-output-actions');
const flutterPlaceholder  = document.getElementById('flutter-output-placeholder');
const flutterError        = document.getElementById('flutter-error');
const flutterErrorMsg     = document.getElementById('flutter-error-msg');
const flutterCodeContainer = document.getElementById('flutter-code-container');
const flutterCodeContent  = document.getElementById('flutter-code-content');

const flutterSubforms = {
  widget: document.getElementById('flutter-widget-fields'),
  screen: document.getElementById('flutter-screen-fields'),
  app:    document.getElementById('flutter-app-fields'),
};

flutterTypeSelect.addEventListener('change', () => {
  Object.entries(flutterSubforms).forEach(([k, el]) =>
    el.classList.toggle('hidden', k !== flutterTypeSelect.value));
});

function flutterSetLoading(on) {
  flutterGenBtn.disabled = on;
  flutterBtnLabel.textContent = on ? 'Generating…' : 'Generate Flutter Code';
  flutterIconArrow.classList.toggle('hidden', on);
  flutterIconSpinner.classList.toggle('hidden', !on);
}

function flutterShowCode(code) {
  flutterPlaceholder.classList.add('hidden');
  flutterError.classList.add('hidden');
  flutterCodeContainer.classList.remove('hidden');
  flutterOutputActions.hidden = false;
  flutterCodeContent.textContent = code;
}

function flutterShowError(msg) {
  flutterPlaceholder.classList.add('hidden');
  flutterCodeContainer.classList.add('hidden');
  flutterError.classList.remove('hidden');
  flutterErrorMsg.textContent = msg;
  flutterOutputActions.hidden = true;
}

function parseJsonField(val) {
  if (!val || !val.trim()) return undefined;
  try { return JSON.parse(val.trim()); } catch (_) { return undefined; }
}

flutterGenBtn.addEventListener('click', async () => {
  const type = flutterTypeSelect.value;
  let url, body;

  if (type === 'widget') {
    const wt   = document.getElementById('flutter-widget-type').value;
    const name = document.getElementById('flutter-widget-name').value.trim();
    if (!name) { flutterShowError('Widget Name is required.'); return; }
    const props = parseJsonField(document.getElementById('flutter-widget-props').value);
    url  = '/api/generate/flutter/widget';
    body = { widget_type: wt, name, ...(props ? { properties: props } : {}) };

  } else if (type === 'screen') {
    const name = document.getElementById('flutter-screen-name').value.trim();
    if (!name) { flutterShowError('Screen Name is required.'); return; }
    const raw = document.getElementById('flutter-screen-widgets').value.trim();
    const widgets = raw ? raw.split(',').map(s => s.trim()).filter(Boolean) : undefined;
    url  = '/api/generate/flutter/screen';
    body = { screen_name: name, ...(widgets ? { widgets } : {}) };

  } else {
    const name = document.getElementById('flutter-app-name').value.trim();
    if (!name) { flutterShowError('App Name is required.'); return; }
    const route = document.getElementById('flutter-app-route').value.trim();
    url  = '/api/generate/flutter/app';
    body = { app_name: name, ...(route ? { initial_route: route } : {}) };
  }

  flutterSetLoading(true);
  try {
    const res  = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const data = await res.json();
    if (!res.ok || !data.success) { flutterShowError(data.error || `Server error (HTTP ${res.status})`); return; }
    flutterShowCode(data.code);
  } catch (err) {
    flutterShowError(err instanceof TypeError
      ? 'Cannot reach the Aibase server.'
      : (err.message || 'Unexpected error.'));
  } finally { flutterSetLoading(false); }
});

attachCopyDownload(
  'flutter-copy-btn', 'flutter-download-btn',
  () => flutterCodeContent.textContent,
  'generated.dart'
);

// ══════════════════════════════════════════════════════════
//   MODE: REACT NATIVE
// ══════════════════════════════════════════════════════════
const rnTypeSelect    = document.getElementById('rn-type');
const rnGenBtn        = document.getElementById('rn-gen-btn');
const rnBtnLabel      = document.getElementById('rn-btn-label');
const rnIconArrow     = document.getElementById('rn-icon-arrow');
const rnIconSpinner   = document.getElementById('rn-icon-spinner');
const rnOutputActions = document.getElementById('rn-output-actions');
const rnPlaceholder   = document.getElementById('rn-output-placeholder');
const rnError         = document.getElementById('rn-error');
const rnErrorMsg      = document.getElementById('rn-error-msg');
const rnCodeContainer = document.getElementById('rn-code-container');
const rnCodeContent   = document.getElementById('rn-code-content');

const rnSubforms = {
  component: document.getElementById('rn-component-fields'),
  screen:    document.getElementById('rn-screen-fields'),
  app:       document.getElementById('rn-app-fields'),
};

rnTypeSelect.addEventListener('change', () => {
  Object.entries(rnSubforms).forEach(([k, el]) =>
    el.classList.toggle('hidden', k !== rnTypeSelect.value));
});

function rnSetLoading(on) {
  rnGenBtn.disabled = on;
  rnBtnLabel.textContent = on ? 'Generating…' : 'Generate React Native Code';
  rnIconArrow.classList.toggle('hidden', on);
  rnIconSpinner.classList.toggle('hidden', !on);
}

function rnShowCode(code) {
  rnPlaceholder.classList.add('hidden');
  rnError.classList.add('hidden');
  rnCodeContainer.classList.remove('hidden');
  rnOutputActions.hidden = false;
  rnCodeContent.textContent = code;
}

function rnShowError(msg) {
  rnPlaceholder.classList.add('hidden');
  rnCodeContainer.classList.add('hidden');
  rnError.classList.remove('hidden');
  rnErrorMsg.textContent = msg;
  rnOutputActions.hidden = true;
}

rnGenBtn.addEventListener('click', async () => {
  const type = rnTypeSelect.value;
  let url, body;

  if (type === 'component') {
    const ct   = document.getElementById('rn-component-type').value;
    const name = document.getElementById('rn-component-name').value.trim();
    if (!name) { rnShowError('Component Name is required.'); return; }
    const props = parseJsonField(document.getElementById('rn-component-props').value);
    const rawHooks = document.getElementById('rn-component-hooks').value.trim();
    const hooks = rawHooks ? rawHooks.split(',').map(s => s.trim()).filter(Boolean) : undefined;
    url  = '/api/generate/react-native/component';
    body = { component_type: ct, name,
             ...(props ? { props } : {}),
             ...(hooks ? { hooks_needed: hooks } : {}) };

  } else if (type === 'screen') {
    const name = document.getElementById('rn-screen-name').value.trim();
    if (!name) { rnShowError('Screen Name is required.'); return; }
    const raw = document.getElementById('rn-screen-components').value.trim();
    const components = raw ? raw.split(',').map(s => s.trim()).filter(Boolean) : undefined;
    url  = '/api/generate/react-native/screen';
    body = { screen_name: name, ...(components ? { components } : {}) };

  } else {
    const name = document.getElementById('rn-app-name').value.trim();
    if (!name) { rnShowError('App Name is required.'); return; }
    const typescript    = document.getElementById('rn-typescript').checked;
    const initialScreen = document.getElementById('rn-initial-screen').value.trim();
    url  = '/api/generate/react-native/app';
    body = { app_name: name, typescript,
             ...(initialScreen ? { initial_screen: initialScreen } : {}) };
  }

  rnSetLoading(true);
  try {
    const res  = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const data = await res.json();
    if (!res.ok || !data.success) { rnShowError(data.error || `Server error (HTTP ${res.status})`); return; }
    rnShowCode(data.code);
  } catch (err) {
    rnShowError(err instanceof TypeError
      ? 'Cannot reach the Aibase server.'
      : (err.message || 'Unexpected error.'));
  } finally { rnSetLoading(false); }
});

const rnTypescript = document.getElementById('rn-typescript');
attachCopyDownload(
  'rn-copy-btn', 'rn-download-btn',
  () => rnCodeContent.textContent,
  () => rnTypescript.checked ? 'generated.tsx' : 'generated.js'
);

// ══════════════════════════════════════════════════════════
//   MODE TABS
// ══════════════════════════════════════════════════════════
const modeTabs  = document.querySelectorAll('.mode-tab');
const modePanels = {
  translate:      document.getElementById('mode-translate'),
  flutter:        document.getElementById('mode-flutter'),
  'react-native': document.getElementById('mode-react-native'),
};

modeTabs.forEach(tab => {
  tab.addEventListener('click', () => {
    const mode = tab.dataset.mode;
    modeTabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    Object.entries(modePanels).forEach(([k, el]) =>
      el.classList.toggle('hidden', k !== mode));
  });
});

// ── Init ───────────────────────────────────────────────────
loadLanguages();

