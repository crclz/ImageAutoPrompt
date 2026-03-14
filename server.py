from flask import Flask

from entropy.application.episode_handler import EpisodeHandler

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/api/episode/<name>")
def get_episode_data(name):
    return EpisodeHandler.get_episode_data_wrapper(name)
