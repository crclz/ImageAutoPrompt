import os
from pathlib import Path

from flask import Flask, abort, redirect, send_from_directory

from entropy.application.episode_handler import EpisodeHandler
from entropy.application.rag_handler import RagHandler

import logging

logging.basicConfig(
    # 1. 日志输出目标：同时输出到文件和控制台（注：basicConfig默认只输出到控制台，指定filename则只输出到文件；如需双输出需自定义，见下文）
    # filename="app.log",  # 取消注释则日志写入文件（默认只输出到控制台）
    # filemode="a",        # 文件写入模式：a=追加（默认），w=覆盖
    # 2. 日志级别（生产环境用INFO，开发用DEBUG）
    level=logging.INFO,
    # 3. 日志格式（包含时间、级别、模块、内容，便于定位问题）
    format="%(asctime)s - %(name)s - %(module)s:%(lineno)d - %(levelname)s - %(message)s",
    # 4. 时间格式（可读性优先）
    datefmt="%Y-%m-%d %H:%M:%S",
    # 5. 编码（解决中文乱码）
    encoding="utf-8",
)

app = Flask(__name__)


class NoPollingFilter(logging.Filter):
    def filter(self, record):
        # 这里的 record.getMessage() 包含了请求行信息
        # 如果包含目标接口且状态码为 200，则返回 False（即不打印）
        return "/api/episodes/dev-1" not in record.getMessage()


log = logging.getLogger("werkzeug")
log.addFilter(NoPollingFilter())


@app.get("/api/episodes/<name>")
def get_episode_data(name):
    return EpisodeHandler.get_episode_data_wrapper(name)


@app.get("/episodes/<episode_name>/files/<path:filename>")
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


@app.post("/api/show-rag")
def show_rag():
    return RagHandler.show_rag_wrapper()


@app.get("/episodes")
def episode_list_page():
    return EpisodeHandler.episode_list_page_wrapper()


@app.get("/")
def index_page():
    return redirect("/episodes")


@app.get("/api/episodes")
def get_episodes():
    return EpisodeHandler.get_episode_list_wrapper()


@app.post("/api/create-episode")
def create_episode():
    return EpisodeHandler.create_episode_wrapper()
