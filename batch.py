import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import threading

# Define the model name variable
model_name = "realesr-animevideov3-x2"

# Set to track the folders currently being processed
processing_folders = set()
lock = threading.Lock()  # Lock to prevent race conditions

# Function to run the Real-ESRGAN binary on a batch folder
def run_realesrgan(batch_folder, output_folder):
    command = f'realesrgan-ncnn-vulkan -i "{batch_folder}" -o "{output_folder}" -s 2 -t 1920 -f jpg -j 4:4:4 -n {model_name}'
    print(f"Running command: {command}")
    subprocess.run(command, shell=True)

# Function to process a batch folder
def process_batch_folder(batch_folder, output_folder):
    # Skip processing if the folder is already being processed
    with lock:
        if batch_folder in processing_folders:
            print(f"Skipping {batch_folder}, already being processed.")
            return
        processing_folders.add(batch_folder)

    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        run_realesrgan(batch_folder, output_folder)

    finally:
        # Remove from processing_folders when done
        with lock:
            processing_folders.remove(batch_folder)

# Function to process a video
def process_video(video_path):
    print(f"Processing video: {video_path}")

    # Write the current working file to batch_output.txt
    with open('batch_output.txt', 'w') as f:
        f.write(f"Current working on: {video_path}\n")

    # Create a new folder inside the output folder with the same name as the file
    output_folder = os.path.join('output', os.path.splitext(os.path.basename(video_path))[0])
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Run the extract_frames script and capture the output
    try:
        result = subprocess.run(['python', 'extract_frames.py'], input=video_path, text=True, capture_output=True, encoding='latin-1')
        print(f"Extract frames output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error running extract_frames.py: {e}")
        return False

    # Check if stdout has content and proceed
    if result.stdout is None:
        print("No output received from extract_frames.py.")
        return False

    # Get the list of batch folders
    batch_folders = [f for f in os.listdir() if f.startswith("batch_")]
    print(f"Batch folders: {batch_folders}")

    # Process remaining batch folders if "Finished extracting frames" is received
    with ThreadPoolExecutor() as executor:
        if "Finished extracting frames" in result.stdout:
            print("Frame extraction finished.")
            executor.map(lambda folder: process_batch_folder(folder, output_folder), batch_folders)
            return False  # End processing when all frames are processed

    # Process batch folders in parallel using ThreadPoolExecutor for partial extraction
    with ThreadPoolExecutor() as executor:
        executor.map(lambda folder: process_batch_folder(folder, output_folder), batch_folders)

    return True

# Main loop to process videos
processed_videos = set()
videos_folder = "videos_to_upscale"

while True:
    videos = [os.path.join(videos_folder, f) for f in os.listdir(videos_folder) if f.endswith((".mp4", ".mkv"))]
    for video in videos:
        if video not in processed_videos:
            # Process the video until all frames are done
            while process_video(video):
                pass

            # Mark video as processed
            processed_videos.add(video)
