console.log("[Coretax Sniffer] Injecting via chrome-extension://");

// --- Inject page_hook.js into the actual webpage ---
const script = document.createElement("script");
script.src = chrome.runtime.getURL("page_hook.js");
(document.head || document.documentElement).appendChild(script);
script.onload = () => {
  console.log("[Coretax Sniffer] Page hook script loaded");
  script.remove();
};

// --- Bridge between page context and extension background ---
window.addEventListener("message", (event) => {
  if (event.source !== window) return; // only listen to our own window
  if (!event.data || event.data.type !== "CORETAX_TOKEN") return;

  const token = event.data.data;
  console.log("[Coretax Sniffer] 🔄 Token received from page, forwarding to background:", token);

  chrome.runtime.sendMessage({
      type: "TOKEN_CAPTURED",
      data: token,
    },
    (response) => {
      if (chrome.runtime.lastError) {
        console.warn("[Coretax Sniffer] SendMessage error:", chrome.runtime.lastError.message);
      } else {
        console.log("[Coretax Sniffer] ✅ Token sent successfully to background:", response);
      }
    }
  );
});

// --- Forward message to streamlit app ---
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "SET_TOKEN") {
    window.postMessage(
      {
        type: "SET_TOKEN",
        token: message.token,
      },
      "*"
    );
  }
});

// --- Optional: direct fetch hook (fallback if page_hook is blocked) ---
(function () {
  const originalFetch = window.fetch;
  window.fetch = async (...args) => {
    const response = await originalFetch(...args);

    try {
      const url = args[0];
      if (typeof url === "string" && url.includes("/connect/token")) {
        const clone = response.clone();
        const data = await clone.json();

        if (data.access_token) {
          console.log("[Coretax Sniffer] 🎯 Access token found (direct hook):", data.access_token);
          chrome.runtime.sendMessage({
            type: "TOKEN_CAPTURED",
            data: data,
          });
        }
      }
    } catch (err) {
      console.error("[Coretax Sniffer] Error reading token:", err);
    }

    return response;
  };
})();
