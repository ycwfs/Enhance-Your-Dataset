import os
import cv2
import json
import random
import numpy as np
import itertools



# ac_len = patterns[0].count('a')
# bg_len = patterns[0].count('b')
ac_len = 7
bg_len = 6

output_video_directory = f"r{ac_len}"
if not os.path.exists(output_video_directory):
    os.makedirs(output_video_directory)

def generate_combinations(num_a, num_b):
    # 生成所有可能的组合
    total_length = num_a + num_b
    patterns = ['a', 'b']
    all_combinations = itertools.product(patterns, repeat=total_length)
    
    valid_combinations = []
    # 筛选出具有正确数量的 'a' 和 'b' 的组合
    for combination in all_combinations:
        if combination.count('a') == num_a and combination.count('b') == num_b:
            valid_combinations.append(''.join(combination))
    
    return valid_combinations

# Load JSON files
al = json.load(open('/data1/wangqiurui/code/datasets/rebuild/combined.json', 'r'))
background_segments = json.load(open('/data1/wangqiurui/code/datasets/rebuild/background_segments_filter2s.json', 'r'))

n = 1

# Combinations of three action and two background clips
patterns = generate_combinations(ac_len, bg_len)

c_len = len(patterns[0])

# Annotations dictionary
anno_json = {}

# Process each action class
for main_vc in al.keys():
    for i in range(10):
        # Ensure first action is from main_vc
        chosen_vcs = [main_vc]
        remaining_vcs = list(al.keys())
        remaining_vcs.remove(main_vc)

        # Randomly choose two more classes
        chosen_vcs.extend(random.sample(remaining_vcs, ac_len-1))

        actions = []
        for vc in chosen_vcs:
            vn = random.choice(list(al[vc].keys()))
            if vn == 'subset':
                continue
            ac = random.choice(al[vc][vn])
            actions.append((vn, ac, vc))
        
        if len(actions) != ac_len:
            i -= 1
            continue

        action_buffers = []
        for vn, ac, vc in actions:
            action_cap = cv2.VideoCapture(f'/data1/wangqiurui/code/datasets/rebuild/resized_videos/{vn}.mp4')
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
                i -= 1
                break
            action_buffers.append((np.stack(ac_buffer), vc))
        if len(action_buffers) != ac_len:
            continue

        # Load background clips
        bgs_buffer = []
        for _ in range(bg_len):
            bn = random.choice(list(background_segments.keys()))
            bg = random.choice(background_segments[bn])
            bg_cap = cv2.VideoCapture(f'/data1/wangqiurui/code/datasets/rebuild/resized_videos/{bn}.mp4')
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

        if len(bgs_buffer) != bg_len:
            i -= 1
            continue

        # Combine the frames based on the chosen pattern
        pattern = random.choices(patterns, weights=[1/len(patterns)]*len(patterns))[0]
        combined_buffer = []
        start_frames = []
        end_frames = []
        action_labels = []
        bg_index = 0
        ac_index = 0
        for segment in pattern:
            if segment == 'a':
                action_buffer, vc = action_buffers[ac_index]
                combined_buffer.extend(action_buffer)
                end_frame_pos = len(combined_buffer)
                start_frame_pos = end_frame_pos - action_buffer.shape[0]
                start_frames.append(start_frame_pos)
                end_frames.append(end_frame_pos)
                action_labels.append(vc)
                ac_index += 1
            elif segment == 'b':
                if bg_index < len(bgs_buffer):
                    combined_buffer.extend(bgs_buffer[bg_index])
                    bg_index += 1

        output_video_path = os.path.join(output_video_directory, f'{n}.mp4')

        # Write the combined frames to a video
        fps = 30
        frame_size = (1280, 720)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, frame_size)
        for frame in combined_buffer:
            out.write(frame)
        out.release()

        print(f"Video successfully saved to {output_video_path}")

        anno_json[n] = {
            'segments': [{'start': start_frame / fps, 'end': end_frame / fps, 'action': action_labels[idx]} for idx, (start_frame, end_frame) in enumerate(zip(start_frames, end_frames))],
        }
        n += 1

# Save annotations to a JSON file
with open(f"annotation_{ac_len}r.json", 'w') as f:
    json.dump(anno_json, f, indent=2)
