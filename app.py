import json
import os
from playwright.async_api import async_playwright
import asyncio, base64
import csv

import os, json
import sys
sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace", buffering=1)

TEXTAREA      = "//ms-autosize-textarea//textarea"
RUN_OR_REGEN  = "//span[normalize-space()='Run'] | //span[normalize-space()='Regenerate']"
STOP_BTN      = "//span[normalize-space()='Stop']"
IMAGE_LOCATOR = "img.loaded-image"

async def wait_for_run_cycle(page, timeout_ms=180000):
    stop = page.locator(STOP_BTN)

    # wait until running starts (Stop appears)
    try:
        await stop.wait_for(state="visible", timeout=15000)
        print("[LOG] Stop Visible -> Model running…")
    except:
        print("[LOG] Stop didn’t appear (maybe fast response)")

    # wait until running ends (Stop disappears)
    try:
        await stop.wait_for(state="hidden", timeout=timeout_ms)
        print("[LOG] Stop Hidden -> Run finished")
    except:
        print("[WARN] Stop didn’t hide timely")

    # settle time
    await page.wait_for_timeout(1000)

    print("[LOG] waiting until model ready (Run/Regenerate)…")
    await page.wait_for_selector(RUN_OR_REGEN, timeout=60000)
    print("[LOG] model ready -> button back!")

async def send_prompt(page, text, index):
    print(f"\n=== Prompt {index} ===")

    await page.wait_for_selector(TEXTAREA, timeout=60000)
    await page.locator(TEXTAREA).fill("")
    await page.fill(TEXTAREA, text)

    print("[LOG] Clicking RUN/REGENERATE…")
    await page.locator(RUN_OR_REGEN).first.click()

    await wait_for_run_cycle(page)

    print("[LOG] Waiting for generated image…")
    await page.wait_for_selector(IMAGE_LOCATOR, timeout=9000000)

    img_locator = page.locator(IMAGE_LOCATOR).nth(-1)
    print(img_locator)
    img = await img_locator.element_handle()

    print("[LOG] Image element found, verifying load…")

    # Wait until image fully loads (no half-visible)
    await page.wait_for_function(
        "(el) => el && el.complete && el.naturalWidth > 0",
        arg=img,                               # <-- Locator NOT valid. ElementHandle is required.
        timeout=9000000
    )

    
    src = await img.get_attribute("src") or ""

    os.makedirs("C:\langgraphlearn\deep-agents-from-scratch\outputs", exist_ok=True)
    filename = f"generated_{index}.png"
    filepath = os.path.join("outputs", filename)

    if not src:

        print("[WARN] <img> has no src; taking element screenshot")
        await img.screenshot(path=filepath)
        print(f"[LOG]  saved (screenshot) {filepath}")
        return

    print("[LOG] Image src detected:", src[:80])

    try:
        if src.startswith("data:image"):
            print("[LOG] Detected base64 image")
            base64_data = src.split(",", 1)[1]
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(base64_data))

        elif src.startswith("blob:"):
            print("[LOG] Detected blob URL; fetching via page context")
            # Fetch in the page (has access to blob URL), return bytes as a list of ints
            byte_list = await page.evaluate("""
                async (img) => {
                    const res = await fetch(img.src);
                    const buf = await res.arrayBuffer();
                    return Array.from(new Uint8Array(buf));
                }
            """, img)
            with open(filepath, "wb") as f:
                f.write(bytes(byte_list))

        elif src.startswith("http://") or src.startswith("https://"):
            print("[LOG] Detected HTTP image URL")
            resp = await page.context.request.get(src)
            if not resp.ok:
                raise RuntimeError(f"HTTP fetch failed: {resp.status} {await resp.text()}")
            content = await resp.body()
            with open(filepath, "wb") as f:
                f.write(content)

        else:
            print(f"[WARN] Unknown src scheme ({src[:20]}…). Falling back to element screenshot.")
            await img.screenshot(path=filepath)

        print(f"[LOG] saved {filepath}")

    except Exception as e:
        print(f"[WARN] Fetch/save failed ({e}). Falling back to element screenshot.")
        await img.screenshot(path=filepath)
        print(f"[LOG]  saved (screenshot) {filepath}")


def fetch_prompts():
    finalpromptlist=[]
    with open(r"C:\langgraphlearn\deep-agents-from-scratch\promptfilenew_all.json",mode='r') as file:
        reader=csv.reader(file)
        
        for row in reader:
         
            for i in row:
                if i=='':
                    continue
                finalpromptlist.append(i)
    return finalpromptlist                


def load_and_update_json():
    path = r"C:\langgraphlearn\deep-agents-from-scratch\promptfilenew_all.json"

    # Load the original JSON
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    result = []
    for obj in data:
        if "items" in obj:
            result.extend(obj["items"])
        else:
            result.append(obj)

    # Overwrite the file with the flattened list
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

    return result
def load_from_file():
    path = r"C:\langgraphlearn\deep-agents-from-scratch\promptfilenew_all.json"
    with open(path, 'r') as file:
        data = json.load(file)
    return data

# print(fetch_prompts())



# async def googleaistudio( ):
#     is_newprocess=True

#     prompts =load_from_file()

    
#     print("Launching Google AI Studio Automation…",len(prompts))

#     async with async_playwright() as p:
#         for i,prompt in enumerate(prompts):
#             if(is_newprocess):
#                 browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
#                 context = browser.contexts[0]
#                 page = context.pages[-1]


#                 await page.goto("https://aistudio.google.com/prompts/new_chat?model=gemini-2.5-flash-image")

#                 await page.wait_for_timeout(5000)

#                 # login continue
#                 if await page.locator("text=Continue").is_visible():
#                     await page.locator("text=Continue").click()

#                 # set Aspect Ratio first
#                 print("[LOG] Setting Aspect Ratio 16:9...")
#                 await page.locator("//mat-select[@aria-label='Aspect ratio']").click()
#                 await page.wait_for_selector("//span[@class='mdc-list-item__primary-text' and normalize-space()='16:9']", timeout=5000)
#                 await page.locator("//span[@class='mdc-list-item__primary-text' and normalize-space()='16:9']").click()
#                 print("[LOG] Aspect Ratio set ✅")
#                 is_newprocess=False
#         # run prompts sequentially
#             else:
                
#                 await send_prompt(page, prompt['image'], i)
#                 if 'act' in prompt:
#                     print("Finished act =",prompt['act'])
#                     is_newprocess=True
                

#     print("\n✅ ALL PROMPTS DONE")


async def googleaistudio( ):
    is_newprocess=True
    prompts=load_and_update_json()
    # prompts =load_from_file()

    
    print("Launching Google AI Studio Automation…",len(prompts))

    async with async_playwright() as p:
       
          

            
        # run prompts sequentially
            
            for i,prompt in enumerate(prompts): 
                if(is_newprocess):
                    browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                    context = browser.contexts[0]
                    page = context.pages[-1]
        

                    await page.goto("https://aistudio.google.com/prompts/new_chat?model=gemini-2.5-flash-image")

                    await page.wait_for_timeout(5000)

                    # login continue
                    if await page.locator("text=Continue").is_visible():
                        await page.locator("text=Continue").click()

                    # set Aspect Ratio first
                    print("[LOG] Setting Aspect Ratio 16:9...")
                    await page.locator("//mat-select[@aria-label='Aspect ratio']").click()
                    await page.wait_for_selector("//span[@class='mdc-list-item__primary-text' and normalize-space()='16:9']", timeout=5000)
                    await page.locator("//span[@class='mdc-list-item__primary-text' and normalize-space()='16:9']").click()
                    print("[LOG] Aspect Ratio set ")
                    is_newprocess=False
                print(f"{prompt['image']} {i} len{len(prompts)}");               
                await send_prompt(page, prompt['image'], i)
                if(i%10==0):
                    is_newprocess=True
           
                

    print(" ALL PROMPTS DONE")


# asyncio.run(googleaistudio())
async def run():
    async with async_playwright() as p:

        # Connect to your existing Chrome
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")

        # Use existing context or new page
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        # Go to your target site
        await page.goto("https://aistudio.google.com/generate-speech", timeout=120000)
        print("Page opened.")

        # =========================
        # WAIT FOR SINGLE-SPEAKER BUTTON
        # =========================

        # This is the correct locator for:
        # "person\nSingle-speaker audio"  →  "person Single-speaker audio"
        button = page.get_by_role("button", name="person Single-speaker audio")

        print("Waiting for Single-speaker audio button...")

        await button.wait_for(state="attached", timeout=90000)
        await button.wait_for(state="visible", timeout=90000)
        await button.wait_for(state="enabled", timeout=90000)

        await button.click()
        print("Clicked: Single-speaker audio")

        # =========================
        # SELECT VOICE (Sadachbia)
        # =========================
        
        dropdown = page.locator("mat-select.mat-mdc-select")
        await dropdown.wait_for(state="visible", timeout=60000)
        await dropdown.click()
        print("Dropdown opened.")

        option = page.get_by_role("option", name="Sadachbia")
        await option.wait_for(state="visible", timeout=30000)
        await option.click()
        print("Voice selected: Sadachbia")

        # =========================
        # TYPE TEXT
        # =========================

        textarea = page.locator(
            "textarea[placeholder='Start writing or paste text here to generate speech']"
        )

        await textarea.wait_for(state="visible", timeout=30000)
        await textarea.click()
        
        text_to_send = "Hello, this is the final updated Playwright script test."
        await textarea.fill(text_to_send)
        print("Text entered.")

        # =========================
        # PRESS CTRL + ENTER
        # =========================

        await textarea.press("Control+Enter")
        print("Triggered Generate (Ctrl + Enter)")

        # =========================
        # WAIT FOR AUDIO ELEMENT
        # =========================

        print("Waiting for audio element to appear...")

        await page.wait_for_selector("audio", timeout=120000)
        audio_el = page.locator("audio")

        src = await audio_el.get_attribute("src")
        print("Audio base64 detected.")

        # =========================
        # DECODE BASE64 AUDIO
        # =========================

        header, b64data = src.split(",", 1)
        audio_bytes = base64.b64decode(b64data)

        # Auto-detect file extension
        if "wav" in header:
            ext = "wav"
        elif "ogg" in header:
            ext = "ogg"
        else:
            ext = "mp3"

        filename = f"output.{ext}"

        with open(filename, "wb") as f:
            f.write(audio_bytes)

        print(f"Audio saved successfully → {filename}")


        # Keep Chrome open. Don't close.
        # await browser.close()

# asyncio.run(run())


async def main():
    async with async_playwright() as p:
        # Connect to running Chrome with your logged-in profile
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")

        # Use existing context or create new
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()

        # Go to Grok Imagine page
        await page.goto("https://grok.com/imagine")
        await page.wait_for_load_state("networkidle")  # wait for full page load

        # Look for the hidden file input in all frames
        frames = page.frames
        upload_input = None
        for frame in frames:
            upload_input = await frame.query_selector('input[type="file"]')
            if upload_input:
                break

        if not upload_input:
            print("❌ Could not find file input!")
            await browser.close()
            return

        # Upload the image
        await upload_input.set_input_files(IMAGE_PATH)

        # Click Animate button
        animate_button = await page.wait_for_selector('button:has-text("Animate")', timeout=30000)
        await animate_button.click()

        # Wait for Video button (animation completion)
        await page.wait_for_selector('button:has-text("Video")', timeout=60000)

        print("✅ Image uploaded and animated successfully!")

        # Optional: keep browser open for 5 seconds to check result
        await asyncio.sleep(5)
        await browser.close()

asyncio.run(googleaistudio())
# asyncio.run(run())


def extract_all_acts_with_intro(data):
    result = []
    current_act = None
    narration = []

    for item in data:
        if 'act' in item:
            # If this is the first act, assign all previous narration to it
            if current_act is None:
                current_act = item['act']
                if 'dialogue' in item:
                    narration.append(item['dialogue'])
            else:
                # Save the previous act block
                result.append({
                    "act": current_act,
                    "narration": " ".join(narration)
                })
                # Start new act
                current_act = item['act']
                narration = [item.get('dialogue', '')]
        else:
            if 'dialogue' in item:
                narration.append(item['dialogue'])

    # Save the final act block
    if current_act:
        result.append({
            "act": current_act,
            "narration": " ".join(narration)
        })

    return result

# final_data=extract_all_acts_with_intro(data=load_from_file())
# with open("narrationfile.json","w") as file:
#     json.dump(final_data, file, indent=4)
