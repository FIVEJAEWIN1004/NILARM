#!/usr/bin/env python3
"""ROS 2 Harvest action adapter for the verified OMX harvest flow."""

import threading

import rclpy
from interfaces_pkg.action import Harvest
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node


class HarvestActionServer(Node):
    """Accept one harvest goal and defer all hardware work until execution."""

    def __init__(self):
        super().__init__('harvest_action_server')
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
        self.get_logger().info(
            'Harvest Action Server READY - waiting for goal')

    def _goal_callback(self, goal_request):
        if goal_request.target_count <= 0:
            self.get_logger().warning(
                'Rejecting Harvest goal: target_count must be positive')
            return GoalResponse.REJECT
        with self._goal_lock:
            if self._goal_active:
                self.get_logger().warning(
                    'Rejecting Harvest goal: another harvest is active')
                return GoalResponse.REJECT
            self._goal_active = True
        self.get_logger().info(
            f'Accepting Harvest goal: target_count={goal_request.target_count}')
        return GoalResponse.ACCEPT

    def _cancel_callback(self, _goal_handle):
        self.get_logger().warning(
            'Harvest cancel requested; stopping at the next safe checkpoint')
        return CancelResponse.ACCEPT

    def _execute_callback(self, goal_handle):
        target_count = int(goal_handle.request.target_count)
        harvested_count = 0
        result = Harvest.Result()

        def publish_feedback(current_count: int, status: str) -> None:
            feedback = Harvest.Feedback()
            feedback.current_count = int(current_count)
            feedback.status = status
            goal_handle.publish_feedback(feedback)
            self.get_logger().info(
                f'Harvest feedback: current_count={current_count}, '
                f'status={status}')

        try:
            # Deliberately deferred: importing the OMX/YOLO harvest stack and
            # calling run_harvest happen only after this accepted goal executes.
            from .pumpkin_full_auto_orange_harvest_to_bin_v5 import run_harvest

            self.get_logger().warning(
                f'Harvest execution started: target_count={target_count}')
            run_result = run_harvest(
                target_count=target_count,
                require_start_confirmation=False,
                require_harvest_confirmation=False,
                feedback_callback=publish_feedback,
                cancel_callback=lambda: goal_handle.is_cancel_requested,
            )
            harvested_count = int(run_result.harvested_count)

            if run_result.cancelled or goal_handle.is_cancel_requested:
                goal_handle.canceled()
                result.success = False
                result.harvested_count = harvested_count
                self.get_logger().warning(
                    'Harvest canceled safely: '
                    f'harvested_count={harvested_count}')
                return result

            result.success = harvested_count >= target_count
            result.harvested_count = harvested_count
            if result.success:
                goal_handle.succeed()
                self.get_logger().info(
                    'Harvest succeeded: '
                    f'harvested_count={harvested_count}')
            else:
                publish_feedback(harvested_count, 'failed')
                goal_handle.abort()
                self.get_logger().error(
                    'Harvest target not met: '
                    f'target_count={target_count}, '
                    f'harvested_count={harvested_count}')
            return result
        except Exception as error:
            harvested_count = int(
                getattr(error, 'harvested_count', harvested_count))
            try:
                publish_feedback(harvested_count, 'failed')
            except Exception:
                pass
            goal_handle.abort()
            result.success = False
            result.harvested_count = harvested_count
            self.get_logger().error(
                f'Harvest execution failed: {error}; '
                f'harvested_count={harvested_count}')
            return result
        finally:
            with self._goal_lock:
                self._goal_active = False

    def destroy_node(self):
        self._action_server.destroy()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = HarvestActionServer()
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
