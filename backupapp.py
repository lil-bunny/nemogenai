import asyncio
from playwright.async_api import async_playwright
import os
IMAGE_PATH = r"C:\Users\Debdut\Downloads\testimage.png"

async def main():
    async with async_playwright() as p:
        # Connect to running Chrome with your profile
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto("https://grok.com/imagine")
        await page.wait_for_load_state("networkidle")

        # Find file input (could be hidden)
        upload_input = await page.query_selector('input[type="file"]')
        if not upload_input:
            print("❌ Could not find file input!")
            await browser.close()
            return

        # Upload the image
        await upload_input.set_input_files(IMAGE_PATH)
        print("📤 Image uploaded!")

        # Wait for video creation progress to reach 100%
        progress_locator = page.locator("div.text-xs.font-semibold")  # generic enough
        print("⏳ Waiting for video to finish...")
        progress_locator = page.locator("div.text-xs.font-semibold")
        print("⏳ Waiting for video to start...")

        # Wait until the progress element appears at least once
        await progress_locator.wait_for(state="visible", timeout=10000)  # 10s max, adjust if needed

        print("⏳ Progress started, monitoring...")

        while True:
            count = await progress_locator.count()
            
            if count == 0:
                # Element vanished after appearing
                print("✅ Progress indicator vanished — Complete")
                break

            progress_text = await progress_locator.first.inner_text()
            print(f"Progress: {progress_text}")

            if "100%" in progress_text:
                print("✅ 100% reached — Complete")
                break

            await asyncio.sleep(1)
        # Click the download button (SVG inside a button)

        print("✅ Download clicked!")
        download_dir = r"C:\Users\Debdut\Downloads"  # your folder
        os.makedirs(download_dir, exist_ok=True)

        # Wait for the download event when clicking the button
        async with page.expect_download() as download_info:
            download_button = page.locator('button[aria-label="Download"]:visible')
            await download_button.click()

        download = await download_info.value

        # Save the file in the Downloads folder
        save_path = os.path.join(download_dir, download.suggested_filename)
        await download.save_as(save_path)

        print(f"✅ Download saved to: {save_path}")

        # download_button_handle = await page.query_selector("svg.lucide-download")
        # if download_button_handle:
        #     parent_button = await download_button_handle.evaluate_handle("node => node.closest('button')")
        #     if parent_button:
        #         await parent_button.click()
        #         print("✅ Download clicked!")

        await asyncio.sleep(5)  # optional: wait for file to finish downloading
        await browser.close()

asyncio.run(main())
