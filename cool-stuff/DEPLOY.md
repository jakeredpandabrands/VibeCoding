# Deploy COOL STUFF to Render

## Fixes applied (for blank page / no response)

- **gunicorn_config.py** — Binds to `0.0.0.0:PORT` (reads from env; Render sets PORT=10000)
- **.python-version** — Pins Python 3.12 for Render
- **/health** — Simple health check endpoint
- **Start command** — Use `gunicorn app:app -c gunicorn_config.py` (avoid $PORT shell expansion issues)

## 1. Push to GitHub

From the VibeCoding repo root:

```bash
# Create a new repo on GitHub first: github.com/new → name it "VibeCoding" (or whatever)
# Then:
cd /Users/jake/GitRepos/VibeCoding
git remote add origin https://github.com/YOUR_USERNAME/VibeCoding.git
git branch -M main
git push -u origin main
```

(Replace `YOUR_USERNAME` with your GitHub username.)

## 2. Deploy on Render

1. Go to [render.com](https://render.com) → **Sign up** or **Log in** (free with GitHub)
2. **New** → **Web Service**
3. Connect your **GitHub** account if prompted
4. Select the **VibeCoding** repo
5. Configure:
   - **Name:** `cool-stuff` (or any name)
   - **Root Directory:** `cool-stuff`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app -c gunicorn_config.py`
   - The config uses 1 worker (required for in-memory game state)
6. **Create Web Service**

First deploy takes ~2 minutes. You'll get a URL like `https://cool-stuff-xxxx.onrender.com`.

## 3. Test

Open the URL on your laptop → Create Game → open the join URL on your phone → Join → Start Game. Play!
