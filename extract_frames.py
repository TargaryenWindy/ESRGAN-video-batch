import cv2
import os
import json
import shutil
from concurrent.futures import ThreadPoolExecutor

# Variables to set
frames_per_run = 1000
num_folders = 1
frame_format = 'jpg'  # Change to 'png' or other formats if needed
jpeg_quality = 90  # Quality for JPEG format (1-100)
num_threads = 32  # Number of threads to use


def save_frame(frame, frame_filename):
    if frame_format == 'jpg':
        cv2.imwrite(frame_filename, frame, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality])
    else:
        cv2.imwrite(frame_filename, frame)
    print(f"Extracted frame to {frame_filename}")


def extract_frames(video_path):
    # Load or initialize the progress file
    progress_file = 'progress.json'
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            progress = json.load(f)
    else:
        progress = {}

    # Get the last frame number extracted for this video
    last_frame = progress.get(video_path, 0)
    print(f"Last frame extracted: {last_frame}")

    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    # Get the total number of frames in the video
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Total frames in video: {total_frames}")

    # Check if the last frame is beyond the total frames
    if last_frame >= total_frames:
        print("Error: Last frame extracted exceeds total frames in video.")
        return

    cap.set(cv2.CAP_PROP_POS_FRAMES, last_frame)

    # Calculate frames per folder
    frames_per_folder = frames_per_run // num_folders

    # Clean old frames or create folders if they don't exist
    for i in range(num_folders):
        folder_name = f'batch_{i + 1}'
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)
        os.makedirs(folder_name)
    print("Folders cleaned and created.")

    # Extract frames
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(frames_per_run):
            ret, frame = cap.read()
            if not ret:
                print("Finished extracting frames.")
                break

            folder_index = ((last_frame + i) % frames_per_run) // frames_per_folder
            folder_name = f'batch_{folder_index + 1}'
            frame_filename = os.path.join(folder_name, f'frame_{last_frame + i}.{frame_format}')

            futures.append(executor.submit(save_frame, frame, frame_filename))

        for future in futures:
            future.result()

    # Update the progress file
    progress[video_path] = last_frame + frames_per_run
    with open(progress_file, 'w') as f:
        json.dump(progress, f)
    print("Progress updated.")

    cap.release()


if __name__ == "__main__":
    video_path = input("Enter the path to the video file: ")
    extract_frames(video_path)
