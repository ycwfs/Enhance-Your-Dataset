import cv2
import json
import os
video_lengths = {}

al = json.load(open('combined.json', 'r'))
# 假设所有视频文件都在 "videos" 目录下
video_directory = "videos"
for category, videos in al.items():
    for video_id in videos:
        video_path = os.path.join(video_directory, video_id + ".mp4")
        if video_id == 'subset':
            continue
        if os.path.exists(video_path):
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps
                if video_id not in video_lengths:
                    video_lengths[video_id] = {}
                video_lengths[video_id]['duration'] = duration
                video_lengths[video_id]['frames'] = frame_count
            cap.release()
            print(f"{video_id} duration: {duration:.2f} seconds, frames: {frame_count}")
        else:
            print(f"Warning: {video_path} does not exist.")

# 保存视频时长信息
with open(("video_lengths.json"), "w") as f:
    json.dump(video_lengths, f, indent=4)