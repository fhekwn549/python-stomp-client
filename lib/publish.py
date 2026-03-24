"""
메시지 발행 모듈.

STOMP SEND 프레임을 생성하여 서버로 전송한다.
dict/list는 자동으로 JSON 직렬화된다.
"""

import logging

import stomper

from . import json_codec
from .connection import StompConnection

logger = logging.getLogger(__name__)


class PublishService:
    """메시지 발행 담당. dict를 넘기면 자동으로 JSON으로 변환한다."""

    def __init__(self, connection: StompConnection):
        self._conn = connection

    def send(self, destination: str, body) -> bool:
        """메시지를 발행한다.

        Args:
            destination: STOMP destination (예: "/app/python")
            body: 메시지 본문. dict/list면 JSON으로 자동 변환.

        Returns:
            전송 성공 여부.
        """
        encoded = json_codec.encode(body)
        send_frame = stomper.send(destination, encoded, content_type="application/json")
        success = self._conn.send_frame(send_frame)
        if success:
            logger.info("송신: %s → %s", destination, encoded)
        return success
