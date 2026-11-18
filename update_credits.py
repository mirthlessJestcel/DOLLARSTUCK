import os, json, html, urllib.parse, urllib.request

UA = "credits-bot (https://github.com, 1.0)"
DISCORD_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
GUILD_ID = os.environ["DISCORD_GUILD_ID"]
ROLE_ID = os.environ["DISCORD_ROLE_ID"]
PATREON_TOKEN = os.environ.get("PATREON_TOKEN", "")
PATREON_CAMPAIGN = os.environ.get("PATREON_CAMPAIGN_ID", "")

TEXT_COLOR = "#12ba41"   # color of the names on the credits page


def get(url, headers):
    request = urllib.request.Request(url, headers=dict(headers, **{"User-Agent": UA}))
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def boosters():
    names, after = [], "0"
    while True:
        url = "https://discord.com/api/v10/guilds/%s/members?limit=1000&after=%s" % (GUILD_ID, after)
        page = get(url, {"Authorization": "Bot " + DISCORD_TOKEN})
        for member in page:
            if ROLE_ID in member["roles"]:
                names.append(member["user"]["username"])
        if len(page) < 1000:
            return sorted(names, key=str.lower)
        after = page[-1]["user"]["id"]


def patrons():
    if not PATREON_TOKEN:
        return []
    headers = {"Authorization": "Bearer " + PATREON_TOKEN}
    if not PATREON_CAMPAIGN:
        data = get("https://www.patreon.com/api/oauth2/v2/campaigns", headers)
        for campaign in data["data"]:
            print("YOUR PATREON CAMPAIGN ID IS:", campaign["id"])
        return []
    names, cursor = [], ""
    while True:
        url = ("https://www.patreon.com/api/oauth2/v2/campaigns/%s/members"
               "?fields%%5Bmember%%5D=full_name,patron_status&page%%5Bcount%%5D=500" % PATREON_CAMPAIGN)
        if cursor:
            url += "&page%5Bcursor%5D=" + urllib.parse.quote(cursor)
        data = get(url, headers)
        for member in data["data"]:
            info = member["attributes"]
            if info.get("patron_status") == "active_patron" and info.get("full_name"):
                names.append(info["full_name"])
        cursor = ((data.get("meta") or {}).get("pagination") or {}).get("cursors", {}).get("next")
        if not cursor:
            return sorted(names, key=str.lower)


patron_names = patrons()
booster_names = boosters()

plain = "Patrons: %s\n\nServer Boosters: %s\n" % (", ".join(patron_names), ", ".join(booster_names))
page = (
    '<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
    'html,body{margin:0;background:transparent;color:%s;font:14px "Courier New",monospace;line-height:1.5}'
    '</style></head><body>Patrons: %s<br><br>Server Boosters: %s</body></html>\n'
    % (TEXT_COLOR,
       ", ".join(html.escape(n) for n in patron_names),
       ", ".join(html.escape(n) for n in booster_names))
)
open("credits.txt", "w", encoding="utf-8").write(plain)
open("credits.html", "w", encoding="utf-8").write(page)
print(plain)
