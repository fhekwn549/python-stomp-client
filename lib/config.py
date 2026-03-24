"""
브로커 설정 모듈.

STOMP 브로커 연결에 필요한 설정값을 관리한다.
환경변수 또는 직접 인자로 설정할 수 있다.
"""

import os
from dataclasses import dataclass


@dataclass
class BrokerConfig:
    """STOMP 브로커 연결 정보.

    Attributes:
        url: WebSocket 연결 URL (예: ws://localhost:9030/stomp/websocket)
        user: STOMP 인증 사용자명
        password: STOMP 인증 비밀번호
    """
    url: str = "ws://localhost:9030/stomp/websocket"
    user: str = "guest"
    password: str = "guest"

    def __post_init__(self):
        if not self.url or not self.url.strip():
            raise ValueError("url은 비어있을 수 없습니다")
        if not self.url.startswith(("ws://", "wss://")):
            raise ValueError(f"url은 ws:// 또는 wss://로 시작해야 합니다: {self.url}")

    @classmethod
    def from_env(cls) -> "BrokerConfig":
        """환경변수에서 설정을 읽어 BrokerConfig를 생성한다.

        환경변수:
            STOMP_URL: WebSocket URL (기본값: ws://localhost:9030/stomp/websocket)
            STOMP_USER: 인증 사용자명 (기본값: guest)
            STOMP_PASSWORD: 인증 비밀번호 (기본값: guest)
        """
        return cls(
            url=os.environ.get("STOMP_URL", "ws://localhost:9030/stomp/websocket"),
            user=os.environ.get("STOMP_USER", "guest"),
            password=os.environ.get("STOMP_PASSWORD", "guest"),
        )
