"""
server.py  –  Shinobi Tactics Game Server
Handles 2 clients, manages turns, HP, and broadcasts game state.
Run:  python server.py
"""

import socket
import threading
import pickle
import struct
import time
import sys
import os
import uuid
from combat_rules import CHARACTERS, initial_resources, unavailable, resolve

# ── Constants ──────────────────────────────────────────────────────
HOST = os.environ.get("SHINOBI_HOST", "0.0.0.0")
PORT = int(os.environ.get("SHINOBI_PORT", "5555"))
MAX_HP = 100

DAMAGE = {
    "ATTACK":   15,
    "JUTSU":    25,
    "ULTIMATE": 50,
}
HEAL_AMOUNT = 20


# ── Helpers ────────────────────────────────────────────────────────
def send_msg(conn: socket.socket, obj):
    """Send a pickle-serialised object with a 4-byte length prefix."""
    data = pickle.dumps(obj)
    length = struct.pack("!I", len(data))
    try:
        conn.sendall(length + data)
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass


def recv_msg(conn: socket.socket):
    """Receive a length-prefixed pickle message. Returns None on failure."""
    try:
        raw_len = _recv_exact(conn, 4)
        if raw_len is None:
            return None
        msg_len = struct.unpack("!I", raw_len)[0]
        raw_data = _recv_exact(conn, msg_len)
        if raw_data is None:
            return None
        return pickle.loads(raw_data)
    except Exception:
        return None


def _recv_exact(conn, n):
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


# ── Game State ─────────────────────────────────────────────────────
class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.match_id = uuid.uuid4().hex
        self.action_id = 0
        self.resources = initial_resources()
        self.hp = {"P1": MAX_HP, "P2": MAX_HP}
        self.characters = {"P1": None, "P2": None}
        self.turn = "P1"
        self.phase = "WAITING"      # WAITING | SELECT | BATTLE | GAME_OVER
        self.winner = None
        self.last_action = None     # dict describing what just happened
        self.connected = {"P1": False, "P2": False}
        self.genjutsu_shield = {"P1": False, "P2": False}  # Active counter shield

    def record_action(self, data):
        self.action_id += 1
        self.last_action = {**data, "id": self.action_id}

    def snapshot(self):
        """Return a serialisable dict of the full state."""
        return {
            "match_id": self.match_id,
            "resources": self.resources,
            "rules_version": 2,
            "hp_p1":      self.hp["P1"],
            "hp_p2":      self.hp["P2"],
            "char_p1":    self.characters["P1"],
            "char_p2":    self.characters["P2"],
            "turn":       self.turn,
            "phase":      self.phase,
            "winner":     self.winner,
            "last_action": self.last_action,
            "p1_connected": self.connected["P1"],
            "p2_connected": self.connected["P2"],
            "genjutsu_shield_p1": self.genjutsu_shield["P1"],
            "genjutsu_shield_p2": self.genjutsu_shield["P2"],
        }


# ── Server ─────────────────────────────────────────────────────────
class GameServer:
    def __init__(self):
        self.state = GameState()
        self.conns = {"P1": None, "P2": None}
        self.lock = threading.Lock()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # ── networking ─────────────────────────────────────────────────
    def start(self):
        self.sock.bind((HOST, PORT))
        self.sock.listen(2)
        print(f"[SERVER] Listening on {HOST}:{PORT}")
        print("[SERVER] Waiting for 2 players …")

        player_num = 0
        while True:
            conn, addr = self.sock.accept()
            player_num += 1
            pid = "P1" if player_num % 2 == 1 else "P2"

            with self.lock:
                self.conns[pid] = conn
                self.state.connected[pid] = True

            print(f"[SERVER] {pid} connected from {addr}")

            # Tell the client which player they are
            send_msg(conn, {"type": "ASSIGN", "player_id": pid})

            t = threading.Thread(target=self.handle_client, args=(conn, pid), daemon=True)
            t.start()

            # Once both slots filled, move to SELECT phase
            with self.lock:
                if self.state.connected["P1"] and self.state.connected["P2"]:
                    if self.state.phase == "WAITING":
                        self.state.phase = "SELECT"
                        self._broadcast({"type": "STATE", **self.state.snapshot()})
                        print("[SERVER] Both players connected  →  SELECT phase")

    def handle_client(self, conn: socket.socket, pid: str):
        """Main loop for one client thread."""
        try:
            while True:
                msg = recv_msg(conn)
                if msg is None:
                    break  # disconnected
                self._process(msg, pid)
        except Exception as e:
            print(f"[SERVER] {pid} error: {e}")
        finally:
            self._disconnect(pid)

    def _disconnect(self, pid):
        with self.lock:
            self.state.connected[pid] = False
            self.conns[pid] = None
            print(f"[SERVER] {pid} disconnected")

            # Notify the other player
            other = "P2" if pid == "P1" else "P1"
            if self.conns[other]:
                send_msg(self.conns[other], {
                    "type": "OPPONENT_DISCONNECTED",
                    **self.state.snapshot(),
                })
            # Reset for next match
            self.state.reset()
            self.state.connected[other] = self.conns[other] is not None
            print("[SERVER] State reset, waiting for reconnection …")

    # ── game logic ─────────────────────────────────────────────────
    def _process(self, msg: dict, pid: str):
        action = msg.get("action")
        if action is None:
            return

        with self.lock:
            # ── Character selection ────────────────────────────────
            if action == "SELECT_CHAR":
                char_name = msg.get("character")
                if self.state.phase != "SELECT" or char_name not in CHARACTERS:
                    self._reject(pid, "Choose a valid character during selection")
                    return
                self.state.characters[pid] = char_name
                print(f"[SERVER] {pid} selected {char_name}")

                # If both selected, start battle
                if self.state.characters["P1"] and self.state.characters["P2"]:
                    self.state.phase = "BATTLE"
                    self.state.turn = "P1"
                    self.state.hp = {"P1": MAX_HP, "P2": MAX_HP}
                    self.state.winner = None
                    print("[SERVER] Both characters selected  →  BATTLE phase")

                self._broadcast({"type": "STATE", **self.state.snapshot()})
                return

            # ── Battle actions ─────────────────────────────────────
            if self.state.phase != "BATTLE":
                return
            if self.state.turn != pid:
                send_msg(self.conns[pid], {"type": "NOT_YOUR_TURN"})
                return

            other = "P2" if pid == "P1" else "P1"

            reason = unavailable(self.state.resources[pid], action, self.state.hp[pid])
            if reason:
                self._reject(pid, reason)
                return
            success = msg.get("success", True)
            if type(success) is not bool:
                self._reject(pid, "Invalid challenge result")
                return
            # Damage is always derived here; client-supplied dmg is ignored.
            self.state.record_action(resolve(self.state, pid, action, success))
            if self.state.hp[pid] <= 0:
                self.state.phase = "GAME_OVER"
                self.state.winner = other
                self._broadcast({"type": "STATE", **self.state.snapshot()})
                return

            # Check win condition
            if self.state.hp[other] <= 0:
                self.state.phase = "GAME_OVER"
                self.state.winner = pid
                print(f"[SERVER] {pid} wins!")
            else:
                # Switch turn
                self.state.turn = other

            self._broadcast({"type": "STATE", **self.state.snapshot()})

    def _reject(self, pid, reason):
        if self.conns[pid]:
            send_msg(self.conns[pid], {"type": "ACTION_REJECTED", "reason": reason})

    # ── broadcast to both clients ──────────────────────────────────
    def _broadcast(self, obj):
        for pid in ("P1", "P2"):
            c = self.conns[pid]
            if c:
                send_msg(c, obj)


# ── Main ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    server = GameServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down.")
        sys.exit(0)
