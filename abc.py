# import json

# def load_and_update_json():
#     path = r"C:\nemogenai\promptfilenew_all.json"

#     # Load the original JSON
#     with open(path, 'r', encoding='utf-8') as file:
#         data = json.load(file)

#     result = []
#     for obj in data:
#         if obj.get("type") == "array" and "items" in obj:
#             result.extend(obj["items"])
#         else:
#             result.append(obj)

#     # Overwrite the file with the flattened list
#     with open(path, 'w', encoding='utf-8') as file:
#         json.dump(result, file, indent=4, ensure_ascii=False)

#     return result


# # Example usage
# if __name__ == "__main__":
#     updated_data = load_and_update_json()
#     print(f"Flattened {len(updated_data)} entries written back to JSON.")

import os
import re

def get_sorted_output_files(folder_path= r"C:\nemogenai\transcript_folder"):
    """
    Returns a list of file paths from the given folder,
    matching the pattern output_<number>.wav.json,
    sorted by the numeric part of the filename.
    """
    files = []
    pattern = re.compile(r"output_(\d+)\.wav\.json$")

    for filename in os.listdir(folder_path):
        match = pattern.match(filename)
        if match:
            number = int(match.group(1))
            files.append((number, os.path.join(folder_path, filename)))

    # Sort by the numeric part
    files.sort(key=lambda x: x[0])

    # Return only the file paths
    return [f[1] for f in files]


# Example usage
if __name__ == "__main__":
    sorted_files = get_sorted_output_files()
    print(sorted_files)