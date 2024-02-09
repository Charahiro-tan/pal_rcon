import struct
from dataclasses import dataclass, field

CHARACTER_CODE = "ascii"


@dataclass(slots=True)
class CommandPacket:
    packet_id: int
    packet_type: int
    message: str
    raw_message: bytes | None = field(default=None)

    def pack_message(self) -> bytes:
        cmd_bytes = self.message.encode(CHARACTER_CODE)
        return (
            struct.pack("<III", len(cmd_bytes) + 10, self.packet_id, self.packet_type)
            + cmd_bytes
            + b"\x00\x00"
        )


@dataclass(slots=True)
class CommandResponse(CommandPacket):
    send_command: CommandPacket | None = field(default=None)
    is_successful: bool = field(default=False)

    def __bool__(self):
        return self.is_successful


@dataclass(slots=True)
class Player:
    name: str
    player_uid: str
    steam_id: str


@dataclass(slots=True)
class PlayerlistResponse(CommandResponse):
    players: list[Player] = field(default_factory=list)
    invalid_uid_players: list[str] = field(default_factory=list)

    def __iter__(self):
        return iter(self.players)

    @classmethod
    def from_response(cls, packet: CommandResponse) -> "PlayerlistResponse":
        players = []
        invalid_uid_players = []
        is_successful = True
        for line in packet.message.splitlines():
            if line == "name,playeruid,steamid":
                continue
            name, player_uid, steam_id = line.split(",")
            if player_uid == "00000000":
                invalid_uid_players.append(Player(name, player_uid, steam_id))
                is_successful = False
                continue
            players.append(Player(name, player_uid, steam_id))
        return cls(
            packet.packet_id,
            packet.packet_type,
            packet.message,
            packet.raw_message,
            packet.send_command,
            is_successful,
            players,
            invalid_uid_players,
        )
