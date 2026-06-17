from playwright.async_api import async_playwright

async def fill_form(
    url: str,
    field_selector: str,
    value: str,
    submit_selector: str
):

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=False
        )

        page = await browser.new_page()

        await page.goto(url)

        await page.fill(
            field_selector,
            value
        )

        await page.click(
            submit_selector
        )

        await page.wait_for_timeout(5000)

        await browser.close()

    return "Form submitted successfully"