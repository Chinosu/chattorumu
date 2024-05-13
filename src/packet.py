from enum import Enum, auto
from typing import Tuple


class PacketType(Enum):
    JOIN = auto()
    PLAIN = auto()
    MESSAGE = auto()
    ERROR = auto()


def encode(packet: Tuple[PacketType, str]) -> bytes:
    return f"{packet[0].value}{packet[1]}".encode()


def decode(data: bytes) -> Tuple[PacketType, str]:
    data = data.decode()
    return PacketType(int(data[0])), data[1:]
