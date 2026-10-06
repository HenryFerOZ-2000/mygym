import { test, expect, type Page } from "@playwright/test";

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Usuario").fill("demo.owner");
  await page.getByLabel("Contraseña").fill(process.env.MYGYM_E2E_PASSWORD!);
  await page.getByRole("button", { name: "Entrar" }).click();
}

for (const width of [360, 768, 1280]) {
test(`keyboard focus and navigation stay consistent at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 844 });
  await login(page);
  await page.getByRole("link", { name: /Gym Titan/ }).click();
  await expect(page.getByText("Ana Ejemplo", { exact: true })).toBeVisible();
  await page.screenshot({ path: `../.local/visual-navigation-${width}.png`, fullPage: false });
  await page.getByRole("link", { name: "Planes y promociones" }).click();
  await page.getByRole("button", { name: "Nuevo plan" }).click();
  await page.getByLabel("Duración", { exact: true }).focus();
  await page.keyboard.press("Tab");
  const unit = page.getByRole("combobox", { name: /Unidad/ });
  await expect(unit).toBeFocused();
  await page.screenshot({ path: `../.local/visual-plan-focus-${width}.png`, fullPage: false });
  await expect(unit).toHaveCSS("outline-color", "rgb(137, 167, 100)");
  await expect(unit).toHaveCSS("outline-width", "3px");
  await expect(page.getByRole("checkbox", { name: "Disponible para inscribir" })).toHaveCSS("accent-color", "rgb(56, 91, 54)");
  await expect(page.getByLabel("Nombre del plan")).toHaveCSS("margin-bottom", "0px");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
}

test("inactive pagination keeps its colour on hover and does not imply loading", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await page.getByRole("link", { name: /Gym Titan/ }).click();
  const previous = page.getByRole("button", { name: "Anterior", exact: true });
  await expect(previous).toBeDisabled();
  const background = await previous.evaluate((element) => getComputedStyle(element).backgroundColor);
  await previous.hover({ force: true });
  await page.screenshot({ path: "../.local/visual-clients-mobile.png", fullPage: false });
  await expect(previous).toHaveCSS("background-color", background);
  await expect(previous).toHaveCSS("cursor", "not-allowed");
  const closeTarget = page.getByRole("button", { name: "Editar Ana Ejemplo", exact: true });
  const box = await closeTarget.boundingBox();
  expect(box!.height).toBeGreaterThanOrEqual(44);
});

test("workspace retry uses the shared secondary control inside its error state", async ({ page }) => {
  await page.route("**/api/v1/me/workspaces/", (route) => route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ error: { code: "server_error", message: "Fallo ficticio de prueba.", fields: {} } }) }));
  await login(page);
  const retry = page.getByRole("button", { name: "Reintentar", exact: true });
  await expect(retry).toBeVisible();
  await page.screenshot({ path: "../.local/visual-workspace-error.png", fullPage: true });
  await expect(retry).toHaveCSS("border-radius", "7px");
  const box = await retry.boundingBox();
  expect(box!.height).toBeGreaterThanOrEqual(44);
});

test("operation pending and failure states keep shared controls and feedback", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: /Gym Titan/ }).click();
  await page.getByRole("link", { name: "Planes y promociones" }).click();
  await page.getByRole("button", { name: "Nuevo plan" }).click();
  await page.getByLabel("Nombre del plan").fill("Plan ficticio de revisión visual");
  await page.getByLabel("Precio").fill("30.00");
  let release!: () => void;
  const pending = new Promise<void>((resolve) => { release = resolve; });
  await page.route("**/api/v1/workspaces/*/gym/plans/", async (route) => {
    await pending;
    await route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ error: { code: "server_error", message: "Fallo ficticio de prueba.", fields: {} } }) });
  });
  await page.getByRole("button", { name: "Guardar plan", exact: true }).click();
  try {
    const saving = page.getByRole("button", { name: /^Guardando/ });
    await expect(saving).toBeDisabled();
    await expect(page.getByRole("button", { name: "Cerrar", exact: true })).toBeDisabled();
    await page.screenshot({ path: "../.local/visual-plan-busy.png", fullPage: false });
    await expect(saving).toHaveAttribute("aria-busy", "true");
    await expect(saving).toHaveCSS("cursor", "wait");
  } finally { release(); }
  const alert = page.getByRole("dialog").getByRole("alert");
  await expect(alert).toBeVisible();
  await expect(alert).toHaveCSS("background-color", "rgb(252, 240, 237)");
  await expect(page.getByRole("button", { name: "Guardar plan", exact: true })).toBeEnabled();
  await page.screenshot({ path: "../.local/visual-plan-error.png", fullPage: false });
});
