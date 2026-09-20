"""Publish raw I420 frames from the Raspberry Pi rpicam stack as ROS images."""

import os
import shutil
import subprocess
import threading
import time
from typing import Optional

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


RPICAM_LIBRARY_PATH = (
    '/usr/local/lib/aarch64-linux-gnu:'
    '/usr/local/lib/aarch64-linux-gnu/libcamera'
)


class RpiCamPublisher(Node):
    """Own rpicam-vid and convert its contiguous I420 byte stream to BGR8."""

    def __init__(self):
        super().__init__('rpicam_publisher')
        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('frame_id', 'camera_link')
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('framerate', 30)
        self.declare_parameter('rpicam_binary', 'rpicam-vid')
        self.declare_parameter('log_fps_interval_sec', 5.0)

        self.width = int(self.get_parameter('width').value)
        self.height = int(self.get_parameter('height').value)
        self.framerate = int(self.get_parameter('framerate').value)
        self.frame_id = str(self.get_parameter('frame_id').value)
        self.frame_size = self.width * self.height * 3 // 2
        if self.width <= 0 or self.height <= 0 or self.framerate <= 0:
            raise ValueError('width, height and framerate must be positive')
        if self.width % 2 or self.height % 2:
            raise ValueError('I420 width and height must both be even')

        self.publisher = self.create_publisher(
            Image, str(self.get_parameter('camera_topic').value),
            qos_profile_sensor_data)
        self.process: Optional[subprocess.Popen] = None
        self.stop_event = threading.Event()
        self.shutdown_lock = threading.Lock()
        self.reader_thread = None
        self.stderr_thread = None
        self.frames_since_log = 0
        self.fps_started_at = time.monotonic()
        self._start_process()

    def _start_process(self):
        binary_name = str(self.get_parameter('rpicam_binary').value)
        binary = shutil.which(binary_name)
        if binary is None:
            raise RuntimeError(f'{binary_name!r} was not found in PATH')

        command = [
            binary,
            '-t', '0',
            '--codec', 'yuv420',
            '--width', str(self.width),
            '--height', str(self.height),
            '--framerate', str(self.framerate),
            '--nopreview',
            '--flush',
            '-o', '-',
        ]
        environment = os.environ.copy()
        # Do not inherit the ROS libcamera/libpisp search path. The rpicam
        # process must use the known-working Raspberry Pi libraries only.
        environment['LD_LIBRARY_PATH'] = RPICAM_LIBRARY_PATH
        self.get_logger().info(
            f'starting {" ".join(command)} with '
            f'LD_LIBRARY_PATH={RPICAM_LIBRARY_PATH}')
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            env=environment,
            start_new_session=True,
        )
        self.reader_thread = threading.Thread(
            target=self._read_loop, name='rpicam-frame-reader', daemon=True)
        self.stderr_thread = threading.Thread(
            target=self._stderr_loop, name='rpicam-stderr-reader', daemon=True)
        self.reader_thread.start()
        self.stderr_thread.start()

    def _read_loop(self):
        try:
            while not self.stop_event.is_set():
                frame_bytes = self._read_exact_frame()
                if frame_bytes is None:
                    if not self.stop_event.is_set():
                        return_code = self.process.poll() if self.process else None
                        self.get_logger().error(
                            'rpicam frame stream ended; '
                            f'process return code={return_code}')
                    return
                self._publish_frame(frame_bytes)
        except Exception as exc:
            if not self.stop_event.is_set():
                self.get_logger().error(f'rpicam reader failed: {exc}')

    def _read_exact_frame(self) -> Optional[bytes]:
        if self.process is None or self.process.stdout is None:
            return None
        data = bytearray()
        while len(data) < self.frame_size and not self.stop_event.is_set():
            chunk = self.process.stdout.read(self.frame_size - len(data))
            if not chunk:
                return None
            data.extend(chunk)
        return bytes(data) if len(data) == self.frame_size else None

    def _publish_frame(self, frame_bytes: bytes):
        yuv = np.frombuffer(frame_bytes, dtype=np.uint8).reshape(
            (self.height * 3 // 2, self.width))
        bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)

        message = Image()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = self.frame_id
        message.height = self.height
        message.width = self.width
        message.encoding = 'bgr8'
        message.is_bigendian = 0
        message.step = self.width * 3
        message.data = bgr.tobytes()
        self.publisher.publish(message)
        self._log_measured_fps()

    def _log_measured_fps(self):
        self.frames_since_log += 1
        elapsed = time.monotonic() - self.fps_started_at
        interval = float(
            self.get_parameter('log_fps_interval_sec').value)
        if elapsed >= interval:
            self.get_logger().info(
                f'publishing {self.frames_since_log / elapsed:.1f} FPS '
                f'({self.width}x{self.height}, bgr8)')
            self.frames_since_log = 0
            self.fps_started_at = time.monotonic()

    def _stderr_loop(self):
        if self.process is None or self.process.stderr is None:
            return
        while not self.stop_event.is_set():
            line = self.process.stderr.readline()
            if not line:
                return
            if self.stop_event.is_set():
                return
            text = line.decode(errors='replace').rstrip()
            if text:
                self.get_logger().info(f'rpicam: {text}')

    def _stop_process(self):
        with self.shutdown_lock:
            if self.stop_event.is_set():
                return
            self.stop_event.set()
            process = self.process
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    self.get_logger().warning(
                        'rpicam did not terminate in 2 seconds; killing it')
                    process.kill()
                    process.wait(timeout=2.0)
            if process is not None:
                if process.stdout is not None:
                    process.stdout.close()
                if process.stderr is not None:
                    process.stderr.close()
            for thread in (self.reader_thread, self.stderr_thread):
                if thread is not None and thread is not threading.current_thread():
                    thread.join(timeout=1.0)

    def destroy_node(self):
        self._stop_process()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = RpiCamPublisher()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        if node is not None:
            node.get_logger().fatal(f'camera publisher stopped: {exc}')
        else:
            print(f'rpicam_publisher fatal: {exc}')
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
