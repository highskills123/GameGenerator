/* ─────────────────────────────────────────────────────────
   Aibase Web UI  ·  app.js
   ───────────────────────────────────────────────────────── */

'use strict';

// ── File-extension map for downloads ──────────────────────
const FILE_EXT = {
  python: 'py', javascript: 'js', java: 'java', cpp: 'cpp',
  csharp: 'cs', go: 'go', rust: 'rs', typescript: 'ts',
  php: 'php', ruby: 'rb', swift: 'swift', kotlin: 'kt',
};

// ── DOM refs ───────────────────────────────────────────────
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
const copyBtn         = document.getElementById('copy-btn');
const downloadBtn     = document.getElementById('download-btn');
const toast           = document.getElementById('toast');

// ── State ──────────────────────────────────────────────────
let currentLanguage = 'python';
let toastTimer = null;

// ── Fetch language list ────────────────────────────────────
async function loadLanguages() {
  try {
    const res = await fetch('/api/languages');
    if (!res.ok) return;
    const data = await res.json();
    const languages = data.languages || [];

    languageSelect.innerHTML = languages
      .map(lang => {
        const label = lang.charAt(0).toUpperCase() + lang.slice(1);
        return `<option value="${lang}">${label}</option>`;
      })
      .join('');
  } catch (_) {
    // If the API is unreachable, keep the default Python option
  }
}

// ── Loading state helpers ──────────────────────────────────
function setLoading(on) {
  generateBtn.disabled = on;
  btnLabel.textContent = on ? 'Generating…' : 'Generate Code';
  btnIconArrow.classList.toggle('hidden', on);
  btnIconSpinner.classList.toggle('hidden', !on);
}

// ── Show helpers ───────────────────────────────────────────
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

function showCode(code, lang) {
  outputPlaceholder.classList.add('hidden');
  errorContainer.classList.add('hidden');
  codeContainer.classList.remove('hidden');
  outputActions.hidden = false;

  codeContent.textContent = code;
}

// ── Toast ──────────────────────────────────────────────────
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2200);
}

// ── Form submit ────────────────────────────────────────────
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
  const includeComments = commentsToggle.checked;

  setLoading(true);

  try {
    const res = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description, language, include_comments: includeComments }),
    });

    const data = await res.json();

    if (!res.ok || !data.success) {
      showError(data.error || `Server error (HTTP ${res.status})`);
      return;
    }

    showCode(data.code, language);

  } catch (err) {
    if (err instanceof TypeError) {
      showError(
        'Cannot reach the Aibase server. Make sure api_server.py is running on this host.'
      );
    } else {
      showError(err.message || 'Unexpected error. Please try again.');
    }
  } finally {
    setLoading(false);
  }
});

// ── Copy ───────────────────────────────────────────────────
copyBtn.addEventListener('click', async () => {
  const code = codeContent.textContent;
  try {
    await navigator.clipboard.writeText(code);
    showToast('✓ Copied to clipboard!');
  } catch (_) {
    // Fallback for browsers without clipboard API
    const ta = document.createElement('textarea');
    ta.value = code;
    ta.style.cssText = 'position:fixed;opacity:0;top:0;left:0;';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    ta.remove();
    showToast('✓ Copied!');
  }
});

// ── Download ───────────────────────────────────────────────
downloadBtn.addEventListener('click', () => {
  const code = codeContent.textContent;
  const ext  = FILE_EXT[currentLanguage] || 'txt';
  const filename = `generated_code.${ext}`;

  const blob = new Blob([code], { type: 'text/plain' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
  showToast(`✓ Downloaded as ${filename}`);
});

// ── Init ───────────────────────────────────────────────────
loadLanguages();
