#!/usr/bin/env python3
"""Hardware-free Harvest action server for Pinky integration tests."""

import threading
import time

import rclpy
from interfaces_pkg.action import Harvest
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node


class FakeHarvestActionServer(Node):
    """Simulate one harvest goal at a time without importing OMX code."""

    def __init__(self):
        super().__init__('fake_harvest_action_server')
        self._goal_lock = threading.Lock()
        self._goal_active = False
        self._action_server = ActionServer(
            self,
            Harvest,
            '/harvest',
            execute_callback=self._execute_callback,
            goal_callback=self._goal_callback,
            cancel_callback=self._cancel_callback,
            callback_group=ReentrantCallbackGroup(),
        )
        self.get_logger().info('Fake Harvest Server READY')

    def _goal_callback(self, goal_request):
        if goal_request.target_count <= 0:
            self.get_logger().warning(
                f'Rejecting Harvest goal: target_count={goal_request.target_count}')
            return GoalResponse.REJECT
        with self._goal_lock:
            if self._goal_active:
                self.get_logger().warning(
                    'Rejecting Harvest goal: another goal is active')
                return GoalResponse.REJECT
            self._goal_active = True
        self.get_logger().info(
            f'Accepting Harvest goal: target_count={goal_request.target_count}')
        return GoalResponse.ACCEPT

    def _cancel_callback(self, _goal_handle):
        self.get_logger().warning('Fake Harvest goal cancel requested')
        return CancelResponse.ACCEPT

    def _execute_callback(self, goal_handle):
        target_count = int(goal_handle.request.target_count)
        feedback = Harvest.Feedback()
        result = Harvest.Result()
        stages = (
            (0, 'searching'),
            (0, 'scanning'),
            (0, 'grasping'),
            (target_count, 'completed'),
        )
        try:
            self.get_logger().info(
                f'Fake harvest started: target_count={target_count}')
            for index, (current_count, status) in enumerate(stages):
                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    result.success = False
                    result.harvested_count = 0
                    self.get_logger().warning('Fake harvest canceled')
                    return result
                feedback.current_count = current_count
                feedback.status = status
                goal_handle.publish_feedback(feedback)
                if index < len(stages) - 1:
                    time.sleep(1.0)

            goal_handle.succeed()
            result.success = True
            result.harvested_count = target_count
            self.get_logger().info(
                'Fake harvest result: '
                f'success=True, harvested_count={target_count}')
            return result
        except Exception as error:
            goal_handle.abort()
            result.success = False
            result.harvested_count = 0
            self.get_logger().error(f'Fake harvest failed: {error}')
            return result
        finally:
            with self._goal_lock:
                self._goal_active = False

    def destroy_node(self):
        self._action_server.destroy()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = FakeHarvestActionServer()
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
