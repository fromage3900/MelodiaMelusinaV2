"""Mock Blender Live Link server for testing UE connection on port 9876."""
import json
import socket
import struct
import threading
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
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    server.settimeout(120.0)
    print(f"[MockBlender] Listening on {HOST}:{PORT}")

    try:
        client, addr = server.accept()
        print(f"[MockBlender] UE connected from {addr}")
        send_message(
            client,
            "handshake",
            {"version": "3.3.1", "blender_version": "5.1.0", "scene_name": "TestScene"},
        )
        print("[MockBlender] Handshake sent")

        client.settimeout(30.0)
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                msg = receive_message(client)
                if msg is None:
                    break
                print(f"[MockBlender] Received: {msg}")
                if msg.get("type") == "ping":
                    send_message(client, "pong", {})
                    print("[MockBlender] Pong sent - test PASSED")
                    return 0
            except socket.timeout:
                continue
        print("[MockBlender] Timeout waiting for ping")
        return 1
    finally:
        server.close()


if __name__ == "__main__":
    raise SystemExit(main())
