const statusEl = document.getElementById('status');
const expEl = document.getElementById('exp');
const timeEl = document.getElementById('time');
const tokenShort = document.getElementById('tokenShort');
const tokenJson = document.getElementById('tokenJson');
const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');
const clearBtn = document.getElementById('clearBtn');
const refreshBtn = document.getElementById('refreshBtn');
const openApiBtn = document.getElementById('openApiBtn');
const historyList = document.getElementById('historyList');

function formatTime(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleString();
  } catch {
    return iso;
  }
}

function renderToken(obj) {
  if (!obj) {
    statusEl.textContent = 'No token';
    expEl.style.display = 'none';
    timeEl.style.display = 'none';
    tokenShort.textContent = 'No token captured yet.';
    tokenJson.textContent = 'No token captured yet.';
    copyBtn.disabled = true;
    downloadBtn.disabled = true;
    clearBtn.disabled = true;
    openApiBtn.disabled = true;
    return;
  }

  const when = obj.__captured_at || obj.captured_at || null;
  const expiresIn = obj.expires_in || null;
  const access = obj.access_token || null;
  statusEl.textContent = '✅ Token captured';
  timeEl.style.display = when ? 'inline-block' : 'none';
  expEl.style.display = expiresIn ? 'inline-block' : 'none';
  if (when) timeEl.textContent = `At ${formatTime(when)}`;
  if (expiresIn) expEl.textContent = `Expires in ${expiresIn}s`;

  tokenShort.textContent = access
    ? `${access.slice(0, 40)}...${access.slice(-10)}`
    : 'No access_token property';
  tokenJson.textContent = JSON.stringify(obj, null, 2);

  copyBtn.disabled = !access;
  downloadBtn.disabled = false;
  clearBtn.disabled = false;
  openApiBtn.disabled = false;
}

function renderHistory(history) {
  if (!history || history.length === 0) {
    historyList.innerHTML = '<div class="empty">No captures yet.</div>';
    return;
  }

  historyList.innerHTML = history
    .slice(-5)
    .reverse()
    .map(
      (h) => `
      <div class="history-entry">
        <b>${formatTime(h.time)}</b><br/>
        <small>${h.access_token ? `${h.access_token.slice(0, 25)}...` : 'No token'}</small>
      </div>`
    )
    .join('');
}

function load() {
  chrome.storage.local.get(['coretax_token', 'coretax_token_time', 'coretax_history'], (d) => {
    const token = d.coretax_token || null;
    if (token && !token.__captured_at) {
      token.__captured_at = d.coretax_token_time || new Date().toISOString();
    }
    renderToken(token);
    renderHistory(d.coretax_history || []);
  });
}

function compressAndEncode(token) {
  // 1️⃣ Convert to JSON and then to UTF-8 bytes
  const json = JSON.stringify(token);
  const bytes = new TextEncoder().encode(json);

  // 2️⃣ Compress using pako (tiny gzip library)
  const compressed = pako.deflate(bytes);

  // 3️⃣ Encode to base64 (URL-safe)
  return btoa(String.fromCharCode(...compressed))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

// --- button actions ---
copyBtn.addEventListener('click', async () => {
  chrome.storage.local.get('coretax_token', async (d) => {
    const t = d.coretax_token;
    if (!t || !t.access_token) return;
    try {
      await navigator.clipboard.writeText(t.access_token);
      copyBtn.textContent = 'Copied!';
      setTimeout(() => (copyBtn.textContent = 'Copy access_token'), 1200);
    } catch (e) {
      window.prompt('Copy the token manually:', t.access_token);
    }
  });
});

downloadBtn.addEventListener('click', () => {
  chrome.storage.local.get('coretax_token', (d) => {
    const t = d.coretax_token;
    if (!t) return;
    const blob = new Blob([JSON.stringify(t, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'coretax_token.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });
});

clearBtn.addEventListener('click', () => {
  if (!confirm('Clear stored token and request details?')) return;
  chrome.storage.local.remove(['coretax_token', 'coretax_token_time', 'coretax_history'], load);
});

refreshBtn.addEventListener('click', load);

openApiBtn.addEventListener('click', () => {
  chrome.storage.local.get('coretax_token', (d) => {
    const t = d.coretax_token;
    if (!t || !t.access_token) {
      alert('No access_token to send.');
      return;
    }
    const shortToken = compressAndEncode(t);

    // -------- use this for production
    const apiUrl = `https://coretax-orientcomp.streamlit.app?ct=${shortToken}`;

    // -------- use this for localtesting
    // const apiUrl = `http://localhost:8501?token=${t.access_token}`;
    chrome.tabs.create({ url: apiUrl });
  });
});

// listen to storage changes
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && (changes.coretax_token || changes.coretax_token_time)) {
    load();
  }
});

load();
