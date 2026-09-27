import asyncio
import base64
import json
import os
import re
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# change this to your URL and text
TARGET_URL = "https://aistudio.google.com/generate-speech"
TEXT_TO_SEND = "Hello, debugging click test."
def fetch_narration():
    with open(r"C:\langgraphlearn\deep-agents-from-scratch\narrationfile.json",'r',encoding='utf-8') as file:
        data=json.load(file)
    narration_list= [d['content'] for d in data['narration_list']]
    return narration_list
def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())

async def find_and_click_button(page):
    # 1) Try the nice role-based locator quickly
    try:
        btn = page.get_by_role("button", name="person Single-speaker audio")
        await btn.wait_for(state="visible", timeout=5000)
        await btn.wait_for(state="enabled", timeout=5000)
        await btn.click()
        print("[+] Clicked button via get_by_role locator")
        return True
    except Exception as e:
        print("[!] get_by_role approach failed or timed out:", repr(e))

    # 2) Wait for network idle — sometimes necessary
    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
        print("[i] networkidle reached")
    except Exception:
        print("[i] networkidle not reached or timed out")

    # 3) Gather candidate buttons with the exact class you mentioned
    candidates = page.locator("button.ms-button-borderless.ms-button-active")
    try:
        count = await candidates.count()
    except Exception as e:
        print("[!] Error counting candidates:", e)
        count = 0

    print(f"[i] Found {count} candidate buttons with class 'ms-button-borderless ms-button-active'")

    for i in range(count):
        el = candidates.nth(i)
        inner = await el.inner_text()
        aria = await el.get_attribute("aria-label")
        role_name = None
        try:
            # accessible name might be available via evaluate
            role_name = await page.evaluate("(el) => el.getAttribute('aria-label') || el.innerText", el)
        except Exception:
            role_name = aria
        print(f"  - idx={i} inner_text={repr(inner)[:200]} aria-label={repr(aria)} normalized={repr(normalize_whitespace(inner))}")

        norm = normalize_whitespace(inner).lower()
        if "person" in norm and "single-speaker" in norm.replace("\u2011","-").lower() or "single speaker" in norm:
            print(f"[+] Candidate idx={i} matches by normalized text. Attempting click.")
            try:
                # scroll into view & try normal click first
                await el.scroll_into_view_if_needed()
                await el.click(timeout=5000)
                print(f"[+] Clicked candidate idx={i} via normal click")
                return True
            except Exception as e:
                print(f"[!] Normal click failed for idx={i}: {e}. Trying JS click.")
                try:
                    await page.evaluate("(e) => (e.scrollIntoView(), e.click())", el)
                    print(f"[+] Clicked candidate idx={i} via JS click")
                    return True
                except Exception as e2:
                    print(f"[!] JS click failed for idx={i}: {e2}")

    # 4) Try an XPath that normalizes whitespace and accounts for newline
    try:
        xpath = "//button[contains(normalize-space(.), 'person Single-speaker audio') or contains(normalize-space(.), 'person Single-speaker')]"
        els = page.locator(f"xpath={xpath}")
        xcount = await els.count()
        print(f"[i] XPath matched {xcount} elements")
        if xcount:
            for j in range(xcount):
                e = els.nth(j)
                try:
                    await e.scroll_into_view_if_needed()
                    await e.click()
                    print(f"[+] Clicked element found by XPath (idx {j})")
                    return True
                except Exception as e:
                    print("[!] Click by XPath element failed:", e)
                    try:
                        await page.evaluate("(el) => (el.scrollIntoView(), el.click())", e)
                        print(f"[+] Clicked element found by XPath via JS (idx {j})")
                        return True
                    except Exception as ee:
                        print("[!] JS click for XPath element failed:", ee)
    except Exception as e:
        print("[!] XPath search failed:", e)

    # 5) As a last resort print all buttons (first 200 chars) to help debugging
    all_buttons = page.locator("button")
    try:
        total = await all_buttons.count()
    except Exception:
        total = 0
    print(f"[i] Total buttons on page: {total}")
    sample = min(total, 40)
    for k in range(sample):
        b = all_buttons.nth(k)
        try:
            txt = await b.inner_text()
            cls = await b.get_attribute("class")
            id_ = await b.get_attribute("id")
            print(f"   - btn[{k}] id={id_} class={cls} text={repr(txt)[:200]} normalized={repr(normalize_whitespace(txt))}")
        except Exception as e:
            print(f"   - btn[{k}] read failed: {e}")

    raise RuntimeError("Could not find / click the Single-speaker audio button. See printed candidates above.")

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        print("Page opening...")
        await page.goto(TARGET_URL, timeout=120000)
 
        # Try clicking with robust function
        clicked = False
        try:
            clicked = await find_and_click_button(page)
        except Exception as e:
            print("[ERROR] find_and_click_button raised:", e)

        if not clicked:
            print("[FATAL] Failed to click the Single-speaker button. Inspect printed output above.")
            return

        # Proceed with dropdown selection and rest of flow (same as before)
        print("[i] Opening voice dropdown...")
        dropdown = page.locator("mat-select.mat-mdc-select")
        await dropdown.wait_for(state="visible", timeout=60000)
        await dropdown.click()

        # Try to select option - sometimes options are rendered in overlay, so we search globally
        try:
            option = page.get_by_role("option", name="Sadachbia")
            await option.wait_for(state="visible", timeout=10000)
            await option.click()
            print("[+] Selected Sadachbia via get_by_role")
        except Exception as e:
            print("[!] get_by_role option failed:", e)
            # fallback: locate by text inside overlay
            try:
                opt_locator = page.locator("text=Sadachbia")
                await opt_locator.first.wait_for(state="visible", timeout=10000)
                await opt_locator.first.click()
                print("[+] Selected Sadachbia via text locator")
            except Exception as e2:
                print("[!] Fallback selection failed:", e2)
                raise

        # Textarea
        textarea = page.locator("textarea[placeholder='Start writing or paste text here to generate speech']")
        await textarea.wait_for(state="visible", timeout=30000)
        narration_list=fetch_narration()
        for index,narration in enumerate(narration_list):

            await textarea.click()
            TEXT_TO_SEND=narration_list[index]
            await textarea.fill(TEXT_TO_SEND)
            print("[i] Text filled")

            await textarea.press("Control+Enter")
            print("[i] Pressed Ctrl+Enter")

            # Wait for audio element and save base64
            await page.wait_for_selector("audio", timeout=120000)
            audio_el = page.locator("audio")
            src = await audio_el.get_attribute("src")
            if not src:
                # maybe src is inside source tag
                source_el = audio_el.locator("source")
                src = await source_el.get_attribute("src")
            if not src:
                raise RuntimeError("Audio element found but no src attribute detected.")

            header, b64data = src.split(",", 1)
            audio_bytes = base64.b64decode(b64data)
            ext = "mp3"
            if "wav" in header:
                ext = "wav"
            elif "ogg" in header:
                ext = "ogg"
            folder="audio_files"

            os.makedirs(folder,exist_ok=True)
            
            filename =os.path.join(folder,f"output{index}.{ext}") 
            with open(filename, "wb") as f:
                f.write(audio_bytes)
            print("[+] Audio saved as", filename)

        # don't close browser so you can inspect it
        # await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
