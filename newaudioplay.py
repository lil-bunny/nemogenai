import asyncio
import base64
import json
import os
import time
from playwright.async_api import async_playwright

TARGET_URL = "https://aistudio.google.com/generate-speech"


import os, json
import sys
sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace", buffering=1)
def fetch_narration():
    """Load narration text from narrationfile.json (always relative to this script's folder)."""
    base_dir = os.path.dirname(os.path.abspath(__file__))   # folder where newaudioplay.py lives
    path = os.path.join(base_dir, "narrationfile.json") 
    print(path)    # narrationfile.json in same folder
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        narration_list = [d["content"] for d in data["narration_list"]]
        return narration_list


# ---------------------------
# WAIT UNTIL GENERATION COMPLETES
# ---------------------------
async def wait_for_generation_complete(page):
    """
    Logic:
    1. Wait for STOP button to appear (if it appears)
    2. Wait for STOP to disappear (real signal of finished)
    3. Then poll audio.src until stable
    """

    print("     Waiting for generation to start...")

    stop_btn = page.locator("button:has-text('Stop')")

    # STEP 1: Wait for STOP button to appear (BUT don't fail if it doesn't)
    try:
        await stop_btn.wait_for(state="visible", timeout=15000)
        print("   Stop button appeared (generation started)")
    except Exception:
        print("     Stop button did not appear (maybe super fast generation)")

    print("    Waiting for Stop to disappear...")

    # STEP 2: Wait for STOP to disappear → generation finished
    try:
        await stop_btn.wait_for(state="hidden", timeout=300000)  # up to 5 min
        print("    Stop button disappeared (generation finished)")
    except Exception:
        print("     Stop did not disappear but continuing...")

    # STEP 3: Wait for audio.src to stabilize
    print("    Waiting for audio src to stabilize...")

    previous_src = None
    stable_count = 0
    start = time.time()

    while True:
        if time.time() - start > 400:  # ~6+ minutes timeout
            raise TimeoutError("Audio generation took too long")

        src = await page.evaluate(
            """() => {
                const a = document.querySelector("audio");
                if (!a) return null;
                return a.currentSrc || a.src || a.getAttribute("src");
            }"""
        )

        # if no base64 yet → wait
        if not src or "base64," not in src:
            await asyncio.sleep(0.4)
            continue

        # check stability
        if src == previous_src:
            stable_count += 1
        else:
            stable_count = 0
            previous_src = src

        # stable for 3 cycles → done
        if stable_count >= 3:
            print("     Audio src stable.")
            return src

        await asyncio.sleep(0.4)


# ---------------------------
# MAIN FUNCTION
# ---------------------------
async def run():
    async with async_playwright() as p:
        # Connect to existing Chromium instance
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(TARGET_URL, timeout=120000)

        # Click Single-speaker audio
        speaker_btn = page.locator("button:has-text('Single-speaker')")
        await speaker_btn.wait_for(state="visible")
        await speaker_btn.click()

        # Select voice → specifically Sadachbia
# Select voice → Sadachbia
        voice_dropdown = page.locator("mat-select.mat-mdc-select").nth(0)
        await voice_dropdown.wait_for(state="visible")
        await voice_dropdown.click()
        await page.locator("mat-option:has-text('Sadachbia')").click()
        # Narration textarea
        textarea = page.locator("textarea[placeholder*='Start writing']")
        await textarea.wait_for(state="visible")

        narrations = fetch_narration()
        os.makedirs("audio_files", exist_ok=True)

        for idx, narration in enumerate(narrations):
            print(f"\n\n==================== GENERATING {idx} ====================")

            await textarea.fill(narration)
            await textarea.press("Control+Enter")

            # WAIT UNTIL GENERATION COMPLETES
            src = await wait_for_generation_complete(page)

            # Decode audio
            header, b64data = src.split(",", 1)
            audio_bytes = base64.b64decode(b64data)

            ext = "mp3"
            if "wav" in header.lower():
                ext = "wav"
            if "ogg" in header.lower():
                ext = "ogg"
# Choose whichever base path you want:
            base_path = os.getcwd()  # or dirname(abspath(__file__)) or expanduser("~")

            save_dir = os.path.join(base_path, "audio_files")
            os.makedirs(save_dir, exist_ok=True)

            filename = os.path.join(save_dir, f"output_{idx}.{ext}")
            with open(filename, "wb") as f:
                f.write(audio_bytes)

            print(f"     Saved: {filename}")
            print("\n🎉 DONE: All audio generated!")

            # filename = f"audio_files/output_{idx}.{ext}"
            # with open(filename, "wb") as f:
            #     f.write(audio_bytes)

            print(f"Saved: {filename}")

        print("\n🎉 DONE: All audio generated!")


if __name__ == "__main__":
    asyncio.run(run())