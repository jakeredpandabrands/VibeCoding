"""COOL STUFF! — Blind auction party game."""

import json
import random
import string
import uuid
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, jsonify

# Constants
STARTING_BUDGET = 1000
ROUNDS = 10
SELL_MULTIPLIER = 0.75
MIN_PLAYERS = 2
MAX_PLAYERS = 8

# Load items
ITEMS_PATH = Path(__file__).parent / "items.json"
with open(ITEMS_PATH) as f:
    ALL_ITEMS = json.load(f)

app = Flask(__name__)

# In-memory game state: game_id -> game dict
games: dict[str, dict] = {}


GAME_CODE_LEN = 6
GAME_CODE_CHARS = string.ascii_uppercase + string.digits


def normalize_game_code(raw: str) -> str:
    """Uppercase, alphanumeric only."""
    return "".join(c for c in (raw or "").upper() if c in GAME_CODE_CHARS)[:GAME_CODE_LEN]


def player_id() -> str:
    """Generate player ID."""
    return str(uuid.uuid4())[:8]


def draw_items(count: int) -> list[dict]:
    """Shuffle and draw N items from the mega-list."""
    shuffled = random.sample(ALL_ITEMS, min(count, len(ALL_ITEMS)))
    return [dict(item) for item in shuffled]


def create_game(game_code: str, host_name: str) -> dict | None:
    """Create a new game with host-chosen code. Host auto-joins as first player. Returns game or None if code taken."""
    code = normalize_game_code(game_code)
    if len(code) < 4:
        return None
    if code in games:
        return None
    items = draw_items(ROUNDS)
    games[code] = {
        "id": code,
        "players": [],
        "items": items,
        "current_round": 0,
        "phase": "lobby",
        "budgets": {},
        "collections": {},
        "actions": {},
        "winner": None,
    }
    g = games[code]
    # Host auto-joins as first player
    p = add_player(code, host_name)
    return g if p else None


def get_game(gid: str) -> dict | None:
    """Get game by ID (game code). Normalizes for lookup."""
    return games.get(normalize_game_code(gid))


def add_player(gid: str, name: str) -> dict | None:
    """Add player to game. Returns player dict or None if full."""
    g = get_game(gid)
    if not g or len(g["players"]) >= MAX_PLAYERS:
        return None
    pid = player_id()
    g["players"].append({"id": pid, "name": name})
    g["budgets"][pid] = STARTING_BUDGET
    g["collections"][pid] = []
    return {"id": pid, "name": name}


def start_game(gid: str) -> bool:
    """Start game if enough players."""
    g = get_game(gid)
    if not g or len(g["players"]) < MIN_PLAYERS:
        return False
    g["phase"] = "play"
    g["current_round"] = 0
    g["actions"] = {}
    return True


def get_current_item(g: dict) -> dict | None:
    """Get current round's item."""
    if g["current_round"] >= len(g["items"]):
        return None
    return g["items"][g["current_round"]]


def all_actions_received(g: dict) -> bool:
    """Check if all active players have submitted."""
    item = get_current_item(g)
    if not item:
        return True
    # Players who are bidding or sitting out
    active = [
        p["id"]
        for p in g["players"]
        if p["id"] not in g["actions"]
    ]
    return len(active) == 0


def resolve_round(g: dict) -> None:
    """Process actions: sells, then bids. Winner pays, gets item."""
    actions = g["actions"]

    # Process sells first (75% of item value)
    for pid, act in actions.items():
        if act.get("sit_out") and act.get("sell_item") is not None:
            # Find item in collection
            coll = g["collections"][pid]
            sell_idx = act["sell_item"]
            if 0 <= sell_idx < len(coll):
                item = coll.pop(sell_idx)
                payout = int(item["value"] * SELL_MULTIPLIER)
                g["budgets"][pid] = g["budgets"][pid] + payout

    # Find bidders (those who didn't sit out or sat out without selling = no bid)
    bidders = [
        (pid, act["bid"])
        for pid, act in actions.items()
        if not act.get("sit_out") and "bid" in act
    ]

    item = get_current_item(g)
    if not item:
        return

    if bidders:
        # Highest bid wins. Tie: first submitter wins (dict order preserves insertion)
        winner_pid = max(bidders, key=lambda x: x[1])[0]
        winning_bid = max(b[1] for b in bidders)

        g["budgets"][winner_pid] -= winning_bid
        g["collections"][winner_pid].append(
            {"name": item["name"], "value": item["value"]}
        )
        g["winner"] = winner_pid
    else:
        g["winner"] = None  # No one bid

    g["phase"] = "reveal"
    g["resolved_item"] = item


def advance_from_reveal(gid: str) -> bool:
    """Advance to next round or end game."""
    g = get_game(gid)
    if not g or g["phase"] != "reveal":
        return False

    g["current_round"] += 1
    g["actions"] = {}
    g["resolved_item"] = None
    g["winner"] = None

    if g["current_round"] >= ROUNDS:
        g["phase"] = "ended"
        return True

    g["phase"] = "play"
    return True


def public_state(g: dict, player_id: str | None = None) -> dict:
    """Build state for client. Never expose budgets or winning bids."""
    players = [{"id": p["id"], "name": p["name"]} for p in g["players"]]

    # Leaderboard: total stuff value (no cash)
    leaderboard = []
    for p in g["players"]:
        pid = p["id"]
        total = sum(it["value"] for it in g["collections"][pid])
        leaderboard.append({"id": pid, "name": p["name"], "total_value": total})
    leaderboard.sort(key=lambda x: x["total_value"], reverse=True)

    current_item = None
    if g["phase"] == "play" and g["current_round"] < len(g["items"]):
        item = g["items"][g["current_round"]]
        current_item = {"name": item["name"]}

    my_action = g["actions"].get(player_id) if player_id else None

    # For reveal: show who won and item value (never the bid)
    resolved = None
    if g["phase"] == "reveal" and g.get("resolved_item"):
        winner = next((p for p in g["players"] if p["id"] == g["winner"]), None)
        resolved = {
            "item_name": g["resolved_item"]["name"],
            "item_value": g["resolved_item"]["value"],
            "winner_name": winner["name"] if winner else None,
        }

    # Has current player submitted?
    has_submitted = player_id in g["actions"] if player_id else False
    submitted_count = len(g["actions"])

    # Own bankroll only (never others')
    my_budget = g["budgets"].get(player_id) if player_id else None

    return {
        "game_id": g["id"],
        "phase": g["phase"],
        "current_round": g["current_round"],
        "rounds_total": ROUNDS,
        "players": players,
        "leaderboard": leaderboard,
        "current_item": current_item,
        "my_action": my_action,
        "has_submitted": has_submitted,
        "resolved": resolved,
        "my_collection": g["collections"].get(player_id, []) if player_id else [],
        "my_budget": my_budget,
        "all_submitted": all_actions_received(g),
        "submitted_count": submitted_count,
    }


# --- Routes ---

@app.route("/health")
def health():
    """Simple health check for Render and debugging."""
    return "ok", 200


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/game/create", methods=["POST"])
def game_create():
    game_code = (request.form.get("game_code") or "").strip()
    host_name = (request.form.get("host_name") or "Host").strip()
    if not host_name:
        host_name = "Host"
    g = create_game(game_code, host_name)
    if not g:
        return render_template("index.html", create_error="Game code taken or invalid (use 4–6 letters/numbers)")
    return redirect(url_for("host", game_id=g["id"]))


@app.route("/game/join", methods=["POST"])
def game_join():
    game_code = (request.form.get("game_code") or "").strip()
    player_name = (request.form.get("player_name") or "").strip()
    g = get_game(game_code)
    if not g:
        return render_template("index.html", join_error="Game not found. Check the code.")
    if not player_name:
        return render_template("index.html", join_error="Enter your name.")
    p = add_player(game_code, player_name)
    if not p:
        return render_template("index.html", join_error="Game full or already started.")
    return redirect(url_for("play", game_id=g["id"], player_id=p["id"]))


@app.route("/game/<game_id>/host")
def host(game_id):
    g = get_game(game_id)
    if not g:
        return "Game not found", 404
    host_player_id = g["players"][0]["id"] if g["players"] else None
    return render_template("host.html", game_id=g["id"], host_player_id=host_player_id)


@app.route("/game/<game_id>/join", methods=["GET", "POST"])
def join(game_id):
    g = get_game(game_id)
    if not g:
        return "Game not found", 404
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if name and len(g["players"]) < MAX_PLAYERS:
            p = add_player(game_id, name)
            if p:
                return redirect(url_for("play", game_id=game_id, player_id=p["id"]))
    return render_template("join.html", game_id=game_id, players=len(g["players"]))


@app.route("/game/<game_id>/play/<player_id>")
def play(game_id, player_id):
    g = get_game(game_id)
    if not g:
        return "Game not found", 404
    if not any(p["id"] == player_id for p in g["players"]):
        return "Player not found", 404
    return render_template("play.html", game_id=game_id, player_id=player_id)


@app.route("/api/game/<game_id>/state")
def api_state(game_id):
    g = get_game(game_id)
    if not g:
        return jsonify({"error": "not_found"}), 404
    pid = request.args.get("player_id")
    return jsonify(public_state(g, pid))


@app.route("/api/game/<game_id>/action", methods=["POST"])
def api_action(game_id):
    g = get_game(game_id)
    if not g:
        return jsonify({"error": "not_found"}), 404
    if g["phase"] != "play":
        return jsonify({"error": "wrong_phase"}), 400

    data = request.get_json() or {}
    pid = data.get("player_id")
    if not pid or not any(p["id"] == pid for p in g["players"]):
        return jsonify({"error": "invalid_player"}), 400
    if pid in g["actions"]:
        return jsonify({"error": "already_submitted"}), 400

    sit_out = data.get("sit_out", False)
    bid = data.get("bid")
    sell_item = data.get("sell_item")

    if sit_out:
        g["actions"][pid] = {"sit_out": True, "sell_item": sell_item}
    else:
        try:
            amount = int(bid) if bid is not None else 0
            budget = g["budgets"][pid]
            if amount < 0 or amount > budget:
                return jsonify({"error": "invalid_bid"}), 400
            g["actions"][pid] = {"sit_out": False, "bid": amount}
        except (TypeError, ValueError):
            return jsonify({"error": "invalid_bid"}), 400

    # Auto-resolve when all have submitted (no host "Resolve" click needed)
    if all_actions_received(g):
        resolve_round(g)

    return jsonify({"ok": True})


@app.route("/api/game/<game_id>/advance", methods=["POST"])
def api_advance(game_id):
    g = get_game(game_id)
    if not g:
        return jsonify({"error": "not_found"}), 404

    if g["phase"] == "lobby":
        if start_game(game_id):
            return jsonify({"ok": True})
        return jsonify({"error": "not_enough_players"}), 400

    if g["phase"] == "reveal":
        advance_from_reveal(game_id)
        return jsonify({"ok": True})

    return jsonify({"error": "nothing_to_advance"}), 400


@app.route("/api/game/<game_id>/resolve", methods=["POST"])
def api_resolve(game_id):
    """Resolve round when all have submitted (host can force too)."""
    g = get_game(game_id)
    if not g:
        return jsonify({"error": "not_found"}), 404
    if g["phase"] != "play":
        return jsonify({"error": "wrong_phase"}), 400
    if not all_actions_received(g):
        return jsonify({"error": "not_all_submitted"}), 400

    resolve_round(g)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
