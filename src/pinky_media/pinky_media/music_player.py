"""Loop the match song on /pinky/music_control START, stop it on STOP."""

import os
import shutil
import signal
import subprocess

import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from std_msgs.msg import String


def player_command(song_path):
    """Return an infinite-loop command for the first installed mp3 player."""
    if shutil.which('ffplay'):
        return ['ffplay', '-nodisp', '-loglevel', 'error', '-loop', '0',
                song_path]
    if shutil.which('mpg123'):
        return ['mpg123', '-q', '--loop', '-1', song_path]
    return None


class MusicPlayer(Node):

    def __init__(self):
        super().__init__('pinky_music_player')
        self.declare_parameter('song_path', '')
        self.declare_parameter('stop_timeout_sec', 2.0)
        self._song = str(self.get_parameter('song_path').value)
        if not self._song:
            try:
                self._song = os.path.join(
                    get_package_share_directory('pinky_media'),
                    'assets', 'keroro_song.mp3')
            except Exception as error:
                self.get_logger().error(f'pinky_media share not found: {error}')
        self._stop_timeout = float(
            self.get_parameter('stop_timeout_sec').value)
        self._proc = None
        self.create_subscription(
            String, '/pinky/music_control', self._on_control, 10)
        self.create_timer(1.0, self._watch_player)
        self.get_logger().info(
            f'music player ready (idle until START): {self._song}')

    def _on_control(self, message):
        command = message.data.strip().upper()
        if command == 'START':
            self._start()
        elif command == 'STOP':
            self._stop()
        else:
            self.get_logger().warning(f'unknown music command: {message.data!r}')

    def _start(self):
        if self._proc is not None and self._proc.poll() is None:
            self.get_logger().info('music already playing; START ignored')
            return
        if not os.path.isfile(self._song):
            self.get_logger().error(f'song file missing: {self._song}')
            return
        command = player_command(self._song)
        if command is None:
            self.get_logger().error('no mp3 player found (ffplay/mpg123)')
            return
        try:
            # Own session: terminal Ctrl+C reaches this node, which then
            # stops the player itself instead of racing it.
            self._proc = subprocess.Popen(
                command, stdin=subprocess.DEVNULL, start_new_session=True)
        except OSError as error:
            self._proc = None
            self.get_logger().error(f'music player failed to start: {error}')
            return
        self.get_logger().info(f'music START (pid={self._proc.pid}): {command[0]}')

    def _stop(self):
        proc, self._proc = self._proc, None
        if proc is None or proc.poll() is not None:
            return
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=self._stop_timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
        except ProcessLookupError:
            pass
        self.get_logger().info('music STOP')

    def _watch_player(self):
        if self._proc is not None and self._proc.poll() is not None:
            self.get_logger().error(
                f'music player exited unexpectedly (code={self._proc.returncode})')
            self._proc = None

    def destroy_node(self):
        self._stop()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    # SIGTERM (ros2 launch / kill) takes the same cleanup path as Ctrl+C.
    signal.signal(signal.SIGTERM, signal.default_int_handler)
    node = MusicPlayer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
