"""Render the GitHub status card: src/status-dark.svg and src/status-light.svg.

    GH_TOKEN=$(gh auth token) python3 scripts/status.py
    (uv's Python on NixOS also needs SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt)

Counts public repos only. Set STATS_PRIVATE=1 (with a token that can read
them) to include private repos in the repo count and language mix.
Runs daily in .github/workflows/status.yml.
"""

import datetime as dt
import json
import os
import urllib.request
from xml.sax.saxutils import escape

from card import W
from term import CW, LH, PAD, TOP, USER, cursor, prompt, window, write

QUERY = """
query($login: String!, $privacy: RepositoryPrivacy) {
  user(login: $login) {
    createdAt
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date weekday contributionCount contributionLevel } }
      }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: $privacy, first: 100) {
      totalCount
      nodes { languages(first: 20) { edges { size node { name color } } } }
    }
  }
}"""

LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
TOP_LANGS = 7  # the rest is folded into "Other"
INNER = W - 2 * PAD


def fetch():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("set GH_TOKEN (e.g. GH_TOKEN=$(gh auth token))")
    private = os.environ.get("STATS_PRIVATE") == "1"
    body = json.dumps({"query": QUERY, "variables": {"login": USER, "privacy": None if private else "PUBLIC"}})
    req = urllib.request.Request("https://api.github.com/graphql", body.encode(),
                                 {"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    if "errors" in res:
        raise SystemExit(json.dumps(res["errors"], indent=2))
    return res["data"]["user"], private


def streaks(days):
    """(current, longest) runs of days with contributions. Today may still be empty."""
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        longest = max(longest, run)
    tail = days[:-1] if days and not days[-1]["contributionCount"] else days
    current = 0
    for d in reversed(tail):
        if not d["contributionCount"]:
            break
        current += 1
    return current, longest


def languages(repos):
    total = {}
    for repo in repos:
        for e in repo["languages"]["edges"]:
            name = e["node"]["name"]
            size, _ = total.get(name, (0, None))
            total[name] = (size + e["size"], e["node"]["color"])
    ranked = sorted(total.items(), key=lambda kv: -kv[1][0])
    all_bytes = sum(s for _, (s, _) in ranked) or 1
    langs = [(n, s / all_bytes, c) for n, (s, c) in ranked[:TOP_LANGS]]
    rest = sum(s for _, (s, _) in ranked[TOP_LANGS:])
    if rest:
        langs.append(("Other", rest / all_bytes, None))
    return langs


def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


def render(t, user, private, today):
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    current, longest = streaks(days)
    langs = languages(user["repositories"]["nodes"])
    repos = user["repositories"]["totalCount"]

    step = INNER / len(weeks)
    cell = step - 2.5
    month_y = TOP + 2 * LH + 12
    grid_y = month_y + 8
    stats_y = grid_y + 7 * step + 32
    since = dt.date.fromisoformat(user["createdAt"][:10])
    stats = [
        ("Contribs", f"{cal['totalContributions']} in the last year"),
        ("Streak", f"{plural(current, 'day')} (best {longest})"),
        ("Commits", f"{user['contributionsCollection']['totalCommitContributions']} in the last year"),
        ("Repos", f"{repos} {'own' if private else 'public'}"),
        ("Joined", since.strftime("%b %Y")),
        ("Updated", today.isoformat()),
    ]
    bar_y = stats_y + (len(stats) // 2) * LH + 12
    legend_y = bar_y + LH + 14
    widest = max(len(f"{n} {p:.1%}") for n, p, _ in langs) + 4  # dot + gap
    cols = max(1, min(4, int(INNER // (widest * CW))))
    end_y = legend_y + ((len(langs) - 1) // cols) * LH + 40
    h = end_y + LH + 28

    desc = "; ".join(f"{k}: {v}" for k, v in stats) + "; languages: " + ", ".join(
        f"{n} {p:.1%}" for n, p, _ in langs)
    out = window(t, W, h, "status", desc,
                 defs=f'<clipPath id="lb"><rect x="{PAD}" y="{bar_y}" width="{INNER}" height="10" rx="5"/></clipPath>')
    o = out.append

    o(prompt(TOP, "status"))

    # contribution calendar
    last_month = None
    last_label_x = -99
    for wi, week in enumerate(weeks):
        x = PAD + wi * step
        month = week["contributionDays"][0]["date"][:7]
        if month != last_month and wi < len(weeks) - 2 and x - last_label_x > 3 * step:
            if last_month is not None or week["contributionDays"][0]["weekday"] == 0:
                label = dt.date.fromisoformat(month + "-01").strftime("%b")
                o(f'<text class="m" x="{x:.1f}" y="{month_y}" style="font-size:11px">{label}</text>')
                last_label_x = x
        last_month = month
        for d in week["contributionDays"]:
            fill = t["heat"][LEVELS.index(d["contributionLevel"])]
            o(f'<rect x="{x:.1f}" y="{grid_y + d["weekday"] * step:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="2" fill="{fill}"/>')

    # numbers, two columns
    for i, (k, v) in enumerate(stats):
        x = PAD + (i % 2) * INNER / 2
        y = stats_y + (i // 2) * LH
        o(f'<text x="{x:.1f}" y="{y}" xml:space="preserve"><tspan class="a b">{k}</tspan>: {escape(v)}</text>')

    # language bar + legend
    o(f'<g clip-path="url(#lb)">')
    x = PAD
    for name, pct, color in langs:
        o(f'<rect x="{x:.1f}" y="{bar_y}" width="{INNER * pct + 0.5:.1f}" height="10" fill="{color or t["muted"]}"/>')
        x += INNER * pct
    o("</g>")
    for i, (name, pct, color) in enumerate(langs):
        x = PAD + (i % cols) * INNER / cols
        y = legend_y + (i // cols) * LH
        o(f'<circle cx="{x + 5:.1f}" cy="{y - 4.5}" r="5" fill="{color or t["muted"]}"/>'
          f'<text x="{x + 2 * CW:.1f}" y="{y}" xml:space="preserve">{escape(name)} <tspan class="m">{pct:.1%}</tspan></text>')

    o(cursor(t, end_y))
    o("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    user, private = fetch()
    today = dt.datetime.now(dt.timezone.utc).date()
    write("status", lambda t: render(t, user, private, today))
