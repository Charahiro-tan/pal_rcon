import random


def generate_packet_id() -> int:
    return random.randint(1, 2**31 - 1)


def safe_message(message: str) -> str:
    return message.replace(" ", "_")


def check_max_attempts(max_attempts: int | None) -> int:
    if max_attempts is None or max_attempts < 1:
        return 1
    return max_attempts


def get_initial(command: str) -> str:
    command = command.lower()
    match command:
        case "shutdown":
            return "The"
        case "doexit":
            return "Shutdown"
        case "broadcast":
            return "Broadcasted:"
        case "kickplayer":
            return "Kicked:"
        case "banplayer":
            return "Baned:"
        case "showplayers":
            return "name"
        case "info":
            return "Welcome"
        case "save":
            return "Complete"
        case _:
            return ""
