#!/usr/bin/env python3

import rclpy
from action_msgs.msg import GoalStatus
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from lab_interfaces.action import DriveDistance
from my_robot_interfaces.action import Rotate


class SquareDriver(Node):
    def __init__(self):
        super().__init__("square_driver")
        self.declare_parameter("side_length", 0.5)
        self.drive = ActionClient(self, DriveDistance, "drive_distance")
        self.rotate = ActionClient(self, Rotate, "rotate")
        self.step = 0
        self.waiting = False
        self.timer = self.create_timer(0.1, self.start)

    def start(self):
        if self.waiting or self.step >= 8:
            return
        client = self.drive if self.step % 2 == 0 else self.rotate
        if not client.server_is_ready():
            return
        self.waiting = True
        if self.step % 2 == 0:
            goal = DriveDistance.Goal()
            goal.distance = self.get_parameter("side_length").value
        else:
            goal = Rotate.Goal()
            goal.angle = 1.57079632679
        client.send_goal_async(goal).add_done_callback(self.on_goal_response)

    def on_goal_response(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error(f"Goal failed on square step {self.step + 1}")
            self.destroy_timer(self.timer)
            return
        goal_handle.get_result_async().add_done_callback(self.on_result)

    def on_result(self, future):
        result = future.result()
        if result.status != GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().error(f"Goal failed on square step {self.step + 1}")
            self.destroy_timer(self.timer)
            return
        self.step += 1
        self.waiting = False
        if self.step == 8:
            self.get_logger().info("Square completed")
            self.destroy_timer(self.timer)


def main():
    rclpy.init()
    node = SquareDriver()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
