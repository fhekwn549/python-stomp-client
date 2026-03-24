"""
ex02: 타이머 pub/sub 예제.

5초마다 현재 시간을 JSON으로 발행하고,
수신 메시지를 화면에 출력한다.

실행:
    python examples/ex02/main.py
"""

import json
import logging
import sys
import time
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


def timer_loop():
    """5초마다 현재 시간을 발행."""
    while True:
        time.sleep(5)
        if client.connected:
            client.publish(TOPIC_PUB, {
                "type": "time",
                "timestamp": time.time(),
                "datetime": time.strftime("%Y-%m-%d %H:%M:%S"),
            })


client.subscribe(TOPIC_SUB)
client.on_message(on_message)
client.on_connected(lambda: threading.Thread(target=timer_loop, daemon=True).start())

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    print(f"5초마다 시간 발행 ({TOPIC_PUB}), 수신 대기 ({TOPIC_SUB})")
    client.run()
