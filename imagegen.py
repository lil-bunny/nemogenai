import json
from playwright.async_api import async_playwright
import asyncio

IMAGE_SELECTOR = "img[alt*='image']"   # adjust if UI different

def load_from_file():
    path = r"C:\nemogenai\promptfilenew.json"
    with open(path, 'r') as file:
        data = json.load(file)
    return data

async def click_run_button(page):
    print("[LOG] Looking for Run button...")

    buttons = [
        "button:has-text('Run')",
        "button[aria-label='Run']",
        "button.mat-mdc-fab"
    ]

    for selector in buttons:
        try:
            if await page.locator(selector).is_visible():
                print(f"[LOG] Clicking Run button using selector: {selector}")
                await page.locator(selector).click()
                return True
        except:
            pass

    print("[ERROR] Run button not found.")
    return False


async def wait_for_image_to_load(page, selector=IMAGE_SELECTOR, timeout=20000):
    print("[LOG] Waiting for image to load completely...")
    await page.wait_for_selector(selector, timeout=timeout)

    await page.wait_for_function(
        """(selector) => {
            const img = document.querySelector(selector);
            if (!img) return false;
            return img.complete && img.naturalWidth > 100 && img.naturalHeight > 100;
        }""",
        selector,
        timeout=timeout
    )

    print("[LOG] Image fully loaded ✔")


async def download_generated_image(page):
    print("[LOG] Preparing to download image...")

    await wait_for_image_to_load(page)

    for attempt in range(3):
        try:
            print(f"[LOG] Clicking Download button (attempt {attempt+1})...")
            await page.locator("text=Download").click()
            await asyncio.sleep(2)
            return True
        except:
            await asyncio.sleep(2)

    print("[ERROR] Download button failed.")
    return False


async def send_prompt(page, prompt_text, index):
    print(f"\n[LOG] Sending prompt #{index}...")

    await page.locator("textarea").fill(prompt_text)

    # PRESS RUN BUTTON HERE 🔥
    await click_run_button(page)

    print("[LOG] Waiting for model to generate image...")
    await page.wait_for_selector(IMAGE_SELECTOR, timeout=30000)

    await wait_for_image_to_load(page)

    print("[LOG] Downloading final image...")
    await download_generated_image(page)

    print(f"[LOG] Prompt #{index} completed ✔")


async def googleaistudio():
    is_newprocess = True
    prompts = load_from_file()

    print("Launching Google AI Studio Automation…")

    async with async_playwright() as p:
        for i, prompt in enumerate(prompts):

            if is_newprocess:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                context = browser.contexts[0]
                page = context.pages[-1]

                await page.goto(
                    "https://aistudio.google.com/prompts/new_chat?model=gemini-2.5-flash-image"
                )
                await page.wait_for_timeout(5000)

                if await page.locator("text=Continue").is_visible():
                    await page.locator("text=Continue").click()

                print("[LOG] Setting Aspect Ratio 16:9...")
                await page.locator("//mat-select[@aria-label='Aspect ratio']").click()
                await page.wait_for_selector(
                    "//span[@class='mdc-list-item__primary-text' and normalize-space()='16:9']",
                    timeout=5000
                )
                await page.locator(
                    "//span[@class='mdc-list-item__primary-text' and normalize-space()='16:9']"
                ).click()

                print("[LOG] Aspect Ratio set ✔")
                is_newprocess = False

            else:
                await send_prompt(page, prompt['image'], i)

                if 'act' in prompt:
                    print("Finished act =", prompt['act'])
                    is_newprocess = True

    print("\n✅ ALL PROMPTS DONE")

asyncio.run(googleaistudio())
