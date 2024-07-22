import cv2
import os
from concurrent.futures import ProcessPoolExecutor

input_directory = "/data1/wangqiurui/code/datasets/rebuild/videos"
output_directory = "/data1/wangqiurui/code/datasets/rebuild/resized_videos"

if not os.path.exists(output_directory):
    os.makedirs(output_directory)

video_files = [f for f in os.listdir(input_directory) if f.endswith('.mp4')]
print(f"Found {len(video_files)} video files.")

def resize_video(video_file):
    input_path = os.path.join(input_directory, video_file)
    output_path = os.path.join(output_directory, video_file)
    if os.path.exists(output_path):
        print(f"Video {video_file} already resized.")
        return
    
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Failed to open video {video_file}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (1280, 720))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        resized_frame = cv2.resize(frame, (1280, 720))
        out.write(resized_frame)
    
    cap.release()
    out.release()
    print(f"Resized video {video_file}")

# 使用 ProcessPoolExecutor
with ProcessPoolExecutor() as executor:
    executor.map(resize_video, video_files)

print("Video resizing completed.")


# [2U903,8BNUT,AT9UV,B32CU,EEVD3,ITDHX]
