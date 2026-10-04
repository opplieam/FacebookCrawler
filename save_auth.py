"""One-time manual login that saves a Playwright storage state.

Run: python save_auth.py
A visible Chromium opens at the Facebook login page. Log in with
your test account, complete either the two-factor approval or the
bot challenge if one appears, wait until you see your feed, then
press Enter here. The session cookies are saved to auth.json for
the spider to reuse.
"""

import asyncio

from playwright.async_api import async_playwright

URL = "https://www.facebook.com/"
OUTPUT = "auth.json"


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await ctx.new_page()
        await page.goto(URL)
        input("Log in and clear 2FA or the bot challenge, then press Enter here... ")
        await ctx.storage_state(path=OUTPUT)
        await browser.close()
    print(f"Saved to {OUTPUT}")


if __name__ == "__main__":
    asyncio.run(main())
