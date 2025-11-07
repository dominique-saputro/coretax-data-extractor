(() => {
  try {
    if (window.__coretax_injected) return;
    window.__coretax_injected = true;
    console.log("[Coretax PageHook] Installing fetch/XHR interceptors...");

    function sendToken(json) {
      window.postMessage({ type: "CORETAX_TOKEN", data: json }, "*");
    }

    const origFetch = window.fetch;
    if (origFetch && !origFetch.__hooked) {
      window.fetch = async function (...args) {
        const [url, init] = args;
        if (typeof url === "string" && url.includes("/connect/token")) {
          const resp = await origFetch.apply(this, args);
          try {
            const clone = resp.clone();
            clone.json().then(j => {
              if (j && (j.access_token || j.error)) {
                console.log("[Coretax PageHook] Token JSON", j);
                sendToken(j);
              }
            }).catch(() => {});
          } catch (e) {}
          return resp;
        }
        return origFetch.apply(this, args);
      };
      window.fetch.__hooked = true;
    }

    const XHR = window.XMLHttpRequest;
    if (XHR && !XHR.__hooked) {
      const open = XHR.prototype.open;
      const send = XHR.prototype.send;
      XHR.prototype.open = function (method, url) {
        this._url = url;
        return open.apply(this, arguments);
      };
      XHR.prototype.send = function (body) {
        if (this._url && this._url.includes("/connect/token")) {
          this.addEventListener("load", function () {
            try {
              const txt = this.responseText;
              if (!txt) return;
              const j = JSON.parse(txt);
              if (j && (j.access_token || j.error)) {
                console.log("[Coretax PageHook] Token JSON (XHR)", j);
                sendToken(j);
              }
            } catch (e) {}
          });
        }
        return send.apply(this, arguments);
      };
      XHR.__hooked = true;
    }

  } catch (err) {
    console.error("[Coretax PageHook] Error:", err);
  }
})();
