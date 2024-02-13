import logging
import socket
import struct
import time

from .errors import (
    AuthenticationFailedError,
    IncompleteMessageError,
    InvalidPacketError,
    PalRconError,
)
from .models import CommandPacket, CommandResponse, PlayerlistResponse
from .utils import check_max_attempts, generate_packet_id, get_initial, safe_message

logger = logging.getLogger(__name__)


class Rcon:
    def __init__(self, host: str, port: int, password: str) -> None:
        self.host = host
        self.port = port
        self.password = password

        self._sock = None

    def connect(self) -> None:
        self._sock = socket.create_connection((self.host, self.port))
        self._authenticate()

    def _authenticate(self) -> None:
        packet_id = generate_packet_id()
        cmd = CommandPacket(packet_id, 3, self.password)
        self._send_command(cmd)
        self._receive_response(cmd)
        logger.debug(f"Successful login: {self.host}:{self.port}")

    def disconnect(self):
        if self._sock:
            self._sock.close()
        self._sock = None
        logger.debug(f"Disconnected from {self.host}:{self.port}")

    def execute_command(self, command: str | list) -> CommandResponse:
        packet_id = generate_packet_id()
        command = command if isinstance(command, str) else " ".join(command)
        if command.startswith("/"):
            command = command[1:]
        cmd = CommandPacket(packet_id, 2, command)
        self._send_command(cmd)
        return self._receive_response(cmd)

    def _send_command(self, command: CommandPacket) -> None:
        logger.debug(
            f"Sending message: packet_id={command.packet_id}, "
            + f"packet_type={command.packet_type}, "
            + f"message={command.message if command.message != self.password else '**Password**'}",
        )
        if self._sock is None:
            raise ConnectionError("Not connected to the server")
        packed_message = command.pack_message()
        self._sock.sendall(packed_message)

    def _receive_response(self, send_command: CommandPacket) -> CommandResponse:
        if self._sock is None:
            raise ConnectionError("Not connected to the server")
        len_bytes = self._sock.recv(4)
        length = struct.unpack("<I", len_bytes)[0]
        response = self._sock.recv(length)
        packet_id, response_type = struct.unpack("<iI", response[:8])
        message, null = response[8:-2], response[-2:]
        logger.debug(f"Received message: {packet_id=}, {response_type=}, {message=}")

        if packet_id != send_command.packet_id:
            logger.debug(
                "Received packets have different IDs"
                + f"(send: {send_command.packet_id}, recv: {packet_id})"
            )

        if packet_id == -1:
            raise AuthenticationFailedError("Failed to authenticate with the server")

        if null != b"\x00\x00":
            raise InvalidPacketError("Received message is not a valid RCON packet")

        if message and not message.endswith(b"\n"):
            raise IncompleteMessageError(
                "Received message does not end with a newline", message
            )

        return CommandResponse(
            packet_id,
            response_type,
            message.decode()[:-1],
            len_bytes + response,
            send_command,
        )


class PalRcon(Rcon):
    def __init__(self, host: str, port: int, password: str) -> None:
        super().__init__(host, port, password)

    def __enter__(self) -> "PalRcon":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.disconnect()

    def connect(self, max_attempts: int | None = 3) -> None:
        if max_attempts is None or max_attempts < 1:
            max_attempts = 1
        attempt = 1
        while attempt <= max_attempts:
            try:
                super().connect()
                return
            except (ConnectionError, AuthenticationFailedError):
                if attempt == max_attempts:
                    raise
                logger.debug(f"Connect Retrying... {attempt + 1}/{max_attempts}")
                time.sleep(attempt)
                attempt += 1
        raise PalRconError(f"Failed to connect after {max_attempts} attempts")

    def execute_command(
        self, command: str | list, max_attempts: int | None = 1
    ) -> CommandResponse:
        max_attempts = check_max_attempts(max_attempts)
        attempt = 1
        reconnetct_attempt = False
        while attempt <= max_attempts:
            try:
                res = super().execute_command(command)
                if isinstance(command, list):
                    cmd = command[0].replace("/", "").lower()
                else:
                    cmd = command.split(" ")[0].replace("/", "").lower()
                initial = get_initial(cmd)
                if res.message.startswith(initial):
                    res.is_successful = True
                return res
            except (ConnectionError, AuthenticationFailedError):
                if reconnetct_attempt:
                    raise
                try:
                    logger.debug("Reconnecting... 1/1")
                    self.connect(max_attempts=1)
                    reconnetct_attempt = True
                    continue
                except (ConnectionError, AuthenticationFailedError):
                    raise
            except (IncompleteMessageError, InvalidPacketError):
                if attempt == max_attempts:
                    raise
                logger.debug(f"Retrying... {attempt + 1}/{max_attempts}")
                time.sleep(1)
                attempt += 1
        raise PalRconError("Failed to execute command")

    def send_shutdown(
        self,
        seconds: int | None = 1,
        message: str | None = "",
        send_save: bool | None = False,
        max_attempts: int | None = 1,
    ) -> CommandResponse:
        if seconds is None or seconds < 1:
            seconds = 1
        if message is None:
            message = ""
        if send_save is None:
            send_save = False

        if send_save:
            self.send_save()
            seconds = max(5, seconds)
        shutdown_command = f"shutdown {max(1, seconds)}"
        if message:
            shutdown_command += f" {safe_message(message)}"
        return self.execute_command(shutdown_command, max_attempts)

    def send_do_exit(self, max_attempts: int | None = 1) -> CommandResponse:
        try:
            return self.execute_command("doexit", max_attempts)
        except ConnectionError:
            self.disconnect()
            raise

    def send_broadcast(
        self, message: str, max_attempts: int | None = 1
    ) -> CommandResponse:
        broadcast_command = f"broadcast {safe_message(message)}"
        return self.execute_command(broadcast_command, max_attempts)

    def send_kick_player(
        self, steam_id: str | int, max_attempts: int | None = 1
    ) -> CommandResponse:
        kick_command = f"kickplayer {steam_id}"
        return self.execute_command(kick_command, max_attempts)

    def send_ban_player(
        self, steam_id: str | int, max_attempts: int | None = 1
    ) -> CommandResponse:
        ban_command = f"banplayer {steam_id}"
        return self.execute_command(ban_command, max_attempts)

    def send_show_players(self, max_attempts: int | None = 10) -> PlayerlistResponse:
        if max_attempts is None:
            max_attempts = 10
        res = self.execute_command("showplayers", max_attempts)
        return PlayerlistResponse.from_response(res)

    def send_info(self, max_attempts: int | None = 1) -> CommandResponse:
        return self.execute_command("info", max_attempts)

    def send_save(self, max_attempts: int | None = 1) -> CommandResponse:
        return self.execute_command("save", max_attempts)
