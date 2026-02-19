"""Be the Better Deal — Amazon price & deal tracker."""

import re
from flask import Flask, render_template, request, redirect, url_for

from database import (
    init_db,
    create_run,
    save_snapshot,
    get_recent_runs,
    get_snapshots_for_run,
)
from amazon import fetch_asin

app = Flask(__name__)


def parse_asins(text: str) -> list[str]:
    """Extract ASINs from comma/newline-separated input."""
    # ASINs are 10 chars, alphanumeric
    candidates = re.findall(r"[A-Z0-9]{10}", text.upper())
    return list(dict.fromkeys(candidates))  # dedupe, preserve order


@app.route("/")
def index():
    runs = get_recent_runs()
    return render_template("index.html", runs=runs)


@app.route("/run", methods=["POST"])
def run_check():
    your_asin = (request.form.get("your_asin") or "").strip().upper()
    competitors_raw = request.form.get("competitor_asins") or ""
    competitor_asins = parse_asins(competitors_raw)

    if not your_asin or len(your_asin) != 10:
        return redirect(url_for("index"))  # TODO: flash error

    run_id = create_run()

    # Fetch and save your product
    data = fetch_asin(your_asin)
    save_snapshot(run_id, your_asin, is_yours=True, **{k: v for k, v in data.items() if k != "fetched_at"})

    # Fetch and save competitors
    for asin in competitor_asins:
        data = fetch_asin(asin)
        save_snapshot(run_id, asin, is_yours=False, **{k: v for k, v in data.items() if k != "fetched_at"})

    return redirect(url_for("run_detail", run_id=run_id))


@app.route("/run/<int:run_id>")
def run_detail(run_id):
    snapshots = get_snapshots_for_run(run_id)
    run = next((r for r in get_recent_runs(100) if r["id"] == run_id), None)
    return render_template("run.html", run=run, snapshots=snapshots)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
