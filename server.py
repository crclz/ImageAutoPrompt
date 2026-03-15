import os
from pathlib import Path

from flask import Flask, abort, send_from_directory

from entropy.application.episode_handler import EpisodeHandler
from entropy.application.rag_handler import RagHandler

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.get("/api/episodes/<name>")
def get_episode_data(name):
    return EpisodeHandler.get_episode_data_wrapper(name)


@app.get("/episodes/<episode_name>/files/<filename>")
def serve_episode_files(episode_name, filename):
    # 1. 构造该 episode 对应的磁盘目录
    episodes_dir = Path("./runs/episodes")

    target_dir = os.path.join(episodes_dir, episode_name)

    # 2. 检查目录是否存在，防止 500 错误
    if not episodes_dir.exists():
        abort(404)

    # 3. 安全地从目录发送文件
    # send_from_directory 会自动防止路径穿越攻击（如 filename 中包含 ../）
    return send_from_directory(target_dir, filename)


@app.get("/episodes/<episode_name>")
def episode_page(episode_name):
    return EpisodeHandler.episode_page_wrapper(episode_name)


@app.post("/api/episodes/<name>/choose-highscore")
def choose_highscore(name: str):
    return EpisodeHandler.choose_high_scores_wrapper(name)


@app.post("/api/episodes/<name>/process-image")
def process_image(name: str):
    return EpisodeHandler.start_image_processing_wrapper(name)


@app.post("/api/episodes/<name>/rollback-timestep")
def rollback_timestep(name: str):
    return EpisodeHandler.rollback_timestep_wrapper(name)


@app.get("/rag")
def rag_page():
    return RagHandler.rag_page_wrapper()

@app.get("/api/show-rag")
def show_rag():
    return RagHandler.show_rag_wrapper()