const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  try {
    await page.goto("https://interview-apper-wfeq2abzgdqyqf28hx9ktq.streamlit.app/", {
      waitUntil: "domcontentloaded",
      timeout: 120000,
    });

    // sleep 화면에서 wake 버튼이 있으면 클릭
    const wakeButton = page.getByText("Yes, get this app back up!", { exact: false });

    if (await wakeButton.isVisible().catch(() => false)) {
      console.log("Wake button found. Clicking...");
      await wakeButton.click();
      await page.waitForLoadState("networkidle", { timeout: 120000 }).catch(() => {});
    } else {
      console.log("Wake button not found. App may already be awake.");
    }

    // 앱 본문이 뜰 때까지 잠깐 대기
    await page.waitForTimeout(10000);
    console.log("Done.");
  } catch (e) {
    console.error("Failed:", e);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
