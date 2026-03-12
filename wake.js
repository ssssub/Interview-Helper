const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  try {
    console.log("Opening Streamlit app...");

    await page.goto(
      "https://interview-apper-wfeq2abzgdqyqf28hx9ktq.streamlit.app/",
      {
        waitUntil: "domcontentloaded",
        timeout: 120000,
      }
    );

    console.log("Page loaded.");

    const wakeButton = page.getByText("Yes, get this app back up!", {
      exact: false,
    });

    if (await wakeButton.isVisible().catch(() => false)) {
      console.log("Wake button found → clicking");
      await wakeButton.click();
      await page.waitForLoadState("networkidle", { timeout: 120000 });
    } else {
      console.log("Wake button not found → app probably awake");
    }

    // 앱이 실제로 렌더링될 때까지 대기
    await page.waitForTimeout(10000);

    // 상태 확인용 스크린샷
    await page.screenshot({
      path: "screenshot.png",
      fullPage: true,
    });

    console.log("Screenshot saved.");
  } catch (err) {
    console.error("Error:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
