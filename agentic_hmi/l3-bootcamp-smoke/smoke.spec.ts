import { test, expect } from "@playwright/test";

test.describe("L3 SA bootcamp HTML smoke", () => {
  test("participant URL: intro only, begin disabled, no game shell", async ({
    page,
  }) => {
    await page.goto("/l3_sa_bootcamp.html");
    const begin = page.locator("#btn-begin");
    await expect(begin).toBeDisabled();
    await expect(begin).toContainText(/participant/i);
    await expect(page.locator("#gm-hint")).toContainText(/participant/i);
    await expect(page.locator("#game")).not.toBeVisible();
    await expect(page.locator("#setup")).not.toBeVisible();
  });

  test("facilitator (?gm=1): launch, unlock, optimal Q1 = 9 pts; re-apply same does not stack; replace with worse then best", async ({
    page,
  }) => {
    await page.goto("/l3_sa_bootcamp.html?gm=1");
    await expect(page.locator("#btn-begin")).toBeEnabled();
    await page.locator("#btn-begin").click();
    await expect(page.locator("#setup")).toBeVisible();
    await page.locator("#team-inputs input").first().fill("Smoke Team");
    await page.getByRole("button", { name: "Launch simulator" }).click();
    await expect(page.locator("#game")).toBeVisible();
    await expect(page.locator("#tc-0 .team-name")).toHaveText("Smoke Team");
    await expect(page.locator("#ts-0")).toHaveText("0");

    await page.getByRole("button", { name: "Unlock this round" }).click();
    await expect(page.locator("#lg-0 .letter-btn[data-code='A']")).toBeVisible({
      timeout: 10_000,
    });

    async function pickThree(a: string, b: string, c: string) {
      await page.locator(`#lg-0 .letter-btn[data-code='${a}']`).click();
      await page.locator(`#lg-0 .letter-btn[data-code='${b}']`).click();
      await page.locator(`#lg-0 .letter-btn[data-code='${c}']`).click();
    }

    // Round 1 optimalSet: A, K, E
    await pickThree("A", "K", "E");
    await page.getByRole("button", { name: "Apply points for this team" }).click();
    await expect(page.locator("#ts-0")).toHaveText("9");

    await pickThree("A", "K", "E");
    await page.getByRole("button", { name: "Apply points for this team" }).click();
    await expect(page.locator("#ts-0")).toHaveText("9");

    await pickThree("B", "C", "D");
    await page.getByRole("button", { name: "Apply points for this team" }).click();
    await expect(page.locator("#ts-0")).toHaveText("0");

    await pickThree("A", "K", "E");
    await page.getByRole("button", { name: "Apply points for this team" }).click();
    await expect(page.locator("#ts-0")).toHaveText("9");
  });
});
