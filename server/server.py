import socket
import threading
import json
import sys
import queue

PORT = 5000

def send_msg(sock: socket.socket, msg: dict):
    raw = json.dumps(msg) + "\n"
    sock.sendall(raw.encode())
    print(f"  → sent {raw.strip()}")

def recv_msg(buf: list, sock: socket.socket) -> dict | None:
    while True:
        if "\n" in "".join(buf):
            break
        chunk = sock.recv(4096).decode(errors="replace")
        if not chunk:
            return None
        buf.append(chunk)

    joined = "".join(buf)
    idx    = joined.index("\n")
    line   = joined[:idx]
    buf.clear()
    buf.append(joined[idx + 1:])
    return json.loads(line)

class GameSession(threading.Thread):

    def __init__(self, sock1: socket.socket, sock2: socket.socket):
        super().__init__(daemon=True)
        self.socks  = [sock1, sock2]
        self.buf    = [[], []]
        self.q      = [queue.Queue(), queue.Queue()]
        self.scores = [0, 0]
        self.final  = [None, None]

    def _reader(self, idx: int):
        buf = self.buf[idx]
        try:
            while True:
                msg = recv_msg(buf, self.socks[idx])
                if msg is None:
                    self.q[idx].put(None)
                    break
                self.q[idx].put(msg)
        except Exception as e:
            print(f"[reader {idx}] error: {e}")
            self.q[idx].put(None)

    def run(self):
        for i in range(2):
            try:
                hello = recv_msg(self.buf[i], self.socks[i])
                name = hello.get("payload", {}).get("name", f"Player{i+1}") if hello else f"Player{i+1}"
                print(f"[session] player {i} says HELLO as '{name}'")
            except Exception as e:
                print(f"[session] error reading HELLO from player {i}: {e}")

        for i in range(2):
            t = threading.Thread(target=self._reader, args=(i,), daemon=True)
            t.start()

        try:
            self._send_initial_turn_info()

            while True:
                for sender_idx in range(2):
                    receiver_idx = 1 - sender_idx
                    try:
                        msg = self.q[sender_idx].get_nowait()
                    except queue.Empty:
                        continue

                    if msg is None:
                        print(f"[session] player {sender_idx} disconnected")
                        self._send_disconnect(receiver_idx)
                        return

                    mtype   = msg.get("type", "")
                    payload = msg.get("payload", {})
                    print(f"[session] p{sender_idx} → {mtype}")

                    if mtype == "END":
                        if payload.get("concede") or payload.get("timeout"):
                            self._send_concede_results(sender_idx, receiver_idx,
                                                       bool(payload.get("timeout")))
                            return

                    if mtype in ("ROLL", "SELECT"):
                        send_msg(self.socks[receiver_idx], msg)

                    if mtype == "SELECT":
                        grand = payload.get("grand", 0)
                        self.scores[sender_idx] = grand
                        if payload.get("gameOver"):
                            self.final[sender_idx] = grand

                    if self.final[0] is not None and self.final[1] is not None:
                        self._send_final_results()
                        return

        except Exception as e:
            print(f"[session] error: {e}")
        finally:
            for s in self.socks:
                try:
                    s.close()
                except Exception:
                    pass

    def _send_initial_turn_info(self):
        send_msg(self.socks[0], {"type": "MATCHED", "payload": {"yourTurn": True}})
        send_msg(self.socks[1], {"type": "MATCHED", "payload": {"yourTurn": False}})

    def _send_concede_results(self, conceding: int, opponent: int, timeout: bool):
        cs = self.scores[conceding]
        os = self.scores[opponent]

        loser_reason  = "Time-out"           if timeout else "You conceded"
        winner_reason = "Opponent timed-out" if timeout else "Opponent conceded"

        send_msg(self.socks[conceding], {
            "type": "END",
            "payload": {
                "yourScore": cs, "opponentScore": os,
                "winner": "Opponent", "reason": loser_reason, "concede": True
            }
        })
        send_msg(self.socks[opponent], {
            "type": "END",
            "payload": {
                "yourScore": os, "opponentScore": cs,
                "winner": "You", "reason": winner_reason, "concede": False
            }
        })

    def _send_final_results(self):
        s0, s1 = self.final
        for i, (my, opp) in enumerate([(s0, s1), (s1, s0)]):
            winner = "You" if my > opp else ("Opponent" if my < opp else "Tie")
            send_msg(self.socks[i], {
                "type": "END",
                "payload": {"yourScore": my, "opponentScore": opp, "winner": winner}
            })

    def _send_disconnect(self, notify_idx: int):
        try:
            send_msg(self.socks[notify_idx], {
                "type": "END",
                "payload": {"reason": "Opponent disconnected."}
            })
        except Exception:
            pass

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    lobby: list[socket.socket] = []
    lock  = threading.Lock()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", port))
    server.listen(10)
    print(f"[server] Yahtzee server listening on port {port}")

    while True:
        conn, addr = server.accept()
        print(f"[server] connection from {addr}")

        with lock:
            lobby.append(conn)
            print(f"[server] lobby size = {len(lobby)}")
            if len(lobby) >= 2:
                p1 = lobby.pop(0)
                p2 = lobby.pop(0)
                print("[server] starting game session")
                GameSession(p1, p2).start()

if __name__ == "__main__":
    main()
