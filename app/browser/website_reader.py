from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def read_website(url: str):

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page()

        await page.goto(url)

        await page.wait_for_timeout(3000)

        content = await page.content()

        soup = BeautifulSoup(
            content,
            "html.parser"
        )

        text = soup.get_text()

        await browser.close()

    return text[:5000]