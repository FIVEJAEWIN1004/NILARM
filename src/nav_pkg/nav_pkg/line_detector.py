#!/usr/bin/env python3

import time

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Float32


LOWER_BLUE = np.array([82, 55, 40], dtype=np.uint8)
UPPER_BLUE = np.array([105, 210, 255], dtype=np.uint8)

KERNEL = np.ones((5, 5), np.uint8)

ROI_START = 0.35
MIN_AREA = 300

CENTER_OFFSET = 390

LOSS_TIMEOUT = 0.5


class LineDetectorV2(Node):

    def __init__(self):
        super().__init__('line_detector_v2')

        self.create_subscription(
            CompressedImage,
            '/camera/image/compressed',
            self.image_callback,
            10
        )

        self.error_publisher = self.create_publisher(
            Float32,
            '/line_error',
            10
        )

        self.debug = self.declare_parameter(
            'debug',
            False
        ).value

        self.last_center = None
        self.last_left_x = None
        self.last_error = 0.0
        self.last_detection_time = time.monotonic()

        self.get_logger().info(
            'NILARM LINE DETECTOR V2 STARTED'
        )

    def image_callback(self, msg):

        frame = cv2.imdecode(
            np.frombuffer(msg.data, np.uint8),
            cv2.IMREAD_COLOR
        )

        if frame is None:
            return

        frame = cv2.flip(frame, -1)

        height, width = frame.shape[:2]

        roi = frame[
            int(height * ROI_START):height,
            0:width
        ]

        roi_height, roi_width = roi.shape[:2]

        image_center_x = roi_width // 2

        hsv = cv2.cvtColor(
            roi,
            cv2.COLOR_BGR2HSV
        )

        mask = cv2.inRange(
            hsv,
            LOWER_BLUE,
            UPPER_BLUE
        )

        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            KERNEL
        )

        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_CLOSE,
            KERNEL
        )

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        candidates = []

        for contour in contours:

            area = cv2.contourArea(contour)

            if area < MIN_AREA:
                continue

            moments = cv2.moments(contour)

            if moments['m00'] == 0:
                continue

            cx = moments['m10'] / moments['m00']
            cy = moments['m01'] / moments['m00']

            if cx >= image_center_x:
                continue

            candidates.append(
                (area, cx, cy, contour)
            )

        center_x = None
        selected_contour = None

        if candidates:

            candidates.sort(
                key=lambda x: x[0],
                reverse=True
            )

            area, cx, cy, selected_contour = candidates[0]

            left_x = cx

            center_x = int(
                np.clip(
                    left_x + CENTER_OFFSET,
                    0,
                    roi_width - 1
                )
            )

            self.last_left_x = left_x
            self.last_center = center_x
            self.last_error = float(
                image_center_x - center_x
            )
            self.last_detection_time = time.monotonic()

            self.error_publisher.publish(
                Float32(data=self.last_error)
            )

        else:

            elapsed = (
                time.monotonic()
                - self.last_detection_time
            )

            if (
                self.last_center is not None
                and elapsed < LOSS_TIMEOUT
            ):

                self.error_publisher.publish(
                    Float32(data=self.last_error)
                )

        if self.debug:

            debug_frame = roi.copy()

            cv2.line(
                debug_frame,
                (image_center_x, 0),
                (image_center_x, roi_height),
                (255, 0, 0),
                2
            )

            if selected_contour is not None:

                cv2.drawContours(
                    debug_frame,
                    [selected_contour],
                    -1,
                    (0, 255, 0),
                    3
                )

                moments = cv2.moments(
                    selected_contour
                )

                if moments['m00'] != 0:

                    cx = int(
                        moments['m10'] /
                        moments['m00']
                    )

                    cy = int(
                        moments['m01'] /
                        moments['m00']
                    )

                    cv2.circle(
                        debug_frame,
                        (cx, cy),
                        8,
                        (0, 255, 0),
                        -1
                    )

                    target_x = int(
                        np.clip(
                            cx + CENTER_OFFSET,
                            0,
                            roi_width - 1
                        )
                    )

                    cv2.circle(
                        debug_frame,
                        (target_x, cy),
                        9,
                        (0, 0, 255),
                        -1
                    )

                    cv2.line(
                        debug_frame,
                        (cx, cy),
                        (target_x, cy),
                        (255, 255, 0),
                        2
                    )

            cv2.putText(
                debug_frame,
                f'CENTER: {self.last_center if self.last_center is not None else "NONE"}',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 0, 255),
                2
            )

            cv2.putText(
                debug_frame,
                f'ERROR: {self.last_error:.1f}',
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 0, 255),
                2
            )

            cv2.putText(
                debug_frame,
                'CONTOUR V2',
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.imshow(
                'NILARM Line Detection V2',
                debug_frame
            )

            cv2.imshow(
                'NILARM HSV Mask V2',
                mask
            )

            cv2.waitKey(1)

    def destroy_node(self):

        self.get_logger().info(
            'STOPPING LINE DETECTOR V2'
        )

        super().destroy_node()


def main(args=None):

    rclpy.init(args=args)

    node = LineDetectorV2()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()