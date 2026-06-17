from playwright.async_api import async_playwright


class BrowserAgent:

    async def search_google(self, query: str):

        async with async_playwright() as p:

            browser = await p.chromium.launch(headless=True)

            page = await browser.new_page()

            await page.goto(
                f"https://www.google.com/search?q={query}"
            )

            content = await page.content()

            await browser.close()

            return content

    async def open_website(self, url: str):

        async with async_playwright() as p:

            browser = await p.chromium.launch(headless=True)

            page = await browser.new_page()

            await page.goto(url)

            title = await page.title()

            content = await page.content()

            await browser.close()

            return {
                "title": title,
                "content": content[:5000],
            }