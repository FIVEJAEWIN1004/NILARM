import numpy as np
from omx_f import OmxFollower

arm = None

try:
    arm = OmxFollower().connect()

    print("기본 준비 자세로 이동합니다.")
    arm.ready(duration=5.0)

    print(
        "관절 각도 [deg]:",
        np.round(np.degrees(arm.joints()), 1)
    )

    print(
        "팔 끝 좌표 [m]:",
        np.round(arm.pose(), 4)
    )

    input("기본 자세를 확인한 뒤 Enter를 누르세요.")

finally:
    if arm is not None:
        print("정리 자세로 이동합니다.")
        arm.park()
        arm.disconnect()