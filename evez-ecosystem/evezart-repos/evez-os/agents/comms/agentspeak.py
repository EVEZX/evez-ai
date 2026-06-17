from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from enum import IntEnum
from hashlib import sha3_256
from typing import Any

MAGIC = int.from_bytes(b"EVEZ", "big")
VERSION = 1
HASH_SIZE = 32
HEADER_STRUCT = struct.Struct("!I B B 32s 32s Q")


class MessageType(IntEnum):
    HELLO = 1
    HEARTBEAT = 2
    MEMORY_SYNC = 3
    EVOLUTION_BROADCAST = 4
    DREAM_SHARE = 5
    SIGNAL_RELAY = 6
    MERGE_REQUEST = 7


@dataclass(slots=True)
class AgentSpeakMessage:
    msg_type: MessageType
    sender_node_id: str
    recipient_node_id: str
    timestamp_ns: int
    payload: dict[str, Any]


def _norm_node_id(node_id: str) -> bytes:
    raw = node_id.encode("utf-8")[:32]
    return raw.ljust(32, b"\x00")


def _denorm_node_id(raw: bytes) -> str:
    return raw.rstrip(b"\x00").decode("utf-8")


def _checksum(header_no_hash: bytes, payload_bytes: bytes) -> bytes:
    return sha3_256(header_no_hash + payload_bytes).digest()


def encode_message(message: AgentSpeakMessage) -> bytes:
    payload_bytes = json.dumps(message.payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    header_no_hash = HEADER_STRUCT.pack(
        MAGIC,
        VERSION,
        int(message.msg_type),
        _norm_node_id(message.sender_node_id),
        _norm_node_id(message.recipient_node_id),
        int(message.timestamp_ns),
    )
    checksum = _checksum(header_no_hash, payload_bytes)
    payload_size = struct.pack("!I", len(payload_bytes))
    return header_no_hash + checksum + payload_size + payload_bytes


def decode_message(raw: bytes) -> AgentSpeakMessage:
    min_size = HEADER_STRUCT.size + HASH_SIZE + 4
    if len(raw) < min_size:
        raise ValueError("Message too short")

    header_no_hash = raw[: HEADER_STRUCT.size]
    magic, version, msg_type, sender, recipient, timestamp_ns = HEADER_STRUCT.unpack(header_no_hash)
    if magic != MAGIC:
        raise ValueError("Invalid magic")
    if version != VERSION:
        raise ValueError("Unsupported version")

    checksum = raw[HEADER_STRUCT.size : HEADER_STRUCT.size + HASH_SIZE]
    payload_len = struct.unpack("!I", raw[HEADER_STRUCT.size + HASH_SIZE : min_size])[0]
    payload_bytes = raw[min_size : min_size + payload_len]
    if len(payload_bytes) != payload_len:
        raise ValueError("Invalid payload size")

    expected = _checksum(header_no_hash, payload_bytes)
    if checksum != expected:
        raise ValueError("Checksum mismatch")

    payload = json.loads(payload_bytes.decode("utf-8"))
    return AgentSpeakMessage(
        msg_type=MessageType(msg_type),
        sender_node_id=_denorm_node_id(sender),
        recipient_node_id=_denorm_node_id(recipient),
        timestamp_ns=timestamp_ns,
        payload=payload,
    )
