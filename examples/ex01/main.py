"""
ex01: 간단한 pub/sub 예제.

구독한 토픽의 메시지를 화면에 출력하고,
키보드 입력을 JSON 메시지로 발행한다.

실행:
    python examples/ex01/main.py
"""

import json
import logging
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from lib import StompClient

TOPIC_SUB = "/topic/python"
TOPIC_PUB = "/app/python"

client = StompClient()


def on_message(destination, body, headers):
    """수신 메시지를 화면에 출력."""
    print(f"[수신] {json.dumps(body, ensure_ascii=False)}")


def input_loop():
    """stdin에서 한 줄씩 읽어 JSON 메시지로 발행."""
    print(f"메시지를 입력하세요 (발행: {TOPIC_PUB}, Ctrl+C 종료):")
    try:
        for line in sys.stdin:
            text = line.strip()
            if text:
                client.publish(TOPIC_PUB, {"type": "chat", "text": text})
    except EOFError:
        pass


client.subscribe(TOPIC_SUB)
client.on_message(on_message)
client.on_connected(lambda: threading.Thread(target=input_loop, daemon=True).start())

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    client.run()
