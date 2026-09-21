"""Minimal OSC 1.0 encoder + UDP sender (stdlib only).

Implements just what the phrase bus needs: address pattern plus int32,
float32, and string arguments. No third-party deps so the bridge can never
break on a missing pip package on a capture workstation.
"""

from __future__ import annotations

import socket
import struct


def _pad4(b: bytes) -> bytes:
    return b + (b"\x00" * ((4 - (len(b) % 4)) % 4))


def encode_message(address: str, args: list) -> bytes:
    if not address.startswith("/"):
        raise ValueError(f"OSC address must start with '/': {address!r}")
    out = bytearray()
    out += _pad4(address.encode("utf-8") + b"\x00")
    typetags = "," + "".join(
        "i" if isinstance(a, int) and not isinstance(a, bool)
        else "f" if isinstance(a, float)
        else "s" if isinstance(a, str)
        else (_ for _ in ()).throw(TypeError(f"unsupported OSC arg type: {type(a).__name__}"))
        for a in args
    )
    out += _pad4(typetags.encode("ascii") + b"\x00")
    for a in args:
        if isinstance(a, bool):
            raise TypeError("bools are not valid OSC args here")
        if isinstance(a, int):
            out += struct.pack(">i", a)
        elif isinstance(a, float):
            out += struct.pack(">f", a)
        elif isinstance(a, str):
            out += _pad4(a.encode("utf-8") + b"\x00")
    return bytes(out)


class OscUdpSender:
    def __init__(self, host: str, port: int, timeout: float = 2.0):
        self._addr = (host, port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.settimeout(timeout)

    def send(self, address: str, args: list) -> int:
        data = encode_message(address, args)
        return self._sock.sendto(data, self._addr)

    def close(self) -> None:
        self._sock.close()

    def __enter__(self) -> "OscUdpSender":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
