chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getToken') {
    try {
      const searchId = 'cats-portal-angular-clientuser';
      const keys = Object.keys(window.sessionStorage).filter(k => k.startsWith(searchId));

      if (keys.length) {
        const data = JSON.parse(window.sessionStorage.getItem(keys[keys.length - 1]));
        const profile = data?.profile || null;
        return sendResponse({
          token: data?.access_token || null,
          taxpayer_id: profile?.taxpayer_id || null,
          tin: profile?.user_name || null,
          taxpayer_name: profile?.full_name || null,
          roles: profile?.roles || null,
        });
      }
      sendResponse({ error: 'Token not found in sessionStorage' });
    } catch (error) {
      sendResponse({ error: `Error: ${error.message}` });
    }
  }
});
