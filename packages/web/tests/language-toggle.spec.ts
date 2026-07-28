import { expect, test } from "@playwright/test"

test("can switch language from Swedish to English", async ({ page }) => {
  await page.goto("http://localhost:5173/")

  await expect(page.getByText("Hej världen")).toBeVisible()
  await expect(page.getByText("TypeScript-mall")).toBeVisible()

  await page.locator("details.dropdown.dropdown-end summary.btn").click()

  await page.getByRole("button", { name: "English" }).click()

  await expect(page).toHaveURL(/\/en\/?$/)

  await expect(page.getByText("Hello world")).toBeVisible()
  await expect(page.getByText("TypeScript Template")).toBeVisible()
})
