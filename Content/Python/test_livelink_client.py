"""Test UE-side Live Link client against mock Blender server on port 9876."""
import json
import socket
import struct
import sys
import time

HOST = "127.0.0.1"
PORT = 9876


def send_message(sock, msg_type, data):
    message = json.dumps({"type": msg_type, "data": data})
    encoded = message.encode("utf-8")
    sock.sendall(struct.pack("!I", len(encoded)) + encoded)


def recv_exact(sock, num_bytes):
    data = b""
    while len(data) < num_bytes:
        chunk = sock.recv(num_bytes - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def receive_message(sock):
    raw_len = recv_exact(sock, 4)
    if not raw_len:
        return None
    length = struct.unpack("!I", raw_len)[0]
    data = recv_exact(sock, length)
    if not data:
        return None
    return json.loads(data.decode("utf-8"))


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10.0)
    sock.connect((HOST, PORT))
    print(f"[TestClient] Connected to {HOST}:{PORT}")

    msg = receive_message(sock)
    if not msg or msg.get("type") != "handshake":
        print(f"[TestClient] FAIL: expected handshake, got {msg}")
        return 1
    print(f"[TestClient] Handshake OK: {msg['data']}")

    send_message(sock, "ping", {})
    msg = receive_message(sock)
    if msg and msg.get("type") == "pong":
        print("[TestClient] Ping/pong OK - protocol verified")
        return 0

    print(f"[TestClient] FAIL: expected pong, got {msg}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
