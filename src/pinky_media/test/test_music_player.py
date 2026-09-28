"""No-audio check: duplicate START spawns one process, STOP reaps it."""

import rclpy
from std_msgs.msg import String

from pinky_media import music_player


def test_start_once_then_stop(monkeypatch):
    monkeypatch.setattr(music_player, 'player_command',
                        lambda path: ['sleep', '60'])
    rclpy.init()
    try:
        node = music_player.MusicPlayer()
        node._song = __file__
        node._on_control(String(data='START'))
        proc = node._proc
        node._on_control(String(data='start'))
        assert node._proc is proc and proc.poll() is None
        node._on_control(String(data='STOP'))
        assert node._proc is None and proc.poll() is not None
        node.destroy_node()
    finally:
        rclpy.shutdown()
