"""Observe Pinky's motion, harvest result and display mode on the LED/LCD.

Canonical copy of the Pi-only pinky_led node (needs pinkylib + pinky_lcd on
the robot). Run by nilarm_bringup competition.launch.py.
"""

import os
import time

import rclpy
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import Twist
from PIL import Image, ImageDraw, ImageFont, ImageOps
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String

from pinky_lcd import LCD
from pinkylib import LED


RED = (255, 0, 0)
GREEN = (0, 255, 0)
LCD_SIZE = (320, 240)
FONT_CANDIDATES = (
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
    '/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
)


class PinkyStatusDisplay(Node):
    """Drive LEDs from /cmd_vel and render the latest harvest result."""

    def __init__(self):
        super().__init__('pinky_status_display')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter(
            'display_result_topic', '/harvest/display_result')
        self.declare_parameter('cmd_vel_epsilon', 0.001)
        self.declare_parameter('cmd_vel_timeout_sec', 0.5)
        self.declare_parameter('lcd_font_size', 90)
        self.declare_parameter('display_mode_topic', '/pinky/display_mode')
        # Empty = keroro.jpg from the pinky_media package share directory.
        self.declare_parameter('image_path', '')

        self._epsilon = float(self.get_parameter('cmd_vel_epsilon').value)
        self._cmd_vel_timeout = float(
            self.get_parameter('cmd_vel_timeout_sec').value)
        self._font_size = int(self.get_parameter('lcd_font_size').value)
        if self._epsilon < 0.0:
            raise ValueError('cmd_vel_epsilon must not be negative')
        if self._cmd_vel_timeout <= 0.0:
            raise ValueError('cmd_vel_timeout_sec must be positive')
        if self._font_size <= 0:
            raise ValueError('lcd_font_size must be positive')

        self._last_cmd_vel_time = None
        self._current_led_state = None
        self._led = None
        self._lcd = None
        self._closed = False
        self._image = self._load_image()

        # LCD is initialized first because both vendor libraries configure
        # hardware resources during construction. Each object is then reused.
        try:
            self._lcd = LCD()
            self._show_black_screen()
        except Exception as error:
            self._lcd = None
            self.get_logger().error(
                f'LCD initialization failed; display disabled: {error}')

        try:
            self._led = LED()
            self._set_led_state(False, 'startup: waiting for /cmd_vel')
        except Exception as error:
            self._led = None
            self.get_logger().error(
                f'LED initialization failed; LED disabled: {error}')

        display_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.create_subscription(
            Twist,
            str(self.get_parameter('cmd_vel_topic').value),
            self._cmd_vel_callback,
            10,
        )
        self.create_subscription(
            String,
            str(self.get_parameter('display_result_topic').value),
            self._display_result_callback,
            display_qos,
        )
        self.create_subscription(
            String,
            str(self.get_parameter('display_mode_topic').value),
            self._display_mode_callback,
            10,
        )
        self.create_timer(0.1, self._cmd_vel_watchdog)
        self.get_logger().info(
            'Pinky status display ready: /cmd_vel moving=GREEN, '
            'stopped/timeout=RED')

    def _cmd_vel_callback(self, message):
        self._last_cmd_vel_time = time.monotonic()
        moving = (
            abs(float(message.linear.x)) > self._epsilon
            or abs(float(message.angular.z)) > self._epsilon
        )
        self._set_led_state(moving, 'nonzero /cmd_vel' if moving else 'zero /cmd_vel')

    def _cmd_vel_watchdog(self):
        if self._last_cmd_vel_time is None:
            self._set_led_state(False, 'waiting for /cmd_vel')
            return
        age = time.monotonic() - self._last_cmd_vel_time
        if age > self._cmd_vel_timeout:
            self._set_led_state(False, f'/cmd_vel timeout ({age:.2f}s)')

    def _set_led_state(self, moving, reason):
        desired_state = 'GREEN' if moving else 'RED'
        if desired_state == self._current_led_state or self._led is None:
            return
        color = GREEN if moving else RED
        try:
            self._led.fill(color)
            self._current_led_state = desired_state
            self.get_logger().info(f'LED={desired_state}: {reason}')
        except Exception as error:
            self.get_logger().error(f'LED write failed: {error}')

    def _show_black_screen(self):
        if self._lcd is not None:
            self._lcd.img_show(Image.new('RGB', LCD_SIZE, 'black'))

    def _load_font(self, text):
        for font_path in FONT_CANDIDATES:
            if not os.path.isfile(font_path):
                continue
            size = self._font_size
            while size >= 32:
                font = ImageFont.truetype(font_path, size)
                bounds = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox(
                    (0, 0), text, font=font)
                if bounds[2] - bounds[0] <= LCD_SIZE[0] - 20:
                    return font
                size -= 2
        return ImageFont.load_default()

    def _load_image(self):
        path = str(self.get_parameter('image_path').value)
        try:
            if not path:
                path = os.path.join(
                    get_package_share_directory('pinky_media'),
                    'assets', 'keroro.jpg')
            with Image.open(path) as source:
                # Keep aspect ratio; letterbox the rest in black.
                return ImageOps.pad(
                    source.convert('RGB'), LCD_SIZE, color='black')
        except Exception as error:
            self.get_logger().error(
                f'LCD image unavailable; IMAGE mode disabled: {error}')
            return None

    def _display_mode_callback(self, message):
        mode = message.data.strip().upper()
        if mode != 'IMAGE':
            self.get_logger().warning(f'Unknown display mode: {message.data!r}')
            return
        if self._lcd is None or self._image is None:
            self.get_logger().error('Cannot show IMAGE: LCD or image unavailable')
            return
        try:
            self._lcd.img_show(self._image)
            self.get_logger().info('LCD mode=IMAGE')
        except Exception as error:
            self.get_logger().error(
                f'LCD image render failed; status node will continue: {error}')

    def _display_result_callback(self, message):
        text = message.data.strip()
        if not text:
            self.get_logger().warning('Ignoring empty harvest display result')
            return
        if self._lcd is None:
            self.get_logger().error(
                f'Cannot display harvest result because LCD is unavailable: {text}')
            return
        try:
            image = Image.new('RGB', LCD_SIZE, 'black')
            draw = ImageDraw.Draw(image)
            font = self._load_font(text)
            left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
            x = (LCD_SIZE[0] - (right - left)) / 2.0 - left
            y = (LCD_SIZE[1] - (bottom - top)) / 2.0 - top
            draw.text((x, y), text, fill='white', font=font)
            self._lcd.img_show(image)
            self.get_logger().info(f'LCD harvest result displayed: {text}')
        except Exception as error:
            self.get_logger().error(
                f'LCD render failed; status node will continue: {error}')

    def destroy_node(self):
        if self._closed:
            return super().destroy_node()
        self._closed = True
        if self._led is not None:
            try:
                self._led.fill(RED)
            except Exception as error:
                self.get_logger().error(f'LED shutdown RED failed: {error}')
            try:
                self._led.close()
            except Exception as error:
                self.get_logger().error(f'LED close failed: {error}')
            self._led = None
        if self._lcd is not None:
            try:
                self._lcd.close()
            except Exception as error:
                self.get_logger().error(f'LCD close failed: {error}')
            self._lcd = None
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = PinkyStatusDisplay()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
