const VPS_URL = "http://localhost:8000";

const captchaImage = document.getElementById("captchaImage");
const statusDiv = document.getElementById("status");

let sessionId = null;

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

async function loadCaptcha() {
    statusDiv.textContent = "Loading CAPTCHA...";

    const res = await fetch(`${VPS_URL}/captcha`);

    const result = await res.json();

    sessionId = result.session_id;

    if (result.success) {
        console.log(result.session);
        statusDiv.textContent = "Login successful";
        const data = result.session
        const roles = assignRoles(data.roles)
        const shortToken = compressAndEncode(data.access_token);
        const apiUrl = `http://103.28.22.140:8501?taxid=${data.taxpayer_id}&taxname=${data.taxpayer_name}&tin=${data.tin}&roles=${data.roles}&ct=${shortToken}`;
        // -------- use this for localtesting
        // const apiUrl = `http://localhost:8501?taxid=${data.taxpayer_id}&taxname=${data.taxpayer_name}&tin=${data.tin}&roles=${roles}&ct=${shortToken}`;
        chrome.tabs.create({ url: apiUrl });
    } else {
        captchaImage.src =
            `${VPS_URL}${result.image_url}`;

        statusDiv.textContent = "";
    }
}

document
    .getElementById("refreshCaptcha")
    .addEventListener("click", loadCaptcha);

document
    .getElementById("loginBtn")
    .addEventListener("click", async () => {

        statusDiv.textContent = "Logging in...";

        const payload = {
            session_id: sessionId,

            username:
                document.getElementById("username").value,

            password:
                document.getElementById("password").value,

            captcha:
                document.getElementById("captchaInput").value
        };

        const res = await fetch(`${VPS_URL}/login`, {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(payload)
        });

        const result = await res.json();

        if (result.success) {
            statusDiv.textContent = "Login successful";
            const data = result.session
            const roles = assignRoles(data.roles)
            const shortToken = compressAndEncode(data.access_token);
            const apiUrl = `http://103.28.22.140:8501?taxid=${data.taxpayer_id}&taxname=${data.taxpayer_name}&tin=${data.tin}&roles=${data.roles}&ct=${shortToken}`;
            // -------- use this for localtesting
            // const apiUrl = `http://localhost:8501?taxid=${data.taxpayer_id}&taxname=${data.taxpayer_name}&tin=${data.tin}&roles=${roles}&ct=${shortToken}`;
            chrome.tabs.create({ url: apiUrl });
        } else {
            statusDiv.textContent =
                "Login failed: " + result.message;

            // loadCaptcha();
        }
    });

loadCaptcha();