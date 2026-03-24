"""
메시지 큐 모듈.

모든 메시지를 큐에 저장하고, 워커 스레드가 순서대로 전송한다.
연결이 끊긴 상태에서는 큐에 쌓아두고, 재연결 시 자동으로 재전송한다.
"""

import logging
import threading
import time
from collections import deque

from .publish import PublishService

logger = logging.getLogger(__name__)


class QueueManager:
    """오프라인 메시지 큐. 워커 스레드 기반 FIFO 전송."""

    def __init__(self, publish_service: PublishService, retry_interval: float = 1.0):
        self._pub = publish_service
        self._queue: deque = deque()
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._retry_interval = retry_interval
        self._running = True

        self._worker = threading.Thread(target=self._process_queue, daemon=True)
        self._worker.start()

    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self._queue)

    def send_or_queue(self, destination: str, body) -> bool:
        """메시지를 큐에 저장한다. 워커 스레드가 순서대로 전송."""
        self._enqueue(destination, body)
        return True

    def flush(self):
        """큐에 메시지가 있으면 워커 스레드를 즉시 깨운다."""
        with self._lock:
            count = len(self._queue)
        if count > 0:
            logger.info("큐 전송: 밀린 메시지 %d건 전송 시작", count)
        self._event.set()

    def stop(self):
        """워커 스레드를 정지한다."""
        self._running = False
        self._event.set()

    def _enqueue(self, destination: str, body):
        with self._lock:
            self._queue.append((destination, body))
            logger.debug("큐 저장: 대기 %d건 → %s", len(self._queue), body)
        self._event.set()

    def _process_queue(self):
        while self._running:
            self._event.wait()
            self._event.clear()

            while self._running:
                with self._lock:
                    if not self._queue:
                        break
                    destination, body = self._queue.popleft()

                success = self._pub.send(destination, body)
                if not success:
                    with self._lock:
                        self._queue.appendleft((destination, body))
                    logger.warning("큐 재전송 실패, %s초 후 재시도", self._retry_interval)
                    time.sleep(self._retry_interval)
