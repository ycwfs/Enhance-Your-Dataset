import os
import cv2
import json
import random
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

al = json.load(open('combined.json', 'r'))
background_segments = json.load(open('background_segments_filter2s.json', 'r'))

n = 1
combinations = [
    (['bg', 'ac', 'bg'], 2),  # Sequence and count of background clips
    (['ac', 'bg', 'bg'], 2),
    (['bg', 'bg', 'ac'], 2)
]
combinations_2 = [
    (['bg', 'ac'], 1),
    (['ac', 'bg'], 1),
]

anno_json = {}
for vc in al.keys():
    for i in range(10):
        # action
        vn = random.choice(list(al[vc].keys()))
        if vn == 'subset':
            i = i - 1
            continue
        ac = random.choice(al[vc][vn])
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
        if len(ac_buffer) == 0:
            i = i - 1
            continue
        ac_buffer = np.stack(ac_buffer)
        
        # background
        number_of_background = random.choices([1,2],weights=[0.5,0.5])
        bgs_buffer = []
        for nb in range(number_of_background[0]):
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
            if len(bg_buffer) == 0:
                continue
            bg_buffer = np.stack(bg_buffer)
            bgs_buffer.append(bg_buffer)

        if len(bgs_buffer) != number_of_background[0]:
            i = i - 1
            continue
        
        # combine, random [bg,ac,bg] [bg,ac] [ac,bg] [ac,bg,bg] [bg,bg,ac]
        if len(bgs_buffer) == 2:
        # Randomly select a combination
            chosen_combo, bg_count = random.choice(combinations)
        elif len(bgs_buffer) == 1:
            chosen_combo, bg_count = random.choice(combinations_2)
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
            
        output_video_directory = "rebuild_videos"
        if not os.path.exists(output_video_directory):
            os.makedirs(output_video_directory)

        # 输出视频文件路径
        output_video_path = os.path.join(output_video_directory, f'{n}.mp4')

        # 视频写入器设置
        fps = 30
        frame_size = (1280, 720)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, frame_size)

        # 假设 combined_buffer 是包含所有视频帧的列表
        for frame in combined_buffer:
            out.write(frame)  # 写入帧到输出视频

        # 释放视频写入器资源
        out.release()

        print(f"Video successfully saved to {output_video_path}")

        anno_json[n] = {'seg':[start_frames/fps,end_frames/fps],'ac':vc}
        #print(anno_json)

        n = n + 1

# save json
with open('annotation.json','w') as f:
    json.dump(anno_json,f,indent=2)
            