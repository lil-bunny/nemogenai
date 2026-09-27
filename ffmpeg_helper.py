import os
import subprocess

folder_path = r"C:\nemogenai\audio_files"
output_file = "merged_output.wav"

def merge_wavs_sequential(folder_path=r"C:\nemogenai\audio_files", output= "merged_output.wav"):
    # Go to folder
    os.chdir(folder_path)

    # Get sorted .wav files
    wav_files = sorted([f for f in os.listdir('.') if f.lower().endswith('.wav')])

    if not wav_files:
        print("No WAV files found in folder!")
        return

    # Create filelist.txt
    with open("filelist.txt", "w") as f:
        for file in wav_files:
            f.write(f"file '{file}'\n")

    # FFmpeg command
    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", "filelist.txt",
        "-c", "copy",
        output
    ]

    print("Running:", " ".join(cmd))
    subprocess.run(cmd)

    print(f"Done! Merged file created at: {os.path.join(folder_path, output)}")


merge_wavs_sequential(folder_path)
