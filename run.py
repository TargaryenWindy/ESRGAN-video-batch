import os
import time
import subprocess
import threading
import shutil


def run_process_to_video():
    subprocess.run(['python', 'process_to_video.py'])


def get_sorted_videos(folder):
    videos = [os.path.join(folder, f) for f in os.listdir(folder) if
              f.endswith('.mp4') and not f.endswith('_final.mp4')]
    videos.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))  # Sort by timestamp or random number
    return videos


def concatenate_videos_ffmpeg(videos, output_path):
    with open('file_list.txt', 'w') as f:
        for video in videos:
            if os.path.exists(video):
                f.write(f"file '{video}'\n")
            else:
                print(f"Warning: {video} does not exist and will be skipped.")
    subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'file_list.txt', '-c', 'copy', output_path])
    os.remove('file_list.txt')


def process_folder(folder):
    videos = get_sorted_videos(folder)
    final_video = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('_final.mp4')]
    if final_video:
        final_video_path = final_video[0]

        # Add delay to ensure the final video file is fully written
        print(f"Final video detected: {final_video_path}. Waiting for 10 seconds to ensure it is fully written...")
        time.sleep(10)

        fixed_final_video_path = final_video_path.replace('.mp4', '_fixed.mp4')

        # Fix moov atom issue in final video
        subprocess.run(
            ['ffmpeg', '-i', final_video_path, '-c', 'copy', '-movflags', 'faststart', fixed_final_video_path])

        # Concatenate all pieces including the final fixed piece
        output_path = os.path.join(folder, f"{os.path.basename(folder)}.mp4")
        concatenate_videos_ffmpeg(videos + [fixed_final_video_path], output_path)

        # Clean up original video parts
        for video in videos + [fixed_final_video_path]:
            try:
                os.remove(video)
            except OSError as e:
                print(f"Error deleting file {video}: {e}")

        return output_path
    return None


def merge_with_upscale(video_path, upscale_folder):
    video_name = os.path.basename(video_path)

    # Check if the video in upscale folder is mp4 or mkv
    upscale_video_mp4 = os.path.join(upscale_folder, video_name.replace('.mp4', '.mp4'))
    upscale_video_mkv = os.path.join(upscale_folder, video_name.replace('.mp4', '.mkv'))

    if os.path.exists(upscale_video_mp4):
        upscale_video_path = upscale_video_mp4
    elif os.path.exists(upscale_video_mkv):
        upscale_video_path = upscale_video_mkv
    else:
        print(f"Upscale video not found for {video_name}")
        return

    output_path = video_path.replace('.mp4', '_merged.mkv')  # Ensure output is in .mkv format

    # Merge audio/subs from the upscale video using mkvmerge
    subprocess.run(['mkvmerge', '-o', output_path, '--no-video', upscale_video_path, video_path])

    # Replace the concatenated video with the merged version
    os.remove(video_path)
    os.rename(output_path, video_path.replace('.mp4', '.mkv'))  # Rename to .mkv


def move_file_to_output(final_video_path):
    # Get the base name of the video file and the output directory
    output_folder = 'output'
    base_name = os.path.basename(final_video_path)

    # New final path in the output folder
    new_final_path = os.path.join(output_folder, base_name)

    # Move the file to the output directory
    shutil.move(final_video_path, new_final_path)

    # Delete the folder it was in
    folder_to_delete = os.path.dirname(final_video_path)
    if os.path.exists(folder_to_delete) and os.path.isdir(folder_to_delete):
        shutil.rmtree(folder_to_delete)

    print(f"Moved {base_name} to {output_folder} and deleted the folder {folder_to_delete}.")


def monitor_output_folder():
    output_folder = 'output'
    upscale_folder = 'videos_to_upscale'
    processed_folders = set()

    while True:
        for folder in os.listdir(output_folder):
            folder_path = os.path.join(output_folder, folder)
            if os.path.isdir(folder_path) and folder_path not in processed_folders:
                concatenated_video = process_folder(folder_path)
                if concatenated_video:
                    merge_with_upscale(concatenated_video, upscale_folder)

                    # After merging, move the final video to the output directory and delete the original folder
                    final_video_mkv = concatenated_video.replace('.mp4', '.mkv')
                    move_file_to_output(final_video_mkv)

                    processed_folders.add(folder_path)
        time.sleep(10)


def main():
    process_thread = threading.Thread(target=run_process_to_video)
    monitor_thread = threading.Thread(target=monitor_output_folder)

    process_thread.start()
    monitor_thread.start()

    process_thread.join()
    monitor_thread.join()


if __name__ == '__main__':
    main()
