"""Run the OMX scan while Pinky drives; harvest only when /harvest arrives.

One pre-scan is one call of the normal ``run_harvest`` in a worker thread.
Its ``before_harvest`` hook parks that call between scan and harvest (arm at
the central camera pose, camera released) until a /harvest goal claims it, so
the very same scan data, arm connection and default gripper width are used and
the scan is never repeated. No ROS or hardware imports: unit-testable.

Rules:
- the arm never grasps before a /harvest goal (Pinky sends it only at STATION);
- a session is used by at most one /harvest goal, then dropped (consumed);
- an unclaimed READY session expires after ``ready_timeout_sec`` (stale) and a
  new pre-scan request supersedes an unclaimed one; both abandon via the
  existing ScanCancelled path (back to the central pose, park, disconnect);
- no usable pre-scan (none, failed, no ripe pumpkins, expired) -> the normal
  scan -> harvest fallback;
- ``_omx_lock`` is held for every run_harvest call: never two OMX users.
"""

from __future__ import annotations

import threading
from typing import Callable


class _Session:
    def __init__(self):
        self.claimed = False       # a /harvest goal owns it (never reused)
        self.expired = False       # stale or superseded: must not harvest
        self.reached_gate = False  # scan finished and harvest was released
        self.start = threading.Event()
        self.done = threading.Event()
        self.result = None
        self.error: BaseException | None = None
        self.feedback = None
        self.cancel = None
        self.display = None
        self.display_result: str | None = None


class PrescanCoordinator:

    def __init__(
        self,
        run_harvest: Callable,
        ready_timeout_sec: float = 180.0,
        log: Callable[[str], None] = print,
    ):
        self._run_harvest = run_harvest
        self._ready_timeout_sec = float(ready_timeout_sec)
        self._log = log
        self._lock = threading.Lock()      # session state
        self._omx_lock = threading.Lock()  # OMX arm + arm camera
        self._session: _Session | None = None
        self._harvesting = False

    # --- pre-scan side ------------------------------------------------------

    def request_prescan(self) -> tuple[bool, str]:
        with self._lock:
            if self._harvesting:
                return False, 'harvest already running; pre-scan refused'
            old, self._session = self._session, _Session()
            session = self._session
            if old is not None:
                self._expire_locked(old)
        threading.Thread(
            target=self._worker, args=(session,), name='omx_prescan',
        ).start()
        if old is not None:
            return True, 'pre-scan started (previous unclaimed pre-scan dropped)'
        return True, 'pre-scan started'

    def _worker(self, session: _Session) -> None:
        try:
            with self._omx_lock:  # waits for a superseded run to park
                if session.expired:
                    return
                self._log('pre-scan: OMX scan started')
                session.result = self._run_harvest(
                    target_count=None,
                    feedback_callback=lambda count, status: self._feedback(
                        session, count, status),
                    cancel_callback=lambda: self._cancelled(session),
                    display_result_callback=lambda text: self._display(
                        session, text),
                    before_harvest=lambda: self._gate(session),
                )
        except BaseException as error:  # handed to the claiming goal
            session.error = error
        finally:
            session.done.set()

    def _gate(self, session: _Session) -> bool:
        """Called by scan.main between scan and harvest (arm at centre)."""
        self._log('pre-scan: SCAN_READY; waiting for /harvest (Pinky STATION)')
        session.start.wait(self._ready_timeout_sec)
        with self._lock:
            if not session.claimed or session.expired:
                session.expired = True
                if self._session is session:
                    self._session = None
                self._log('pre-scan: expired unused; arm returns to park')
                return False
            session.reached_gate = True
            display, pending = session.display, session.display_result
        self._log('pre-scan: /harvest received; harvesting scanned pumpkins')
        if pending is not None and display is not None:
            display(pending)
        return True

    def _feedback(self, session, count, status):
        with self._lock:
            callback = session.feedback if session.reached_gate else None
        if callback is not None:
            callback(count, status)

    def _cancelled(self, session) -> bool:
        with self._lock:
            if session.expired:
                return True
            callback = session.cancel if session.reached_gate else None
        return bool(callback is not None and callback())

    def _display(self, session, text):
        with self._lock:
            if not session.reached_gate:
                session.display_result = text  # sent once harvest starts
                return
            callback = session.display
        if callback is not None:
            callback(text)

    @staticmethod
    def _expire_locked(session: _Session) -> None:
        if not session.claimed:
            session.expired = True
            session.start.set()

    # --- /harvest side --------------------------------------------------------

    def harvest(
        self,
        target_count,
        feedback_callback=None,
        cancel_callback=None,
        display_result_callback=None,
    ):
        """Return run_harvest's result (or raise its error) for one goal."""
        with self._lock:
            if self._harvesting:
                raise RuntimeError('another harvest is already running')
            self._harvesting = True
            session, self._session = self._session, None  # consumed
            usable = (
                session is not None
                and not session.expired
                and not session.done.is_set()
            )
            if usable:
                session.claimed = True
                session.feedback = feedback_callback
                session.cancel = cancel_callback
                session.display = display_result_callback
        try:
            if usable:
                self._log('/harvest: using pre-scan (waiting if still scanning)')
                session.start.set()
                session.done.wait()  # scan + harvest in the worker thread
                if session.reached_gate:
                    if session.error is not None:
                        raise session.error
                    return session.result
                self._log('/harvest: pre-scan unusable; normal scan -> harvest')
            else:
                self._log('/harvest: no usable pre-scan; normal scan -> harvest')
            with self._omx_lock:
                return self._run_harvest(
                    target_count=target_count,
                    feedback_callback=feedback_callback,
                    cancel_callback=cancel_callback,
                    display_result_callback=display_result_callback,
                )
        finally:
            with self._lock:
                self._harvesting = False

    def shutdown(self) -> None:
        with self._lock:
            session, self._session = self._session, None
            if session is not None:
                self._expire_locked(session)
