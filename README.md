# Python STOMP Client

WebSocket 기반 STOMP 클라이언트 라이브러리. Spring Boot STOMP 서버와 JSON 메시지를 송수신합니다.

## 구조

```
python-stomp-client/
├── lib/                        # 라이브러리
│   ├── client.py               #   StompClient (고수준 API)
│   ├── connection.py           #   StompConnection (WebSocket + STOMP)
│   ├── publish.py              #   PublishService (메시지 발행)
│   ├── subscribe.py            #   SubscribeService (토픽 구독)
│   ├── queue_manager.py        #   QueueManager (오프라인 큐)
│   ├── config.py               #   BrokerConfig (설정)
│   └── json_codec.py           #   JSON 직렬화/역직렬화
│
├── examples/                   # 예제
│   ├── ex01/                   #   간단 pub/sub (stdin → 발행, 수신 → 출력)
│   ├── ex02/                   #   타이머 pub/sub (5초마다 시간 발행)
│   └── ex03/                   #   action 기반 구독 (action 필드별 처리)
│
├── .env.example                # 환경변수 템플릿
└── requirements.txt
```

## 설치

```bash
pip install -r requirements.txt
```

## 설정

환경변수로 서버 정보를 설정합니다:

```bash
cp .env.example .env
# .env 파일에서 STOMP_URL 등을 수정
```

| 환경변수 | 기본값 | 설명 |
|----------|--------|------|
| `STOMP_URL` | `ws://localhost:9030/stomp/websocket` | WebSocket URL |
| `STOMP_USER` | `guest` | 인증 사용자 |
| `STOMP_PASSWORD` | `guest` | 인증 비밀번호 |

## 사용법

```python
from lib import StompClient

client = StompClient()  # 환경변수에서 자동 설정

# 구독 (수신 메시지는 자동으로 JSON → dict 변환)
client.subscribe("/topic/python")
client.on_message(lambda dest, body, headers: print(body))

# 발행 (dict는 자동으로 JSON 직렬화)
client.on_connected(lambda: client.publish("/app/python", {"type": "hello"}))

# 실행 (Ctrl+C로 종료, 자동 재연결)
client.run()
```

## JSON 자동 처리

라이브러리가 직렬화/역직렬화를 자동으로 처리합니다:

- **발행**: `dict`/`list` → JSON 문자열로 자동 변환
- **수신**: JSON 문자열 → `dict`/`list`로 자동 변환

```python
# 발행: dict를 넘기면 자동으로 JSON
client.publish("/app/python", {"sensor": "lidar", "value": 2.5})

# 수신: handler의 body는 자동으로 dict
def handler(destination, body, headers):
    print(body["sensor"])  # "lidar"
    print(body["value"])   # 2.5
```

## 예제 실행

```bash
# ex01: 키보드 입력 → 발행, 수신 → 화면 출력
python3 examples/ex01/main.py

# ex02: 5초마다 시간 발행, 수신 → 화면 출력
python3 examples/ex02/main.py

# ex03: action 필드별 처리 (구독 전용)
python3 examples/ex03/main.py
```

### ex01: 간단 pub/sub

stdin에서 한 줄씩 읽어 JSON으로 발행하고, 수신 메시지를 화면에 출력합니다.

### ex02: 타이머 pub/sub

5초마다 현재 시간을 JSON으로 발행하고, 수신 메시지를 화면에 출력합니다.

### ex03: action 기반 구독

수신 메시지의 `action` 필드에 따라 다른 처리를 합니다. 웹에서 아래 메시지를 보내 테스트할 수 있습니다:

```json
{"action": "greet", "name": "홍길동"}
{"action": "status"}
{"action": "echo", "message": "안녕하세요"}
```

## 직접 설정 (환경변수 없이)

```python
from lib import StompClient, BrokerConfig

client = StompClient(
    broker=BrokerConfig(
        url="ws://your-server:9030/stomp/websocket",
        user="admin",
        password="secret",
    )
)
```
