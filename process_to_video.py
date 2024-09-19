import os
import subprocess
import time
import glob

# Configurable variables
NUM_FRAMES = 1000  # Number of frames to process at a time
FFMPEG_ENCODER = 'libx264'  # Encoder to be used
FFMPEG_ARGS = '-crf 12 -preset veryfast -pix_fmt yuv420p'  # Arguments for ffmpeg
FRAME_EXTENSION = 'jpg'  # Change to 'png' if needed
WAIT_TIME = 15  # Time to wait before processing remaining frames

def get_fps(video_path):
    print(f"Getting FPS for video: {video_path}")
    result = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'default=noprint_wrappers=1:nokey=1', video_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    fps = eval(result.stdout.decode('utf-8').strip())
    return fps

def process_frames(current_video_folder, current_video):
    while True:
        # List frames and sort them by number
        frames = sorted(glob.glob(f'{current_video_folder}/frame_*.{FRAME_EXTENSION}'), key=lambda x: int(x.split('_')[-1].split('.')[0]))
        total_frames = len(frames)
        print(f"Found {total_frames} frames in {current_video_folder}")

        if total_frames >= NUM_FRAMES:
            # Process exactly NUM_FRAMES frames
            frames_to_process = frames[:NUM_FRAMES]
            start_number = int(frames_to_process[0].split('_')[-1].split('.')[0])
            video_name = f"{os.path.splitext(os.path.basename(current_video))[0]}_{int(time.time())}.mp4"
            output_path = os.path.join(current_video_folder, video_name)
            fps = get_fps(current_video)
            print(f"Processing {NUM_FRAMES} frames into video {output_path} with FPS {fps}")
            result = subprocess.run(f'ffmpeg -framerate {fps} -start_number {start_number} -i {current_video_folder}/frame_%d.{FRAME_EXTENSION} -frames:v {NUM_FRAMES} -c:v {FFMPEG_ENCODER} {FFMPEG_ARGS} {output_path}', shell=True, capture_output=True, text=True)
            print(f"ffmpeg output: {result.stdout}")
            print(f"ffmpeg error: {result.stderr}")

            if result.returncode != 0:
                print(f"Error encoding video: {result.stderr}")
                break

            # Remove processed frames
            for frame in frames_to_process:
                os.remove(frame)
            print(f"Video {output_path} created and frames deleted.")
        elif total_frames > 0:
            # Handle remaining frames (less than NUM_FRAMES)
            print(f"Waiting for more frames in {current_video_folder}...")
            initial_frame_count = total_frames
            time.sleep(WAIT_TIME)
            frames = sorted(glob.glob(f'{current_video_folder}/frame_*.{FRAME_EXTENSION}'), key=lambda x: int(x.split('_')[-1].split('.')[0]))

            # Process remaining frames if no new ones are added
            if len(frames) == initial_frame_count:
                frames_to_process = frames
                start_number = int(frames_to_process[0].split('_')[-1].split('.')[0])
                video_name = f"{os.path.splitext(os.path.basename(current_video))[0]}_{int(time.time())}_final.mp4"
                output_path = os.path.join(current_video_folder, video_name)
                fps = get_fps(current_video)
                print(f"Processing remaining {len(frames)} frames into video {output_path} with FPS {fps}")
                result = subprocess.run(f'ffmpeg -framerate {fps} -start_number {start_number} -i {current_video_folder}/frame_%d.{FRAME_EXTENSION} -frames:v {len(frames)} -c:v {FFMPEG_ENCODER} {FFMPEG_ARGS} {output_path}', shell=True, capture_output=True, text=True)
                print(f"ffmpeg output: {result.stdout}")
                print(f"ffmpeg error: {result.stderr}")

                if result.returncode != 0:
                    print(f"Error encoding video: {result.stderr}")
                    break

                # Remove remaining frames
                for frame in frames_to_process:
                    os.remove(frame)
                print(f"Video {output_path} created and remaining frames deleted.")
                break
        else:
            print(f"No frames found in {current_video_folder}. Waiting...")
            time.sleep(WAIT_TIME)

if __name__ == "__main__":
    if not os.path.exists('output'):
        os.makedirs('output')

    current_video = ""
    current_video_folder = ""

    # Run the batch script in a separate terminal (Make sure 'batch.py' is running correctly)
    subprocess.Popen(['start', 'cmd', '/k', 'python batch.py'], shell=True)

    # Monitor the batch output for new video
    while True:
        if os.path.exists('batch_output.txt'):
            with open('batch_output.txt', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    decoded_line = line.strip()
                    print(f"Batch output: {decoded_line}")
                    if "Current working on:" in decoded_line:
                        new_video = decoded_line.split(": ")[1]
                        new_video_folder = os.path.join('output', os.path.splitext(os.path.basename(new_video))[0])
                        if new_video_folder != current_video_folder:
                            current_video = new_video
                            current_video_folder = new_video_folder
                            print(f"Current video: {current_video}")
                            print(f"Current video folder: {current_video_folder}")
                            process_frames(current_video_folder, current_video)
        else:
            print("batch_output.txt not found. Waiting...")
        time.sleep(1)
