#!/bin/bash

input_directory="videos"
output_directory="resized_videos"

# 创建输出目录，如果不存在的话
mkdir -p "$output_directory"

# 遍历所有 .mp4 视频文件
for file in "$input_directory"/*.mp4; do

    # 设置输出文件的路径
    output_file="$output_directory/$(basename "$file")"
    # 如果文件名存在，则跳过
    if [ -f "$output_file" ]; then
        echo "File already exists. Skipping..."
        continue
    fi

    echo "Processing $(basename "$file")..."

    # 使用 ffmpeg 调整视频分辨率
    ffmpeg -i "$file" -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" -loglevel error "$output_file"
done

echo "All videos have been resized and saved to $output_directory."
