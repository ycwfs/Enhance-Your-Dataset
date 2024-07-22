import os
import cv2
import json
import random
import numpy as np
import threading

# Define global variables
n = 1  # Global variable to track video number
lock_n = threading.Lock()  # Lock for accessing the global variable n

combinations = [
    (['bg', 'ac', 'bg'], 2),  # Sequence and count of background clips
    (['ac', 'bg', 'bg'], 2),
    (['bg', 'bg', 'ac'], 2)
]
combinations_2 = [
    (['bg', 'ac'], 1),
    (['ac', 'bg'], 1),
]

# Define a function to process each video segment
def process_video_segment(segment_keys, al, background_segments, output_video_path_template, anno_json, lock):
    global n  # Access the global variable n
    for vc in segment_keys:
        for _ in range(10):
            vn = random.choice(list(al[vc].keys()))
            if vn == 'subset':
                continue
            ac = random.choice(al[vc][vn])
            bg_count = random.choices([1,2],weights=[0.5,0.5])
            action_cap = cv2.VideoCapture('resized_videos/' + vn + '.mp4')
            fps = action_cap.get(cv2.CAP_PROP_FPS)
            start_frame = int(ac[0] * fps)
            end_frame = int(ac[1] * fps)
            action_cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            ac_buffer = []
            for j in range(start_frame, end_frame):
                ret, frame = action_cap.read()
                if not ret:
                    break
                ac_buffer.append(frame)
            if len(ac_buffer) > 0:
                ac_buffer = np.stack(ac_buffer)

            bgs_buffer = []
            for _ in range(bg_count[0]):
                bn = random.choice(list(background_segments.keys()))
                bg = random.choice(background_segments[bn])
                bg_cap = cv2.VideoCapture('resized_videos/' + bn + '.mp4')
                fps = bg_cap.get(cv2.CAP_PROP_FPS)
                start_frame = int(bg[0] * fps)
                end_frame = int(bg[1] * fps)
                bg_cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                bg_buffer = []
                for j in range(start_frame, end_frame):
                    ret, frame = bg_cap.read()
                    if not ret:
                        break
                    bg_buffer.append(frame)
                if len(bg_buffer) > 0:
                    bg_buffer = np.stack(bg_buffer)
                    bgs_buffer.append(bg_buffer)

            if len(bgs_buffer) != bg_count[0]:
                i = i - 1
                continue
        
            # combine, random [bg,ac,bg] [bg,ac] [ac,bg] [ac,bg,bg] [bg,bg,ac]
            if len(bgs_buffer) == 2:
            # Randomly select a combination
                chosen_combo, bg_counts = random.choice(combinations)
            elif len(bgs_buffer) == 1:
                chosen_combo, bg_counts = random.choice(combinations_2)
            combined_buffer = []

            # Combine the sequences based on the chosen combination
            bg_index = 0
            for segment in chosen_combo:
                if segment == 'ac':
                    # Add action frames
                    combined_buffer.extend(ac_buffer)
                    end_frames = len(combined_buffer)
                    start_frames = end_frames - ac_buffer.shape[0]
                elif segment == 'bg':
                    if bg_index < len(bgs_buffer):
                        # Add background frames
                        combined_buffer.extend(bgs_buffer[bg_index])
                        bg_index += 1

                fps = 30
                frame_size = (1280, 720)
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')

                with lock:
                    out = cv2.VideoWriter(output_video_path_template.format(n), fourcc, fps, frame_size)

                    for frame in combined_buffer:
                        out.write(frame)
                    out.release()

                    anno_json[n] = {'seg': [start_frames / fps, end_frames / fps], 'ac': vc}
                    print(f"Processed video {n} successfully.")
                    n = n + 1  # Increment n globally after processing each video

# Load data
al = json.load(open('combined.json', 'r'))
background_segments = json.load(open('background_segments_filter2s.json', 'r'))

# Initialize variables
output_video_directory = "r"
output_video_path_template = os.path.join(output_video_directory, '{}.mp4')
anno_json = {}
lock = threading.Lock()

# Split keys into chunks for parallel processing
num_threads = 10  # Define the number of threads
chunk_size = len(al) // num_threads  # Adjust num_threads as needed
chunks = [list(al.keys())[i:i + chunk_size] for i in range(0, len(al), chunk_size)]

# Start processing videos
threads = []
for chunk in chunks:
    thread = threading.Thread(target=process_video_segment, args=(chunk, al, background_segments, output_video_path_template, anno_json, lock))
    thread.start()
    threads.append(thread)

# Wait for all threads to finish
for thread in threads:
    thread.join()

# Save JSON
with open('annotations.json', 'w') as f:
    json.dump(anno_json, f, indent=2)

print("All videos processed successfully.")
