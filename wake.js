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
    console.log("Waiting for Streamlit UI...");

    await page.waitForTimeout(15000); // Streamlit 렌더링 대기
    
    console.log("Looking for analysis button...");
    
    const analysisButton = page.locator("button:has-text('AI 심층 분석 시작')");
    
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
