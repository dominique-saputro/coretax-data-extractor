console.log('[Coretax Sniffer] Background active');

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'TOKEN_CAPTURED' && msg.data) {
    const token = msg.data;
    const now = new Date().toISOString();

    console.log('[Coretax Sniffer] 🟢 Token captured:', token);

    try {
      chrome.storage.local.set(
        { coretax_token: token, coretax_token_time: now },
        async () => {
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

          // ✅ Try to send token to any open Streamlit tab
          const streamlitUrl = 'https://coretax-orientcomp.streamlit.app/';
          const tabs = await chrome.tabs.query({ url: streamlitUrl + '*' });

          if (tabs.length > 0) {
            console.log(`[Coretax Sniffer] 🔄 Found ${tabs.length} Streamlit tab(s), injecting token...`);

            for (const tab of tabs) {
              try {
                await chrome.scripting.executeScript({
                  target: { tabId: tab.id },
                  func: (t) => {
                    window.postMessage({ type: 'SET_TOKEN', token: t }, '*');
                  },
                  args: [token],
                });
                console.log(`[Coretax Sniffer] ✅ Token sent to Streamlit tab ${tab.id}`);
              } catch (err) {
                console.warn(`[Coretax Sniffer] ⚠️ Failed to inject token into tab ${tab.id}:`, err);
              }
            }
          } else {
            console.log('[Coretax Sniffer] ⚪ No Streamlit tab open yet — will send when opened.');
          }

          // Notify popup if open
          chrome.runtime.sendMessage({ type: 'TOKEN_UPDATED' }, () => {
            if (chrome.runtime.lastError) {
              // popup not open — ignore
            }
          });

          sendResponse({ status: 'ok' });
        }
      );

      return true; // keep message channel alive for async ops
    } catch (err) {
      console.error('[Coretax Sniffer] ❌ Error saving token:', err);
      sendResponse({ status: 'error', error: err.message });
    }
  }
});
