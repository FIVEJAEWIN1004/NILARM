"""Pinky /harvest client: early departure on feedback status=departure_ready.

Real CameraStraightDrive callbacks on a stand-in `self`: no rclpy node, no
publisher, no motor. The drive step itself (_start_next_stop_from_station) is
recorded, never run.
"""

import types

import pytest

from pinky_camera_drive import camera_straight_drive as drive

Drive = drive.CameraStraightDrive


class Log:
    def __init__(self):
        self.lines = []

    def info(self, text):
        self.lines.append(('info', text))

    def warning(self, text):
        self.lines.append(('warning', text))

    def error(self, text):
        self.lines.append(('error', text))


def make_node(target_count=1):
    node = types.SimpleNamespace()
    log = Log()
    node.get_logger = lambda: log
    node.log = log
    node.use_harvest_action = True
    node.harvest_target_count = target_count
    node.harvest_shutting_down = False
    node.harvest_cycle_id = 0
    node.state = drive.DriveState.STATION_LOAD_WAIT
    node.departures = []
    node.cancels = []
    node._publish_stop = lambda repeat=1: None
    node.harvest_action_client = types.SimpleNamespace(server_is_ready=lambda: True)
    node.harvest_goal_handle = types.SimpleNamespace(
        cancel_goal_async=lambda: node.cancels.append(1))

    def depart(now):
        node.departures.append(now)
        node.state = drive.DriveState.STATION_TO_NEXT_STOP
    node._start_next_stop_from_station = depart
    for name in ('_reset_harvest_action_state', '_harvest_feedback_callback',
                 '_harvest_result_callback', '_control_station_load_wait'):
        setattr(node, name, getattr(Drive, name).__get__(node))
    node._reset_harvest_action_state()  # cycle 1, as at STATION arrival
    node.harvest_goal_sent = True
    node.harvest_goal_accepted = True
    return node


def feedback(node, status, count=1, cycle=None):
    message = types.SimpleNamespace(
        feedback=types.SimpleNamespace(status=status, current_count=count))
    node._harvest_feedback_callback(
        message, node.harvest_cycle_id if cycle is None else cycle)


def result(node, success=True, count=1):
    future = types.SimpleNamespace(result=lambda: types.SimpleNamespace(
        result=types.SimpleNamespace(success=success, harvested_count=count)))
    node._harvest_result_callback(future, node.harvest_cycle_id)


def tick(node, now='t'):
    if node.state == drive.DriveState.STATION_LOAD_WAIT:
        node._control_station_load_wait(now)


def test_departure_ready_departs_before_final_result_without_cancel():
    node = make_node()
    feedback(node, 'grasping', 0)
    feedback(node, 'placing', 0)
    tick(node)
    assert node.departures == []  # ordinary progress never departs
    feedback(node, 'departure_ready', 1)
    tick(node, 't1')
    assert node.departures == ['t1']
    assert node.state == drive.DriveState.STATION_TO_NEXT_STOP
    assert node.cancels == [] and node.harvest_departed_early


def test_late_success_result_never_departs_twice():
    node = make_node()
    feedback(node, 'departure_ready', 1)
    tick(node, 't1')
    feedback(node, 'departure_ready', 1)  # duplicate: ignored
    result(node, success=True, count=1)
    tick(node, 't2')
    assert node.departures == ['t1']
    assert node.state == drive.DriveState.STATION_TO_NEXT_STOP


def test_late_failed_result_logs_error_but_keeps_driving():
    node = make_node()
    feedback(node, 'departure_ready', 1)
    tick(node, 't1')
    result(node, success=False, count=1)
    tick(node, 't2')
    assert node.departures == ['t1']
    assert node.state == drive.DriveState.STATION_TO_NEXT_STOP
    assert any(level == 'error' and 'AFTER EARLY DEPARTURE' in text
               for level, text in node.log.lines)


def test_without_departure_ready_waits_for_final_result():
    node = make_node()
    feedback(node, 'completed', 1)
    tick(node)
    assert node.departures == []
    result(node, success=True, count=1)
    tick(node, 't3')
    assert node.departures == ['t3'] and not node.harvest_departed_early


def test_failed_result_without_departure_ready_stays_stopped():
    node = make_node()
    feedback(node, 'failed', 0)
    result(node, success=False, count=0)
    tick(node)
    tick(node)
    assert node.departures == []
    assert node.state == drive.DriveState.STATION_LOAD_WAIT


def test_flag_off_keeps_result_based_departure(monkeypatch):
    monkeypatch.setattr(drive, 'ENABLE_PINKY_DEPARTURE_AFTER_LAST_RISE', False)
    node = make_node()
    feedback(node, 'departure_ready', 1)
    tick(node)
    assert node.departures == []
    result(node, success=True, count=1)
    tick(node, 't4')
    assert node.departures == ['t4']


@pytest.mark.parametrize('count,cycle', [(1, 0), (0, None)])
def test_stale_cycle_or_short_count_is_ignored(count, cycle):
    node = make_node()
    feedback(node, 'departure_ready', count, cycle=cycle)
    tick(node)
    assert node.departures == []


def test_next_station_starts_clean():
    node = make_node()
    feedback(node, 'departure_ready', 1)
    tick(node, 't1')
    node.state = drive.DriveState.STATION_LOAD_WAIT
    node._reset_harvest_action_state()
    assert not node.harvest_departure_ready and not node.harvest_departed_early


def test_flag_has_same_name_and_default_on_both_sides():
    import pathlib
    v4 = (pathlib.Path(__file__).resolve().parents[2] / 'arm_control_pkg' / 'arm_control_pkg'
          / 'pumpkin_harvest' / 'pumpkin_full_auto_orange_harvest_to_bin_v4.py').read_text()
    assert 'ENABLE_PINKY_DEPARTURE_AFTER_LAST_RISE = True' in v4
    assert drive.ENABLE_PINKY_DEPARTURE_AFTER_LAST_RISE is True
