import os, asyncio
import httpx
from playwright.async_api import async_playwright

OUTPUTS_DIR = "outputs"
DOWNLOADS_DIR = "downloadvideo"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

BTN_TEXTS = ["Animate","Make video","Make Video","Generate","Regenerate"]

async def find_action_btn(page):
    for txt in BTN_TEXTS:
        btn = await page.query_selector(f'button:has-text("{txt}")')
        if btn: return btn
    return None

async def wait_action_btn(page, timeout=300):
    for _ in range(timeout):
        btn = await find_action_btn(page)
        if btn and not await btn.is_disabled():
            return btn
        await asyncio.sleep(1)
    raise Exception("action button never enabled")

async def wait_video_ready(page, timeout=600):
    for _ in range(timeout):
        video_btn = await page.query_selector('button:has-text("Video")')
        if video_btn and not await video_btn.is_disabled():
            return video_btn
        await asyncio.sleep(1)
    raise Exception("video button never enabled")

async def wait_dl_icon(page, timeout=600):
    for _ in range(timeout):
        dl_btn = await page.query_selector('button[aria-label="Download"]')
        if dl_btn and not await dl_btn.is_disabled():
            return dl_btn
        await asyncio.sleep(1)
    raise Exception("download icon never enabled")

async def main():
    async with async_playwright() as p:

        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto("https://grok.com/imagine")

        for file in os.listdir(OUTPUTS_DIR):

            if not file.lower().endswith((".png",".jpg",".jpeg",".webp")):
                continue

            in_path = os.path.join(OUTPUTS_DIR, file)
            out_path = os.path.join(DOWNLOADS_DIR, file.split('.')[0] + ".mp4")

            if os.path.exists(out_path):
                print(f"SKIP | Already exists: {out_path}")
                continue

            print("\n======================")
            print("Processing:", in_path)

            await asyncio.sleep(3)

            upload_input = None
            for frame in page.frames:
                upload_input = await frame.query_selector('input[type="file"]')
                if upload_input:
                    break

            if not upload_input:
                print("upload input missing.. waiting 5s")
                await asyncio.sleep(5)
                continue

            await upload_input.set_input_files(in_path)
            print("Uploaded ✔")

            btn = await wait_action_btn(page)
            print("Click:", await btn.inner_text())
            await btn.click()

            print("Waiting for Video button…")
            video_btn = await wait_video_ready(page)
            print("Video ready → clicking Video button")
            await video_btn.click()

            print("waiting download icon…")
            dl_btn = await wait_dl_icon(page)
            print("Clicking download icon…")

            # hybrid logic:
            tabs_before = len(context.pages)
            await dl_btn.click()
            await asyncio.sleep(3)

            tabs_after = len(context.pages)

            if tabs_after > tabs_before:
                new_page = context.pages[-1]
                video_url = new_page.url
                print("Video URL:", video_url)

                async with httpx.AsyncClient() as client:
                    r = await client.get(video_url)
                    with open(out_path, "wb") as f:
                        f.write(r.content)
                print("✅ Saved:", out_path)
                await new_page.close()

            else:
                print("🟡 Chrome auto-downloaded file. skip manual download.")

            print("Reload page for next item…")
            await page.goto("https://grok.com/imagine")

        print("\n✅ COMPLETED ALL")

asyncio.run(main())
