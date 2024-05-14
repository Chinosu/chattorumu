from enum import Enum, auto
from typing import Tuple, TypeAlias


class PacketType(Enum):
    JOIN = auto()
    MESSAGE = auto()
    PLAIN = auto()
    COMMAND_RESULT = auto()
    ERROR = auto()


Packet: TypeAlias = Tuple[PacketType, str]


def encode(packet: Packet) -> bytes:
    return f"{packet[0].value}{packet[1]}".encode()


def decode(data: bytes) -> Packet:
    data = data.decode()
    return PacketType(int(data[0])), data[1:]
