import { test, expect } from "@playwright/test";

test.afterEach(async ({ page }) => {
  await page.unrouteAll({ behavior: "wait" });
});

test("una consulta de asistencia fallida se puede reintentar sin recargar", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Usuario").fill("demo.owner");
  await page.getByLabel("Contraseña").fill(process.env.MYGYM_E2E_PASSWORD!);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.getByRole("link", { name: /Gym Titan/ }).click();
  let unavailable = true;
  await page.route("**/attendance/clients/?**", (route) => {
    if (unavailable) return route.abort("failed");
    return route.continue();
  });
  await page.getByRole("link", { name: "Asistencia", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Buscar personas" }).getByRole("alert"),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Reintentar búsqueda" }),
  ).toBeVisible();
  unavailable = false;
  await page.getByRole("button", { name: "Reintentar búsqueda" }).click();
  await expect(
    page.getByRole("button", { name: "Revisar entrada de Ana Ejemplo" }),
  ).toBeVisible();
});

for (const mode of ["attendance", "financial"]) {
  test(`entrada al negocio con acceso sólo a ${mode}`, async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Usuario").fill("demo.owner");
    await page.getByLabel("Contraseña").fill(process.env.MYGYM_E2E_PASSWORD!);
    await page.getByRole("button", { name: "Entrar" }).click();
    await expect(
      page.getByRole("heading", { name: "Elige tu espacio" }),
    ).toBeVisible();
    const body = await (
      await page.request.get("/api/v1/me/workspaces/")
    ).json();
    await page.route("**/api/v1/me/workspaces/", (route) =>
      route.fulfill({
        json: body.map((w: { capabilities: string[] }) => ({
          ...w,
          capabilities:
            mode === "attendance"
              ? ["gym.attendance"]
              : ["receivables.manage", "receivables.reports"],
        })),
      }),
    );
    await page.reload();
    await page.getByRole("link", { name: /Gym Titan/ }).click();
    await expect(
      page.getByRole("heading", {
        name: mode === "attendance" ? "Asistencia" : "Vencimientos y reportes",
        exact: true,
      }),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Planes y promociones", exact: true }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("link", { name: "Clientes", exact: true }),
    ).toHaveCount(0);
    if (mode === "financial") {
      await expect(
        page.getByRole("heading", { name: "Movimientos manuales" }),
      ).toBeVisible();
      await expect(
        page.getByRole("heading", { name: "Asistencia del período" }),
      ).toHaveCount(0);
    }
  });
}

test("revisión de asistencia muestra fechas sin exigir acceso a membresías", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Usuario").fill("demo.owner");
  await page.getByLabel("Contraseña").fill(process.env.MYGYM_E2E_PASSWORD!);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.getByRole("link", { name: /Gym Titan/ }).click();
  await page.getByRole("link", { name: "Asistencia", exact: true }).click();
  await page.getByLabel("Buscar cliente").fill("Ana Ejemplo");
  const spaces = await (
    await page.request.get("/api/v1/me/workspaces/")
  ).json();
  await page.route("**/api/v1/me/workspaces/", (route) =>
    route.fulfill({
      json: spaces.map((w: { capabilities: string[] }) => ({
        ...w,
        capabilities: ["gym.attendance"],
      })),
    }),
  );
  await page.reload();
  await expect(
    page.getByRole("link", { name: "Planes y promociones" }),
  ).toHaveCount(0);
  await page.getByLabel("Buscar cliente").fill("Ana Ejemplo");
  await page.route("**/attendance/preview/", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    await route.fulfill({
      response,
      json: {
        ...data,
        status: "ACTIVE",
        last_day: "2026-10-31",
        previous_last_day: null,
        next_start: "2026-11-01",
      },
    });
  });
  await page
    .getByRole("button", { name: "Revisar entrada de Ana Ejemplo" })
    .click();
  await expect(
    page.getByText("Último día del período vigente: 31/10/2026", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByText("Próximo período: 01/11/2026", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "../.local/attendance-dates-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../.local/attendance-dates-mobile.png",
    fullPage: true,
  });
});
