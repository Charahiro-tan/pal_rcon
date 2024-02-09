class PalRconError(Exception):
    pass


class AuthenticationFailedError(PalRconError):
    pass


class InvalidPacketError(PalRconError):
    pass


class IncompleteMessageError(PalRconError):
    def __init__(self, message: str, raw_message: bytes = b""):
        super().__init__(message)
        self.raw_message = raw_message
