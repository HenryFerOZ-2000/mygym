import { expect, type Page } from "@playwright/test";

export async function selectNewestPlan(
  page: Page,
  option: string | { label: string },
) {
  const workspaceId = new URL(page.url()).pathname.split("/")[2];
  const plans = await (
    await page.request.get(`/api/v1/workspaces/${workspaceId}/gym/plans/`)
  ).json();
  const enrollment = page
    .getByRole("heading", { name: "Inscribir o renovar", exact: true })
    .locator("..");
  for (let number = 1; number < Math.ceil(plans.count / 25); number++) {
    await enrollment
      .getByRole("button", { name: "Siguiente", exact: true })
      .click();
    await expect(
      enrollment.getByText(`Página ${number + 1}`, { exact: true }),
    ).toBeVisible();
  }
  await enrollment.getByLabel("Plan para inscribir").selectOption(option);
}
