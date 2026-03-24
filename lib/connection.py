"""
STOMP 연결 모듈.

WebSocket + STOMP 프로토콜의 연결/인증/재연결/종료를 관리한다.
모든 상태 플래그는 threading.Lock으로 보호되어 스레드 안전하다.
"""

import logging
import threading
import time

import stomper
import websocket

from .config import BrokerConfig

logger = logging.getLogger(__name__)


class StompConnection:
    """WebSocket + STOMP 연결 관리."""

    def __init__(self, broker: BrokerConfig, reconnect_interval: float = 3.0,
                 shutdown_timeout: float = 5.0):
        self._broker = broker
        self._reconnect_interval = reconnect_interval
        self._shutdown_timeout = shutdown_timeout

        self._ws = None
        self._connected = False
        self._running = True
        self._lock = threading.Lock()

        self._on_connected_callbacks: list = []
        self._on_frame_callbacks: list = []

    @property
    def connected(self) -> bool:
        with self._lock:
            return self._connected

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running

    def on_connected(self, callback):
        """STOMP CONNECTED 프레임 수신 시 호출할 콜백을 등록한다."""
        self._on_connected_callbacks.append(callback)

    def on_frame(self, callback):
        """모든 STOMP 프레임 수신 시 호출할 콜백을 등록한다."""
        self._on_frame_callbacks.append(callback)

    def send_frame(self, frame: str) -> bool:
        """STOMP 프레임을 WebSocket으로 전송한다."""
        with self._lock:
            if self._ws and self._connected:
                self._ws.send(frame)
                return True
            return False

    def _on_open(self, ws):
        connect_frame = stomper.connect(
            self._broker.user, self._broker.password, host="/"
        )
        ws.send(connect_frame)

    def _on_message(self, ws, message):
        frame = stomper.unpack_frame(message)
        command = frame.get("cmd", "")

        if command == "CONNECTED":
            with self._lock:
                self._connected = True
            logger.info("STOMP 연결 성공")
            for cb in self._on_connected_callbacks:
                cb()
        elif command == "ERROR":
            logger.error("STOMP 에러: %s", frame.get("body", ""))

        for cb in self._on_frame_callbacks:
            cb(frame)

    def _on_error(self, ws, error):
        if self._running:
            logger.error("WebSocket 에러: %s", error)

    def _on_close(self, ws, close_status, close_msg):
        with self._lock:
            self._connected = False
        if self._running:
            logger.warning("연결 끊김")

    def _connect_once(self):
        self._ws = websocket.WebSocketApp(
            self._broker.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        logger.info("%s 연결 시도...", self._broker.url)
        self._ws.run_forever()

    def run(self):
        """무한 재연결 루프. stop()이 호출되면 종료된다."""
        while self._running:
            try:
                self._connect_once()
            except websocket.WebSocketException as e:
                logger.error("WebSocket 연결 실패: %s", e)
            except OSError as e:
                logger.error("네트워크 오류: %s", e)
            except Exception as e:
                logger.error("예상치 못한 오류: %s", e)
            with self._lock:
                self._connected = False
            if self._running:
                logger.info("%s초 후 재연결 시도...", self._reconnect_interval)
                time.sleep(self._reconnect_interval)

    def stop(self):
        """정상 종료. DISCONNECT 프레임 전송 후 WebSocket을 닫는다."""
        logger.info("종료 중...")
        with self._lock:
            self._running = False

        if self._ws and self._connected:
            try:
                self._ws.send(stomper.disconnect())
            except (websocket.WebSocketException, OSError) as e:
                logger.warning("DISCONNECT 전송 실패: %s", e)

        if self._ws:
            def force_close():
                try:
                    if self._ws.sock:
                        self._ws.sock.close()
                except OSError:
                    pass

            timer = threading.Timer(self._shutdown_timeout, force_close)
            timer.start()
            try:
                self._ws.close()
            except (websocket.WebSocketException, OSError):
                pass
            timer.cancel()
