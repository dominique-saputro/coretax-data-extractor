import uuid
import os
import glob

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from playwright.async_api import async_playwright

# =========================================================
# HELPERS
# =========================================================

def clear_captchas():

    files = glob.glob("captchas/*")

    for file in files:
        try:
            os.remove(file)
        except:
            pass
        
def response_logger(response):

            global success
            
            responses = []

            print("RESPONSE:", response.status, response.url)

            responses.append(response.url)

            if "/connect/token" in response.url:
                success = True
        
async def get_session_data(page):

    return await page.evaluate("""
    () => {

        try {

            const searchId =
                'cats-portal-angular-clientuser';

            const keys = Object.keys(sessionStorage)
                .filter(
                    k => k.startsWith(searchId)
                );

            if (!keys.length) {

                return {
                    success: false,
                    error: 'Token not found in sessionStorage'
                };
            }

            const latestKey =
                keys[keys.length - 1];

            const raw =
                sessionStorage.getItem(latestKey);

            const data = JSON.parse(raw);

            const profile =
                data?.profile || {};

            return {

                success: true,
                storage_key: latestKey,
                access_token:
                    data?.access_token || null,
                taxpayer_id:
                    profile?.taxpayer_id || null,
                tin:
                    profile?.user_name || null,
                taxpayer_name:
                    profile?.full_name || null,
                roles:
                    profile?.roles || null
            };

        } catch (error) {

            return {
                success: false,
                error: error.message
            };
        }
    }
    """)    


# =========================================================
# APP SETUP
# =========================================================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("captchas", exist_ok=True)

sessions = {}

playwright_instance = None
browser = None

LOGIN_URL = (
    "https://coretaxdjp.pajak.go.id/"
    "identityproviderportal/Account/Login"
)


# =========================================================
# MODELS
# =========================================================

class LoginRequest(BaseModel):
    session_id: str
    username: str
    password: str
    captcha: str


# =========================================================
# PLAYWRIGHT STARTUP
# =========================================================

@app.on_event("startup")
async def startup():

    global playwright_instance
    global browser

    playwright_instance = await async_playwright().start()

    browser = await playwright_instance.chromium.launch_persistent_context(
        user_data_dir="./chromium_profile",
        headless=True,
        # devtools=True,
        # args=[
        #     "--disable-quic",
        #     "--disable-http3",
        #     "--disable-features=UseChromeOSDirectVideoDecoder",
        #     "--disable-blink-features=AutomationControlled"
        # ]
    )


@app.on_event("shutdown")
async def shutdown():

    global browser
    global playwright_instance

    if browser:
        await browser.close()

    if playwright_instance:
        await playwright_instance.stop()


# =========================================================
# CAPTCHA ROUTE
# =========================================================

@app.get("/captcha")
async def create_captcha():

    clear_captchas()
    session_id = str(uuid.uuid4())
    
    context = browser
    page = browser.pages[0] if browser.pages else await browser.new_page()

    # Load login page
    await page.goto(
        LOGIN_URL,
        wait_until="networkidle"
    )
    
    session_data = await get_session_data(page)
    
    if session_data.get("success"):
        print("AUTH SUCCESS")
        print(session_data)
        return {
            "success": True,
            "session": session_data
        }
    else:
        # Wait for captcha image
        await page.wait_for_selector(
            "#dntCaptchaImg"
        )

        # Allow all session/cookies/scripts to settle
        await page.wait_for_timeout(1500)

        # Screenshot captcha
        captcha_locator = page.locator(
            "#dntCaptchaImg"
        )

        captcha_path = f"captchas/{session_id}.png"

        await captcha_locator.screenshot(
            path=captcha_path
        )

        # Store session
        sessions[session_id] = {
            "context": context,
            "page": page
        }

        return {
            "session_id": session_id,
            "image_url": f"/captcha_image/{session_id}"
        }


# =========================================================
# CAPTCHA IMAGE
# =========================================================

@app.get("/captcha_image/{session_id}")
async def captcha_image(session_id: str):

    path = f"captchas/{session_id}.png"

    return FileResponse(path)


# =========================================================
# LOGIN
# =========================================================

@app.post("/login")
async def login(data: LoginRequest):

    if data.session_id not in sessions:
        return {
            "success": False,
            "message": "Invalid session"
        }

    session = sessions[data.session_id]

    page = session["page"]
    context = session["context"]
    
    # Monitor popups
    page.on(
        "request",
        lambda r: print(
            "REQUEST:",
            r.method,
            r.url
        )
    )

    page.on(
        "response",
        lambda r: print(
            "RESPONSE:",
            r.status,
            r.url
        )
    )

    page.on(
        "console",
        lambda msg: print(
            "BROWSER LOG:",
            msg.type,
            msg.text
        )
    )

    page.on(
        "pageerror",
        lambda err: print(
            "PAGE ERROR:",
            err
        )
    )

    try:

        # Ensure page still alive
        await page.wait_for_load_state("domcontentloaded")

        # Fill username
        await page.fill(
            "#Username",
            # data.username
            "3578096402000005"
        )

        # Fill password
        await page.fill(
            "#password",
            # data.password
            "Moniq2402!!"
        )

        # Fill captcha
        await page.fill(
            "#DNTCaptchaInputText",
            data.captcha
        )

        # Small delay to mimic human timing
        await page.wait_for_timeout(500)

        # Verify anti-forgery token still exists
        # token = await page.locator(
        #     'input[name="__RequestVerificationToken"]'
        # ).input_value()

        # print("Submitting with token:")
        # print(token)

        # Verify cookies still exist
        # cookies = await context.cookies()

        # print("Cookies before login:")
        # print(cookies)

        # Listen for responses
        success = False

        # page.on("response", response_logger)

        # Submit REAL FORM
        await page.locator(
            'button[name="button"][value="login"]'
        ).click()
        
        for attempt in range(5):
            await page.wait_for_timeout(3000)
            session_data = await get_session_data(page)

            if session_data.get("success"):

                print("AUTH SUCCESS:")
                print(session_data)

                return {
                    "success": True,
                    "session": session_data
                }

            print(f"Retry #{attempt + 1}")

            try:
                await page.reload(wait_until="domcontentloaded")
            except:
                pass
            
        return {
            "success": False,
            "message": "Session token never appeared"
        }
            
        # print("Cookies After Login:")
        # print(await context.cookies())

        # local_storage_keys = await page.evaluate(
        #     "() => Object.keys(localStorage)"
        # )

        # session_storage_keys = await page.evaluate(
        #     "() => Object.keys(sessionStorage)"
        # )

        # print("LOCAL STORAGE KEYS:")
        # print(local_storage_keys)

        # print("SESSION STORAGE KEYS:")
        # print(session_storage_keys)


    except Exception as e:

        # Save crash screenshot
        try:
            await page.screenshot(
                path="exception.png",
                full_page=True
            )
        except:
            pass

        return {
            "success": False,
            "message": str(e)
        }