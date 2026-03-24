"""
토픽 구독 모듈.

STOMP SUBSCRIBE 프레임을 전송하고, 수신된 MESSAGE 프레임을
등록된 콜백 함수에 전달한다. JSON 역직렬화가 자동으로 수행된다.
"""

import logging

import stomper

from . import json_codec
from .connection import StompConnection

logger = logging.getLogger(__name__)


class SubscribeService:
    """토픽 구독 담당. 수신 메시지를 콜백 함수에 전달한다."""

    def __init__(self, connection: StompConnection):
        self._conn = connection
        self._callbacks: list = []
        self._sub_counter = 0
        self._conn.on_frame(self._handle_frame)

    def on_message(self, callback):
        """메시지 수신 콜백을 등록한다.

        callback(destination: str, body: dict|str, headers: dict)
        body는 JSON 자동 역직렬화된 dict. 파싱 실패 시 원본 문자열.
        """
        self._callbacks.append(callback)

    def subscribe(self, topic: str) -> str:
        """토픽을 구독한다.

        Returns:
            구독 ID (예: "sub-1")
        """
        self._sub_counter += 1
        sub_id = f"sub-{self._sub_counter}"
        sub_frame = stomper.subscribe(topic, sub_id, ack="auto")
        if self._conn.send_frame(sub_frame):
            logger.info("구독: %s (id=%s)", topic, sub_id)
        return sub_id

    def _handle_frame(self, frame: dict):
        """수신 프레임 처리. MESSAGE만 콜백에 전달한다."""
        if frame.get("cmd") != "MESSAGE":
            return

        destination = frame["headers"].get("destination", "?")
        raw_body = frame.get("body", "")
        headers = frame.get("headers", {})

        body = json_codec.decode(raw_body)

        for cb in self._callbacks:
            cb(destination, body, headers)
