# FacebookCrawler

This is the 2026/2027 version.

> DISCLAIMER: this script is not authorized by Facebook. For commercial
> use please contact Facebook. The purpose of this script is for
> **educational**, to demonstrate how Scrapy can be written to extract
> pages with less help of headless browser. Use it at your own risk.
>
> WARNING: your Facebook account might get suspended if your spider runs
> too fast. Please be careful. Try to increase download_delay in
> `settings.py`.

## 2024 version

Login was done through Splash. Facebook encrypts the password client
side before sending it to the server. Instead of sending a plaintext
password, `strongpass` gets encrypted like this:

`#PWD_BROWSER:5:........`

Reverse engineering that encryption would be tedious to get right, so
Splash performed the login request, grabbed the cookies, and the rest
was normal Scrapy parsing. The mobile version was parsed because its
layout was easier to scrape.

That world is gone. Splash is dead, the mobile layout is outdated, and
bot detection is much stronger.

## 2026 version

Splash was picked originally because it is scalable: a separate
service, not a big fat browser living inside the Python process. This
version does the same thing with Playwright. The browser runs as a
separate service in Docker, Scrapy only talks to it, so this script
stays lightweight and scalable.

The process is more complicated than before. Login is manual, one time,
to avoid bot detection, and the session is saved. The bot reuses that
session for a long run.

Scraping uses the desktop version instead of mobile. There is room to
optimize: a mobile version means fewer requests and a smaller request
body to scrape, but not currently. That will probably come later.

## Requirements

- Python 3.14 (developed on 3.14.8 via pyenv) with an isolated venv.
- `pip install -r requirement.text` (or `make install`).
- Pinned trio: `Scrapy==2.19.0`, `scrapy-playwright==0.0.48`,
  `playwright==1.63.0`.
- Docker for the browser server:
  `mcr.microsoft.com/playwright:v1.63.0-noble`. Client and server
  versions must match or the connection fails.

## Browser service

The browser runs outside Python, like Splash did:

- `make pw-server-up` starts Chromium headless in Docker, listening on
  port 3000.
- Scrapy connects over `PLAYWRIGHT_CONNECT_URL=ws://localhost:3000/`.
- `make pw-server-logs` tails it, `make pw-server-down` stops it.

Each crawl page is a remote Playwright page. The Python process stays
light and the browser side scales independently.

## Manual login

Automated login always trips the bot check, so login is manual, once:

- `make auth` opens a visible Chromium at the Facebook login page.
- Log in with the test account, clear 2FA or the bot challenge if one
  appears, wait for the feed, then press Enter.
- The session is saved to `auth.json` and every crawl request reuses it
  as a Playwright storage state.

If the session expires the spider stops with `Session expired, rerun
python save_auth.py`. Just run `make auth` again.

## Running the crawl

```
make pw-server-up
make auth                      # once, or when the session expires
FB_PAGE_ID=ejeab FB_OUTPUT=fb.json make crawl
```

Or set them once as environment variables (for example in `.envrc`,
which is gitignored) and run plain `make crawl`.

`FB_PAGE_ID` accepts one page or several split by comma.
`FB_OUTPUT` defaults to `fb.json`. The flow is timeline to story to
item: the timeline render yields one story url, the story render yields
the post item with counts and comments.

## Data schema

Each item in the output JSON:

- page_id, page_name, page_url: the crawled page.
- post_id: story fbid from the UFI JSON.
- post_url: `story.php?story_fbid=...&id=...` permalink.
- post_text: full message text.
- image_urls: image urls attached to the post.
- reaction_count, comment_count, share_count.
- comments: list of comment_id, comment_text, comment_reaction_count,
  author_name, author_url.

## Configuration

- `USER_AGENT` in `settings.py`: desktop Chrome 126. It is forwarded
  into browser navigations, so changing surfaces means changing it too.
- `DOWNLOAD_DELAY = 3`: seconds between requests. Raise it if the
  account gets challenged.
- `PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30 * 1000`: slow renders
  need the headroom.
- `TWISTED_REACTOR`: asyncio selector reactor, required by
  scrapy-playwright on modern Scrapy.

## Troubleshooting

- Bot challenge or checkpoint after login. Slow down (`DOWNLOAD_DELAY`),
  solve it in the `make auth` window, and reuse the saved session.
- Interstitial or stub pages. The UA does not match the surface. Check
  `USER_AGENT` in `settings.py` against the Playwright context UA, the
  handler forwards Scrapy headers into navigations.
- Connection refused on `ws://localhost:3000/`. The server is down
  (`make pw-server-up`) or the `playwright` client and the Docker image
  versions drifted. They must match.
- Session expired mid-run. The spider stops and asks to rerun
  `make auth`. Refresh `auth.json` and crawl again.
- Empty output. The timeline render changed. Save a fresh snapshot and
  check the article selectors against it.
- Wrong text language. Post and comment language follows the test
  account's language setting, not the code. English account gets machine
  translations, Thai account gets the original text.

## TODO

- Mobile version for optimization. Fewer requests and a smaller
  response body to scrape than desktop. Not currently planned in
  detail, probably later.
- Infinite scroll to get more posts and comments. One timeline load
  yields the newest post only. Older posts and full comment pages need
  scroll-driven loading.
