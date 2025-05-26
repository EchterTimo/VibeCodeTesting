from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import eventlet
import random
import math
import uuid

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

players = {}
bullets = []

WIDTH, HEIGHT = 1200, 800
SHIP_SIZE = 20
BULLET_SPEED = 7


def respawn():
    return {
        "x": random.uniform(0, WIDTH),
        "y": random.uniform(0, HEIGHT),
        "angle": random.uniform(0, math.pi * 2),
        "vx": 0,
        "vy": 0,
        "alive": True,
        "color": "#%06x" % random.randint(0, 0xFFFFFF),
        "shootCooldown": 0,
        "id": str(uuid.uuid4())
    }


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('join')
def on_join(data):
    sid = request.sid
    players[sid] = respawn()
    print(f"Player {sid} joined")
    emit('init', {"id": sid, "width": WIDTH,
         "height": HEIGHT, "players": players}, room=sid)
    emit('player_update', players, broadcast=True)


@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    if sid in players:
        players.pop(sid)
        emit('player_update', players, broadcast=True)
        print(f"Player {sid} left")


@socketio.on('input')
def on_input(data):
    sid = request.sid
    if sid not in players:
        return
    p = players[sid]
    if not p["alive"]:
        return
    keys = data.get('keys', {})
    if keys.get('left'):
        p["angle"] -= 0.05
    if keys.get('right'):
        p["angle"] += 0.05
    if keys.get('up'):
        p["vx"] += math.cos(p["angle"]) * 0.1
        p["vy"] += math.sin(p["angle"]) * 0.1
    if keys.get('shoot') and p.get('shootCooldown', 0) <= 0:
        angle = p["angle"]
        bullet = {
            "x": p["x"] + math.cos(angle) * SHIP_SIZE,
            "y": p["y"] + math.sin(angle) * SHIP_SIZE,
            "dx": math.cos(angle) * BULLET_SPEED + p["vx"],
            "dy": math.sin(angle) * BULLET_SPEED + p["vy"],
            "owner": sid,
            "id": str(uuid.uuid4())
        }
        bullets.append(bullet)
        p["shootCooldown"] = 15
    if p.get("shootCooldown", 0) > 0:
        p["shootCooldown"] -= 1


def update():
    global bullets
    # update players
    for p in players.values():
        if not p["alive"]:
            continue
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vx"] *= 0.98
        p["vy"] *= 0.98
        # screen wrap
        if p["x"] < 0:
            p["x"] = WIDTH
        if p["x"] > WIDTH:
            p["x"] = 0
        if p["y"] < 0:
            p["y"] = HEIGHT
        if p["y"] > HEIGHT:
            p["y"] = 0

    # update bullets
    remove = set()
    for b in bullets:
        b["x"] += b["dx"]
        b["y"] += b["dy"]
        # Remove offscreen bullets
        if not (0 <= b["x"] <= WIDTH and 0 <= b["y"] <= HEIGHT):
            remove.add(b["id"])

    # bullet collision
    for b in bullets:
        if b["id"] in remove:
            continue
        for sid, p in players.items():
            if not p["alive"] or sid == b["owner"]:
                continue
            dx = b["x"] - p["x"]
            dy = b["y"] - p["y"]
            if math.hypot(dx, dy) < SHIP_SIZE:
                p["alive"] = False
                remove.add(b["id"])
                # respawn after 1s
                socketio.start_background_task(respawn_player, sid)
    # Remove flagged bullets
    bullets = [b for b in bullets if b["id"] not in remove]


def respawn_player(sid):
    eventlet.sleep(1)
    if sid in players:
        players[sid].update(respawn())
        players[sid]["alive"] = True


def send_state():
    state = {
        "players": players,
        "bullets": bullets
    }
    socketio.emit('state', state)


def game_loop():
    while True:
        update()
        send_state()
        socketio.sleep(1/60)


@socketio.on('connect')
def on_connect():
    print(f"Client {request.sid} connected")


if __name__ == '__main__':
    socketio.start_background_task(game_loop)
    socketio.run(app, host='0.0.0.0', port=5000)
