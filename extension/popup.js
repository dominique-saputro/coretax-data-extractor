document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('copyBtn').addEventListener('click', copyToken);
  document.getElementById('copyShortBtn').addEventListener('click', copyShortToken);
  document.getElementById('openApiBtn').addEventListener('click', openExtractor);
  document.getElementById('refreshBtn').addEventListener('click', extractToken);
  // Auto-extract on open
  extractToken();
});

function updateTimestamp() {
  const now = new Date();
  document.getElementById('timestamp').textContent = `Grabbed: ${now.toLocaleTimeString()}`;
}

function showStatus(message, type) {
  const status = document.getElementById('status');
  status.textContent = message;
  status.className = `status ${type}`;

  // Keep error messages longer, auto-close others
  if (type !== 'error') {
    setTimeout(() => { status.className = 'status'; }, 5000);
  }
}

function assignRoles(data) {
  // Targets in required order
  const targets = [32, 38, 42];

  // Parse data
  let arr = typeof data === "string" ? JSON.parse(data) : data;

  // Use a Set for O(1) lookups and to ignore duplicates
  const set = new Set(arr.map(Number));

  // Build the 3-digit code
  return targets.map(num => (set.has(num) ? '1' : '0')).join('');
}

function extractToken() {
  const btn = document.getElementById('refreshBtn');
  btn.disabled = true;
  btn.textContent = 'Refreshing...';

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, { action: 'getToken' }, (response) => {
      btn.disabled = false;
      btn.textContent = 'Refresh Token';

      if (chrome.runtime.lastError || !response) {
        showStatus('Could not grab token from coretaxdjp', 'error');
        return;
      }

      if (response.token) {
        const taxidDisplay = document.getElementById('taxidDisplay');
        taxidDisplay.textContent = response.taxpayer_id;
        const taxnameDisplay = document.getElementById('taxnameDisplay');
        taxnameDisplay.textContent = response.taxpayer_name;
        const tinDisplay = document.getElementById('tinDisplay');
        tinDisplay.textContent = response.tin;
        const rolesDisplay = document.getElementById('rolesDisplay');
        rolesDisplay.textContent = assignRoles(response.roles);
        
        const tokenDisplay = document.getElementById('tokenDisplay');
        tokenDisplay.textContent = response.token;
        chrome.storage.local.set({ accessToken: response.token, tokenTime: Date.now() });

        // Auto-copy to clipboard
        // navigator.clipboard.writeText(response.token).then(() => {
        //   updateTimestamp();
        //   showStatus('Token grabbed and copied!', 'success');
        // }).catch(() => {
        //   updateTimestamp();
        //   showStatus('Token grabbed (copy failed)', 'error');
        // });
        console.log(response);
        updateTimestamp();
        showStatus('Token grabbed!', 'success');
      } else if (response.error) {
        showStatus(response.error, 'error');
      } else {
        showStatus('No token found', 'error');
      }
    });
  });
}

function copyToken() {
  const token = document.getElementById('tokenDisplay').textContent;
  if (!token || token == 'No token captured yet.') {
    showStatus('No token to copy', 'error');
    return;
  }
  navigator.clipboard.writeText(token).then(() => {
    showStatus('Copied to clipboard!', 'success');
  }).catch(() => {
    showStatus('Copy failed', 'error');
  });
}

function copyShortToken() {
  const token = document.getElementById('tokenDisplay').textContent;
  const taxid = document.getElementById('taxidDisplay').textContent;
  const taxname = document.getElementById('taxnameDisplay').textContent;
  const tin = document.getElementById('tinDisplay').textContent;
  const roles = document.getElementById('rolesDisplay').textContent;
  if (!token || token == 'No token captured yet.') {
    showStatus('No token to send', 'error');
    return;
  }
  const shortToken = compressAndEncode(token);

  // -------- use this for production
  const apiUrl = `https://coretax-orientcomp.streamlit.app?taxid=${taxid}&taxname=${taxname}&tin=${tin}&roles=${roles}&ct=${shortToken}`;

  navigator.clipboard.writeText(apiUrl).then(() => {
    showStatus('Copied to clipboard!', 'success');
  }).catch(() => {
    showStatus('Copy failed', 'error');
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

function openExtractor(){
  const token = document.getElementById('tokenDisplay').textContent;
  const taxid = document.getElementById('taxidDisplay').textContent;
  const taxname = document.getElementById('taxnameDisplay').textContent;
  const tin = document.getElementById('tinDisplay').textContent;
  const roles = document.getElementById('rolesDisplay').textContent;
  if (!token || token == 'No token captured yet.') {
    showStatus('No token to send', 'error');
    return;
  }
  const shortToken = compressAndEncode(token);

  // -------- use this for production
  const apiUrl = `https://coretax-orientcomp.streamlit.app?taxid=${taxid}&taxname=${taxname}&tin=${tin}&roles=${roles}&ct=${shortToken}`;

  // -------- use this for localtesting
  // const apiUrl = `http://localhost:8501?token=${t.access_token}`;
  chrome.tabs.create({ url: apiUrl });
}
