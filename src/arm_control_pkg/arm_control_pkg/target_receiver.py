from std_msgs.msg import Float64MultiArray


class TargetReceiver:

    def __init__(self, node):
        self.targets = []

        self.subscription = (
            node.create_subscription(
                Float64MultiArray,
                "/pumpkin_target",
                self.target_callback,
                10
            )
        )

    def target_callback(self, msg):
        if len(msg.data) < 5:
            return

        target = {
            "position": (
                msg.data[0],
                msg.data[1],
                msg.data[2]
            ),
            "ripe": bool(msg.data[3]),
            "confidence": msg.data[4]
        }

        self.targets.append(target)