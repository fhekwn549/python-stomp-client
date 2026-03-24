"""
STOMP 클라이언트 고수준 API.

Connection + Publish + Subscribe를 통합한 래퍼 클래스.
JSON 직렬화/역직렬화가 자동으로 처리된다.
"""

import logging
import signal

from .config import BrokerConfig
from .connection import StompConnection
from .publish import PublishService
from .subscribe import SubscribeService

logger = logging.getLogger(__name__)


class StompClient:
    """STOMP 클라이언트. 모든 pub/sub이 JSON 객체 기반으로 동작한다.

    사용법:
        client = StompClient()
        client.subscribe("/topic/python")
        client.on_message(lambda dest, body, headers: print(body))
        client.run()
    """

    def __init__(self, broker: BrokerConfig = None,
                 reconnect_interval: float = 3.0):
        """
        Args:
            broker: 브로커 설정. None이면 환경변수에서 자동 로드.
            reconnect_interval: 재연결 대기 시간 (초)
        """
        if broker is None:
            broker = BrokerConfig.from_env()
        self._broker = broker
        self._conn = StompConnection(broker, reconnect_interval=reconnect_interval)
        self._pub = PublishService(self._conn)
        self._sub = SubscribeService(self._conn)
        self._on_connected_callbacks: list = []
        self._subscriptions: list = []

    @property
    def connected(self) -> bool:
        """현재 STOMP 연결 상태."""
        return self._conn.connected

    def subscribe(self, topic: str):
        """토픽 구독을 등록한다. 연결 전에 호출해도 연결 후 자동 구독된다."""
        self._subscriptions.append(topic)

    def on_message(self, callback):
        """메시지 수신 콜백을 등록한다.

        callback(destination: str, body: dict|str, headers: dict)
        """
        self._sub.on_message(callback)

    def on_connected(self, callback):
        """연결 성공 시 호출할 콜백을 등록한다."""
        self._on_connected_callbacks.append(callback)

    def publish(self, destination: str, data) -> bool:
        """메시지를 발행한다. dict/list는 자동으로 JSON 직렬화된다."""
        return self._pub.send(destination, data)

    def run(self):
        """클라이언트를 시작한다. 블로킹이며, Ctrl+C로 종료 가능."""
        self._conn.on_connected(self._handle_connected)

        logger.info("=" * 50)
        logger.info("  STOMP Client")
        logger.info("  서버: %s", self._broker.url)
        logger.info("  구독: %s", self._subscriptions)
        logger.info("=" * 50)

        signal.signal(signal.SIGINT, lambda *_: self.stop())
        self._conn.run()

    def stop(self):
        """클라이언트를 종료한다."""
        self._conn.stop()

    def _handle_connected(self):
        """연결 성공 시 등록된 토픽 자동 구독 + 콜백 호출."""
        for topic in self._subscriptions:
            self._sub.subscribe(topic)
        for cb in self._on_connected_callbacks:
            cb()
