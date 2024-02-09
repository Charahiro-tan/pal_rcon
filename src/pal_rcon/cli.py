import argparse
import asyncio
import base64
import json
import logging
import os
from dataclasses import asdict

from . import __version__
from .async_pal_rcon import AsyncPalRcon
from .models import CommandResponse, PlayerlistResponse
from .pal_rcon import PalRcon


def rcon(
    host: str, port: int, password: str, command: str
) -> CommandResponse | PlayerlistResponse:
    cmd = command.split(" ")[0].replace("/", "").lower()
    with PalRcon(host, port, password) as rcon:
        if cmd == "showplayers":
            res = rcon.send_show_players()
        else:
            res = rcon.execute_command(command)
    return res


async def arcon(
    host: str, port: int, password: str, command: str
) -> CommandResponse | PlayerlistResponse:
    cmd = command.split(" ")[0].replace("/", "").lower()
    async with AsyncPalRcon(host, port, password) as rcon:
        if cmd == "showplayers":
            res = await rcon.send_show_players()
        else:
            res = await rcon.execute_command(command)
    return res


def custom_json_encoder(obj):
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode("utf-8")
    return obj


def main():
    password = os.getenv("RCON_PASSWORD")

    # fmt: off
    parser = argparse.ArgumentParser(prog="pal_rcon", description="RCON client for Palworld", add_help=False)

    parser.add_argument("--help", action="help", default=argparse.SUPPRESS, help="Show help")
    parser.add_argument("-h", "--host", help="The hostname of the server", required=True)
    parser.add_argument("-p", "--port", help="The port of the server", type=int, required=True)
    parser.add_argument("-P", "--password", help="The RCON password")
    parser.add_argument("-c", "--command", help="The command to send to the server", required=True,)
    parser.add_argument("--json", help="Output as JSON", action="store_true")
    parser.add_argument("-v", "--version", action="version", version=f"pal_rcon v{__version__}")
    parser.add_argument("--debug", help="Enable debug logging", action="store_true")
    parser.add_argument("-a", help="Use async RCON(debugging purpose)", action="store_true")
    # fmt: on

    args = parser.parse_args()

    password = password or args.password

    if args.debug and not args.json:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.a:
        res = asyncio.run(arcon(args.host, args.port, password, args.command))
    else:
        res = rcon(args.host, args.port, password, args.command)

    if args.json:
        res = asdict(res)
        print(json.dumps(res, default=custom_json_encoder))
        return
    print(asdict(res))
    print("\n" + res.message)
