console.log('[Coretax Sniffer] Background active');

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'TOKEN_CAPTURED' && msg.data) {
    const token = msg.data;
    const now = new Date().toISOString();

    console.log('[Coretax Sniffer] 🟢 Token captured:', token);

    try {
      chrome.storage.local.set(
        { coretax_token: token, coretax_token_time: now },
        () => {
          console.log('[Coretax Sniffer] Token saved at', now);

          // keep short history
          chrome.storage.local.get('coretax_history', (d) => {
            const history = d.coretax_history || [];
            history.push({
              time: now,
              access_token: token.access_token || '(none)',
            });
            chrome.storage.local.set({ coretax_history: history.slice(-10) });
          });

          // safely notify popup if open
          chrome.runtime.sendMessage({ type: 'TOKEN_UPDATED' }, () => {
            if (chrome.runtime.lastError) {
              // popup not open – ignore
            }
          });
        }
      );

      sendResponse({ status: 'ok' });
    } catch (err) {
      console.error('[Coretax Sniffer] ❌ Error saving token:', err);
      sendResponse({ status: 'error', error: err.message });
    }

    return true;
  }
});
