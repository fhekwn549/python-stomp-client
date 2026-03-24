"""
ex03: Action 기반 구독 전용 예제.

수신 메시지의 "action" 필드에 따라 다른 응답을 화면에 출력한다.
발행 없이 구독만 사용한다.

실행:
    python examples/ex03/main.py

테스트 메시지 예시 (웹 클라이언트에서 /app/python으로 전송):
    {"action": "greet", "name": "홍길동"}
    {"action": "status"}
    {"action": "echo", "message": "안녕하세요"}
"""

import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from lib import StompClient

TOPIC_SUB = "/topic/python"

client = StompClient()

# action 핸들러 레지스트리
ACTIONS = {}


def action(name):
    """action 핸들러를 등록하는 데코레이터."""
    def decorator(fn):
        ACTIONS[name] = fn
        return fn
    return decorator


@action("greet")
def handle_greet(body):
    name = body.get("name", "익명")
    print(f"  → 안녕하세요, {name}님!")


@action("status")
def handle_status(body):
    print(f"  → 시스템 정상 (시간: {time.strftime('%H:%M:%S')})")


@action("echo")
def handle_echo(body):
    message = body.get("message", "")
    print(f"  → {message}")


def on_message(destination, body, headers):
    """action 필드에 따라 등록된 핸들러를 호출한다."""
    if not isinstance(body, dict):
        print(f"[경고] JSON이 아닌 메시지: {body}")
        return

    act = body.get("action")
    print(f"[수신] action={act} | {json.dumps(body, ensure_ascii=False)}")

    handler = ACTIONS.get(act)
    if handler:
        handler(body)
    else:
        print(f"  → 알 수 없는 action: {act}")


client.subscribe(TOPIC_SUB)
client.on_message(on_message)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    print(f"Action 핸들러 대기 중 ({TOPIC_SUB})")
    print(f"  등록된 action: {', '.join(ACTIONS.keys())}")
    client.run()
