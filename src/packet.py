from enum import Enum, auto
from dataclasses import dataclass


class PacketType(Enum):
    JOIN = auto()
    LEAVE = auto()
    COMMAND = auto()
    ERROR = auto()
    MESSAGE = auto()
    OTHER = auto()


@dataclass(frozen=True)
class Packet:
    type: PacketType
    content: str


def encode(packet: Packet):
    return f"{packet.type.value}{packet.content}".encode()


def decode(data: bytes):
    data = data.decode()
    return Packet(PacketType(int(data[0])), data[1:])
