
import os
import json
from deepgram import DeepgramClient

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "").strip()

def transcribe_folder(audio_folder, output_folder):
    if not DEEPGRAM_API_KEY:
        raise SystemExit("Set the DEEPGRAM_API_KEY environment variable.")

    deepgram = DeepgramClient(api_key=DEEPGRAM_API_KEY)
    os.makedirs(output_folder, exist_ok=True)

    audio_files = sorted([
        f for f in os.listdir(audio_folder)
        if f.lower().endswith((".mp3", ".wav", ".m4a", ".flac"))
    ])

    for filename in audio_files:
        audio_path = os.path.join(audio_folder, filename)
        print(f"=== Transcribing: {filename} ===")

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        # Transcribe file using Deepgram v5 API
        response = deepgram.listen.v1.media.transcribe_file(
            request=audio_bytes,
            model="nova-3",
            smart_format=True
        )

        # Convert Pydantic object → JSON string
        json_str = response.model_dump_json(indent=4)

        # Save to file
        out_path = os.path.join(output_folder, filename + ".json")
        with open(out_path, "w", encoding="utf-8") as out:
            out.write(json_str)

        print(f"Saved  {out_path}")

    print(" All files transcribed successfully!")



# -----------------------------
# Run the script
# -----------------------------
if __name__ == "__main__":
    # Your new folder with audio files
    AUDIO_FOLDER = r"C:\langgraphlearn\deep-agents-from-scratch\audio_files"
    
    # Where to save JSON transcript outputs
    OUTPUT_FOLDER = r"C:\langgraphlearn\deep-agents-from-scratch\transcript_folder"
    
    transcribe_folder(AUDIO_FOLDER, OUTPUT_FOLDER)