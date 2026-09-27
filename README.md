# NemoGenAI

Windows scripts that drive a logged-in Chrome window to build a short explainer video:

1. Still images from prompts in Google AI Studio
2. Short clips from those stills on Grok Imagine
3. Narration audio from Google AI Studio speech
4. One merged WAV via ffmpeg
5. Transcripts via Deepgram

There is no single command that runs the whole pipeline. Each step is its own Python file, and several files are older copies of the same step. Use the script named in each section below.

These scripts click live websites. Google AI Studio and Grok change their pages often, so a run can stop on a missing button even when setup is correct. Stay at the machine while a script runs. Do not close the Chrome window it is attached to.

## What you need

- Windows
- Python 3.11
- Google Chrome
- A Google account that can use [AI Studio](https://aistudio.google.com/) image generation and speech generation
- A logged-in [Grok](https://grok.com/imagine) session in that same Chrome profile, for the video step
- A [Deepgram](https://deepgram.com/) API key, for the transcript step
- [ffmpeg](https://ffmpeg.org/) on your `PATH`, for the audio-merge step

## One-time setup

From `C:\nemogenai`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install
```

`requirements.txt` does not include the Deepgram client. Install it only if you will run transcription:

```powershell
pip install deepgram-sdk
```

Confirm ffmpeg:

```powershell
ffmpeg -version
```

## 1. Pick a Chrome profile

```powershell
python chromeprofile.py
```

This prints every local Chrome profile: profile id (`Default`, `Profile 7`, …), display name, and signed-in email. Note the profile id that is already logged into Google AI Studio and Grok.

## 2. Start Chrome with remote debugging

Close every Chrome window first. A normal Chrome process will ignore the debugging port if one is already running.

Replace `Profile 7` with the id from the previous step:

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="$env:LOCALAPPDATA\Google\Chrome\User Data" --profile-directory="Profile 7"
```

Leave that window open. Every generation script attaches to `http://127.0.0.1:9222`. It does not launch its own browser.

Check the port before a run:

```powershell
curl http://127.0.0.1:9222/json/version
```

A JSON blob means Playwright can attach. A connection error means Chrome is not listening on 9222.

## Paths you must edit

Several scripts still point at `C:\langgraphlearn\deep-agents-from-scratch\`, which is not this folder. Edit those paths to `C:\nemogenai` (or wherever you cloned the repo) before running them.

| Script | What to change |
| --- | --- |
| `app.py` | `load_and_update_json()` and `load_from_file()` open `C:\langgraphlearn\deep-agents-from-scratch\promptfilenew_all.json`. Point them at `C:\nemogenai\promptfilenew_all.json`. The image save directory on the `os.makedirs(...)` line is the same old folder; point it at `C:\nemogenai\outputs`. |
| `finalimagegen.py` | Same prompt and output paths as `app.py`. |
| `audio.py` | `fetch_narration()` opens `C:\langgraphlearn\deep-agents-from-scratch\narrationfile.json`. Point it at `C:\nemogenai\narrationfile.json`. |
| `audioplay.py` | Same narration path as `audio.py`. |
| `gettranscript.py` | `AUDIO_FOLDER` and `OUTPUT_FOLDER` use the old tree. Point them at `C:\nemogenai\audio_files` and `C:\nemogenai\transcript_folder`. Replace the hardcoded Deepgram key with your own key. |
| `abc.py` | `get_sorted_output_files()` defaults to `C:\nemogenai\transcript_folder`. Change it if your transcripts live elsewhere. |
| `ffmpeg_helper.py` | Defaults to `C:\nemogenai\audio_files`. Create that folder first, or the script exits as soon as it tries to change into it. |
| `backupapp.py` | `IMAGE_PATH` is a single file under `C:\Users\Debdut\Downloads`. Set it to the still you want to animate. |

`imagegen.py` and `newaudioplay.py` already read files next to the repo (`promptfilenew.json` and `narrationfile.json`).

`app.py` rewrites its prompt JSON on every run. `load_and_update_json()` flattens the file and saves it back in place. Keep a copy of `promptfilenew_all.json` before the first image run.

## Input files

| File | Used by | Shape |
| --- | --- | --- |
| `promptfilenew.json` | `imagegen.py` | JSON list of objects with an `image` string (the prompt) and a `dialogue` string. |
| `promptfilenew_all.json` | `app.py`, `finalimagegen.py` | Same list shape, longer. This is the file the main image script expects after you fix the path. |
| `narrationfile.json` | `newaudioplay.py`, `audio.py`, `audioplay.py` | Object with `narration_list`: a list of `{ "act", "title", "content" }`. Speech scripts read `content`. |
| `promptfile.csv` | nothing in the current entry points | Older comma-separated prompt dump. |
| `promptfile.txt` | nothing | Placeholder. |
| `dialougestructure.json` | nothing | Sample Deepgram transcript, useful as a reference for transcript JSON. |

## Run order

Work from `C:\nemogenai` with the venv active and the debugging Chrome window still open.

### Images

Two scripts do this job. Run one of them.

**`app.py`** is the script that saves image files itself (`generated_0.png`, `generated_1.png`, …). After the path edits above:

```powershell
python app.py
```

What it does:

- Attaches to Chrome on port 9222
- Opens a new Gemini image chat (`gemini-2.5-flash-image`)
- Sets aspect ratio to 16:9
- Fills each `image` prompt, clicks Run or Regenerate, waits until the Stop button is gone, then saves the last `img.loaded-image`
- Starts a fresh chat every 10 prompts

Create `C:\nemogenai\outputs` yourself. The save path inside `send_prompt` is the relative folder `outputs\`, so run the script from `C:\nemogenai` or the PNGs land in whatever directory you launched from.

**`imagegen.py`** reads `C:\nemogenai\promptfilenew.json` and clicks the on-page Download button, so files go to Chrome's download folder rather than `outputs\`. The first prompt is used only to open the chat and set 16:9; generation starts at the second item. Move the downloaded PNGs into `C:\nemogenai\outputs` before the video step.

```powershell
python imagegen.py
```

`finalimagegen.py` is the same flow as `app.py`. Run `app.py` or `finalimagegen.py`, not both, on the same prompt file.

### Video

Put the stills in `C:\nemogenai\outputs` as `.png`, `.jpg`, `.jpeg`, or `.webp`.

```powershell
python genvideo.py
```

For each image that does not already have a matching file in `downloadvideo\`:

- Opens `https://grok.com/imagine`
- Uploads the image
- Clicks Animate / Make video / Generate
- Waits for a Video button, then the download icon
- If a new tab opens, saves that URL as `downloadvideo\<name>.mp4`
- If Chrome downloads the file itself, the script prints that and moves on

`backupapp.py` animates one image (`IMAGE_PATH`) and saves the download under `C:\Users\Debdut\Downloads`. Use it to test a single still. `genvideo.py` is the batch script.

### Narration

`newaudioplay.py` reads `narrationfile.json` from this folder. Use it.

```powershell
python newaudioplay.py
```

It opens AI Studio speech, chooses Single-speaker audio and the voice Sadachbia, pastes each `content` string, presses Ctrl+Enter, waits until the audio source stops changing, and writes `audio_files\output_0.wav` (or `.mp3` / `.ogg`, depending on what the page returns).

`audio.py` and `audioplay.py` do the same job and still point at the old narration path. After you fix that path, any one of the three is enough. Do not run two of them at once against the same Chrome window.

### Merge the WAVs

`ffmpeg_helper.py` only concatenates `.wav` files. If AI Studio returned `.mp3`, convert them first or this step will see an empty folder and stop.

```powershell
python ffmpeg_helper.py
```

It `cd`s into `C:\nemogenai\audio_files`, writes `filelist.txt`, and produces `audio_files\merged_output.wav`. Filenames are sorted alphabetically (`output_0`, `output_1`, `output_10`, …). Rename files to zero-padded names (`output_00`, `output_01`) if you need numeric order past 9.

### Transcripts

Edit `gettranscript.py` so `AUDIO_FOLDER` and `OUTPUT_FOLDER` point at this repo. The script reads the key from the environment. It is not stored in the file.

```powershell
$env:DEEPGRAM_API_KEY = "your-key"
python gettranscript.py
```

Each audio file in the input folder becomes `<filename>.json` in the output folder (Deepgram `nova-3`, smart format).

List those JSON files in numeric order:

```powershell
python abc.py
```

It prints paths matching `output_<number>.wav.json` inside `transcript_folder`. Other extensions are ignored.

## Folders the scripts create or expect

| Folder | Who writes it | Who reads it |
| --- | --- | --- |
| `outputs\` | `app.py` / `finalimagegen.py` (after the path fix, and only if you run from this directory) | `genvideo.py` |
| `downloadvideo\` | `genvideo.py` | you |
| `audio_files\` | `newaudioplay.py`, `audio.py`, `audioplay.py` | `ffmpeg_helper.py`, `gettranscript.py` |
| `transcript_folder\` | `gettranscript.py` | `abc.py` |

## Scripts you can ignore

| File | Why |
| --- | --- |
| `backupapp.py` | Single-image Grok test with a personal download path. |
| `finalimagegen.py` | Duplicate of `app.py`. |
| `audio.py`, `audioplay.py` | Older speech scripts. `newaudioplay.py` is the one wired to this folder. |
| `contents\100mindbreaking\json` | Extra prompt content, not read by the entry points. |

Nothing in this repo starts a web server. `fastapi` and `uvicorn` are listed in `requirements.txt` and are unused by these scripts.

## When a run stops

- **`FileNotFoundError` on `promptfilenew_all.json` or `narrationfile.json`.** The script is still using the `C:\langgraphlearn\...` path. Edit it as in the table above.
- **Playwright cannot connect to `127.0.0.1:9222`.** Chrome was already open, or it was started without `--remote-debugging-port=9222`. Close Chrome and start it with the command in section 2.
- **`TargetClosedError` while waiting for `img.loaded-image`.** The attached tab or the whole Chrome window closed during generation. Leave that window alone until the script prints that it saved the file. This is how the last `app.py` run ended: aspect ratio was set, prompt 0 was submitted, then the page went away before an image loaded.
- **Stop never appears, then the script waits forever on the image.** The Run click did not start a generation (login wall, quota, or a changed button label). Look at the AI Studio tab.
- **`IMAGE_PATH` is not defined.** That name exists only inside unused functions in `app.py` / `finalimagegen.py`. The live call is `googleaistudio()`, which does not need it. `backupapp.py` does define it.
- **`No WAV files found`.** `audio_files` is missing, or the speech step saved `.mp3` files. `ffmpeg_helper.py` only sees `.wav`.
- **`deepgram` import error.** `pip install deepgram-sdk`.
- **Grok upload input missing.** The Imagine page layout changed, or the profile is not logged in. The script waits and skips that file.

Generated media is not in the repo until you run the steps above. A clean checkout has the prompt and narration JSON only.
