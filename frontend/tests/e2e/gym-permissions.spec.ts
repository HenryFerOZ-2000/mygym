import { test, expect, type Page } from "@playwright/test";
import { selectNewestPlan } from "./gym-helpers";

async function prepare(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Usuario").fill("demo.owner");
  await page.getByLabel("Contraseña").fill(process.env.MYGYM_E2E_PASSWORD!);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(
    page.getByRole("heading", { name: "Elige tu espacio" }),
  ).toBeVisible();
  const workspaces = await (
    await page.request.get("/api/v1/me/workspaces/")
  ).json();
  const space = workspaces.find(
    (w: { name: string }) => w.name === "Gym Titan",
  );
  const csrf = await (await page.request.get("/api/v1/auth/csrf/")).json();
  const options = { headers: { "X-CSRFToken": csrf.csrfToken } };
  const base = `/api/v1/workspaces/${space.id}/`;
  const client = await (
    await page.request.post(base + "clients/", {
      ...options,
      data: { full_name: "Permisos ficticios " + Date.now() },
    })
  ).json();
  const plan = await (
    await page.request.post(base + "gym/plans/", {
      ...options,
      data: {
        name: "Permisos " + Date.now(),
        amount: "25.00",
        currency: "USD",
        unit: "DAYS",
        quantity: 30,
      },
    })
  ).json();
  return {
    space,
    client,
    plan,
    route: `/workspaces/${space.id}/clients/${client.id}/account`,
  };
}

test("revocación durante confirmación oculta la inscripción", async ({
  page,
}) => {
  const { route, plan } = await prepare(page);
  await page.goto(route);
  await selectNewestPlan(page, plan.id);
  await page.getByRole("button", { name: "Revisar inscripción" }).click();
  await expect(
    page.getByRole("button", { name: "Confirmar inscripción" }),
  ).toBeVisible();
  await page.route("**/gym/memberships/", (route) =>
    route.fulfill({
      status: 403,
      contentType: "application/json",
      body: JSON.stringify({
        error: {
          code: "permission_denied",
          message: "Acceso revocado.",
          fields: {},
        },
      }),
    }),
  );
  await page.getByRole("button", { name: "Confirmar inscripción" }).click();
  await expect(
    page.getByRole("button", { name: "Confirmar inscripción" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Revisar inscripción" }),
  ).toHaveCount(0);
});

for (const capability of ["gym.manage", "receivables.manage"]) {
  test(`cuenta mantiene accesible ${capability} por separado`, async ({
    page,
  }) => {
    const { route } = await prepare(page);
    await page.route("**/api/v1/me/workspaces/", async (route) => {
      const response = await route.fetch();
      const body = await response.json();
      await route.fulfill({
        response,
        json: body.map((w: { capabilities: string[] }) => ({
          ...w,
          capabilities: w.capabilities.filter(
            (c) => c === "clients.manage" || c === capability,
          ),
        })),
      });
    });
    await page.route(
      capability === "gym.manage"
        ? "**/api/v1/**/receivables/**"
        : "**/api/v1/**/gym/**",
      (route) =>
        route.fulfill({
          status: 403,
          contentType: "application/json",
          body: JSON.stringify({
            error: {
              code: "permission_denied",
              message: "Módulo deshabilitado.",
              fields: {},
            },
          }),
        }),
    );
    await page.goto(route);
    await expect(
      page.getByRole("heading", {
        name: capability === "gym.manage" ? "Membresías" : "Cargos y saldos",
        exact: true,
      }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", {
        name: capability === "gym.manage" ? "Cargos y saldos" : "Membresías",
        exact: true,
      }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: "Revisar inscripción" }),
    ).toHaveCount(0);
  });
}
