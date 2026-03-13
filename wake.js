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

    // sleep 화면이면 wake 버튼 클릭
    const wakeButton = page.getByText("Yes, get this app back up!", { exact: false });

    if (await wakeButton.isVisible().catch(() => false)) {
      console.log("Wake button found → clicking");
      await wakeButton.click();
      await page.waitForLoadState("networkidle", { timeout: 120000 });
    }

    // 분석 시작 버튼 대기
    console.log("Waiting for analysis button...");

    const analysisButton = page.getByText("분석 시작", { exact: false });

    await analysisButton.waitFor({ timeout: 120000 });

    console.log("Clicking analysis button");

    await analysisButton.click();

    // Streamlit 실행 대기
    await page.waitForTimeout(15000);

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
