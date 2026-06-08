from playwright.async_api import async_playwright

async def google_search(query: str):

    results = []

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page()

        await page.goto(
            f"https://www.google.com/search?q={query}"
        )

        await page.wait_for_timeout(3000)

        links = await page.locator("h3").all_text_contents()

        for item in links[:5]:
            results.append(item)

        await browser.close()

    return results