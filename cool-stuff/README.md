# COOL STUFF!

The blind auction party game. Bid on mystery items — you never know what they're worth or how deep your opponents' pockets are. Collect the most valuable stuff to win!

## Quick Start

```bash
cd cool-stuff
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000 (or http://YOUR_IP:5000 for others on your WiFi).

1. Host: Create Game → share the join URL with players
2. Players: Join, enter name
3. Host: Start Game when 2–8 players are ready
4. Each round: bid or sit out (optionally sell an item for 75% cash)
5. Highest bid wins. Item value revealed. Winning bid stays secret. Repeat for 10 rounds.

## Deploy to Render (play from anywhere)

1. Push this repo to GitHub.
2. Go to [render.com](https://render.com) → Sign up (free).
3. **New** → **Web Service**.
4. Connect your GitHub repo. If cool-stuff is a subfolder (e.g. in VibeCoding), set **Root Directory** to `cool-stuff`.
5. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app -c gunicorn_config.py`
6. Click **Create Web Service**. First deploy takes ~2 min.
7. Your app will be at `https://your-app-name.onrender.com`.

Play on laptop + phone by opening the same URL. Free tier spins down after ~15 min idle (cold start ~30–60 sec).

## Rules

- **Starting budget:** $1,000
- **Sell payout:** 75% of item's full value
- **Win condition:** Most total value in stuff collected
- **Privacy:** Bankrolls and winning bids are never shown
