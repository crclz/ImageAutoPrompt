import sys

from entropy.domain.models.episode import Episode, EpisodeTimestep, ImageComment, ImagePointer
from entropy.infra.episode_repository import EpisodeRepository


def _make_argv(name):
    return ["get_feedback.py", "--name", name]


def test_prints_extra_comments_on_same_line(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(EpisodeRepository, "episodes_dir", classmethod(lambda cls: tmp_path))
    EpisodeRepository.save_episode(
        "tmp_fb",
        Episode(
            timesteps=[
                EpisodeTimestep(
                    i=0,
                    status=2,
                    chosen_highscores=[ImagePointer(timestep=0, image_index=0)],
                    extra_comments=[ImageComment(timestep=0, image_index=2, comment="配色好")],
                )
            ]
        ),
    )

    from entropy.cli.get_feedback import main

    monkeypatch.setattr(sys, "argv", _make_argv("tmp_fb"))
    main()

    out = capsys.readouterr().out
    assert (
        out.strip()
        == "newest timestep is 0, user choose highscore: timestep_0_image[0], extra comments: timestep_0_image[2]: 配色好"
    )


def test_no_extra_comments_section_when_absent(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(EpisodeRepository, "episodes_dir", classmethod(lambda cls: tmp_path))
    EpisodeRepository.save_episode(
        "tmp_fb2", Episode(timesteps=[EpisodeTimestep(i=0, status=2)])
    )

    from entropy.cli.get_feedback import main

    monkeypatch.setattr(sys, "argv", _make_argv("tmp_fb2"))
    main()

    out = capsys.readouterr().out
    assert out.strip() == "newest timestep is 0, user submitted but chose no highscore"
