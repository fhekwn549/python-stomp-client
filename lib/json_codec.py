"""
JSON 직렬화/역직렬화 유틸리티.

발행 시 dict/list → JSON 문자열 변환,
수신 시 JSON 문자열 → dict/list 변환을 담당한다.
"""

import json
import logging

logger = logging.getLogger(__name__)


def encode(data) -> str:
    """Python 객체를 JSON 문자열로 직렬화한다.

    dict/list는 JSON 문자열로 변환하고, 그 외는 str()로 변환한다.
    한글이 깨지지 않도록 ensure_ascii=False를 사용한다.
    """
    if isinstance(data, (dict, list)):
        return json.dumps(data, ensure_ascii=False)
    return str(data)


def decode(raw: str):
    """JSON 문자열을 Python 객체로 역직렬화한다.

    파싱 실패 시 원본 문자열을 그대로 반환한다.
    """
    if not isinstance(raw, str) or not raw.strip():
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw
