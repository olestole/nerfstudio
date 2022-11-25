#!/usr/bin/env python

import glob
import os
from dataclasses import dataclass
from pathlib import Path

import cv2
import tyro
from rich.console import Console
from typing_extensions import Literal

from nerfstudio.utils.scripts import run_command

CONSOLE = Console(width=120)

@dataclass
class Args:
    model: str
    data_source: Literal["video", "images", "polycam"]
    input_data_dir: Path
    output_dir: Path
    percent_frames: float = 1.0

def process_data(data_source: Literal["video", "images", "polycam"], input_data_dir: Path, output_dir: Path, percent_frames: float):
    CONSOLE.print("Processing data")
    cmd = f"ns-process-data {data_source} --data {input_data_dir} --output-dir {output_dir}"

    if data_source == "video" and percent_frames != 1.0:
        video = cv2.VideoCapture(path)
        total = int(video.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT))
        print(f"Num frames: {total}")
        num_frames = int(total * percent_frames)
        cmd = f"ns-process-data {data_source} --data {input_data_dir} --output-dir {output_dir} --num-frames-target {num_frames}"

    print(cmd)
    run_command(cmd, verbose=True)

# ns-train instant-ngp --data data/videos/tier2 --trainer.load_dir $output_path --viewer.start-train False
def train(model: str, input_data_dir: Path):
    CONSOLE.print(f"Trainig model\nModel: {model}\nInput dir: {input_data_dir}")
    cmd = f"ns-train {model} --data {input_data_dir} --vis wandb --viewer.quit-on-train-completion True"
    run_command(cmd, verbose=True)

def eval(config: Path, output_name: Path):
    CONSOLE.print("Evaluating model")
    cmd = f"ns-eval --load-config {config} --output-path evals/{output_name}.json"
    run_command(cmd, verbose=True)


if __name__ == '__main__':
    """
    Run this script to process input-data, train and evaluate a model.
    Example: ./nerf_pipeline.py --model nerfacto --data_source images --input_data data/videos/hovedbygget/images_old --output_dir data/videos/hovedbygget
    """
    args = tyro.cli(Args)
    print(args)
    
    process_data(args.data_source, args.input_data_dir, args.output_dir, args.percent_frames)
    train(args.model, args.output_dir)

    experiment_name = '-'.join(str(args.output_dir).split('/'))
    train_output_dir = f"outputs/{experiment_name}/{args.model}"
    latest_changed_dir = max(glob.glob(f"{train_output_dir}/*"), key=os.path.getmtime).split("/")[-1]
    train_output_dir = os.path.join(train_output_dir, latest_changed_dir, "config.yml")

    eval(train_output_dir, experiment_name)
