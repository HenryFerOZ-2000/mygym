import { test, expect } from "@playwright/test";

test("respuesta perdida y cambio de pestaña conservan la misma entrada al reintentar", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Usuario").fill("demo.owner");
  await page.getByLabel("Contraseña").fill(process.env.MYGYM_E2E_PASSWORD!);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(
    page.getByRole("heading", { name: "Elige tu espacio" }),
  ).toBeVisible();
  const spaces = await (
    await page.request.get("/api/v1/me/workspaces/")
  ).json();
  const space = spaces.find((w: { name: string }) => w.name === "Gym Titan");
  const csrf = await (await page.request.get("/api/v1/auth/csrf/")).json();
  const name = `Reintento ${Date.now()}`;
  const client = await (
    await page.request.post(`/api/v1/workspaces/${space.id}/clients/`, {
      headers: { "X-CSRFToken": csrf.csrfToken },
      data: { full_name: name },
    })
  ).json();
  await page.goto(`/workspaces/${space.id}/attendance`);
  await page.getByLabel("Buscar cliente").fill(name);
  await page
    .getByRole("button", { name: `Revisar entrada de ${name}` })
    .click();
  await page
    .getByLabel("Motivo de excepción")
    .fill("Cortesía con respuesta perdida");
  const ids: string[] = [];
  await page.route(`**/clients/${client.id}/attendance/`, async (route) => {
    ids.push(route.request().postDataJSON().request_id);
    const response = await route.fetch();
    expect(response.status()).toBe(201);
    if (ids.length === 1) await route.abort("failed");
    else await route.fulfill({ response });
  });
  await page.getByRole("button", { name: "Confirmar entrada" }).click();
  await expect(page.getByRole("dialog").getByRole("alert")).toBeVisible();
  const refresh = page.waitForResponse((response) =>
    response.url().endsWith(`/clients/${client.id}/attendance/preview/`),
  );
  await page.evaluate(() => {
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      get: () => "hidden",
    });
    window.dispatchEvent(new Event("visibilitychange"));
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      get: () => "visible",
    });
    window.dispatchEvent(new Event("visibilitychange"));
  });
  await refresh;
  await expect(page.getByLabel("Motivo de excepción")).toHaveValue(
    "Cortesía con respuesta perdida",
  );
  await page.getByRole("button", { name: "Confirmar entrada" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  expect(ids).toHaveLength(2);
  expect(ids[1]).toBe(ids[0]);
  const history = await (
    await page.request.get(
      `/api/v1/workspaces/${space.id}/attendance/?q=${encodeURIComponent(name)}`,
    )
  ).json();
  expect(history.count).toBe(1);
});

test("asistencia por excepción, repetición confirmada, anulación y reportes", async ({
  page,
}) => {
  test.setTimeout(60000);
  await page.goto("/login");
  await page.getByLabel("Usuario").fill("demo.owner");
  await page.getByLabel("Contraseña").fill(process.env.MYGYM_E2E_PASSWORD!);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.getByRole("link", { name: /Gym Titan/ }).click();
  await page.getByRole("button", { name: "Nuevo cliente" }).click();
  const name = `Visita ${Date.now()}`;
  await page.getByLabel("Nombre completo").fill(name);
  await page.getByRole("button", { name: "Guardar cliente" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.getByRole("link", { name: "Asistencia", exact: true }).click();
  await page.getByLabel("Buscar cliente").fill(name);
  await page
    .getByRole("button", { name: `Revisar entrada de ${name}` })
    .click();
  await page.getByLabel("Motivo de excepción").fill("Cortesía de prueba");
  await page.getByRole("button", { name: "Confirmar entrada" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByText("Entrada registrada.", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: `Revisar entrada de ${name}` })
    .click();
  await expect(page.getByText("Entradas válidas hoy: 1")).toBeVisible();
  await page.getByLabel("Confirmo otra visita hoy").check();
  await page.getByLabel("Motivo de excepción").fill("Segunda visita de prueba");
  await page.getByRole("button", { name: "Confirmar entrada" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page
    .getByRole("button", { name: `Anular entrada de ${name}` })
    .first()
    .click();
  await page
    .getByLabel("Motivo de anulación")
    .fill("Registro de prueba equivocado");
  await page.getByRole("button", { name: "Confirmar anulación" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByText("Anulada", { exact: true })).toBeVisible();
  await page.screenshot({
    path: "../.local/attendance-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../.local/attendance-mobile.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "Vencimientos y reportes" }).click();
  await expect(
    page.getByRole("heading", { name: "Asistencia del período" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Movimientos manuales" }),
  ).toBeVisible();
  await page.getByLabel("Estado del servicio").selectOption("NO_MEMBERSHIP");
  await page.getByLabel("Filtrar cliente").fill(name);
  await expect(page.getByText(name, { exact: true })).toBeVisible();
  await page.screenshot({
    path: "../.local/reports-mobile.png",
    fullPage: true,
  });
});

test("revocación al confirmar asistencia cierra la autorización", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Usuario").fill("demo.owner");
  await page.getByLabel("Contraseña").fill(process.env.MYGYM_E2E_PASSWORD!);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.getByRole("link", { name: /Gym Titan/ }).click();
  await page.getByRole("link", { name: "Asistencia", exact: true }).click();
  await page.getByLabel("Buscar cliente").fill("Ana Ejemplo");
  await page
    .getByRole("button", { name: "Revisar entrada de Ana Ejemplo" })
    .click();
  await page.getByLabel("Motivo de excepción").fill("Cortesía");
  await page.route("**/clients/*/attendance/", (route) =>
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
  await page.getByRole("button", { name: "Confirmar entrada" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByText("Acceso revocado.", { exact: true }),
  ).toBeVisible();
});

test("vencimientos muestra el último día cubierto de una membresía vencida", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Usuario").fill("demo.owner");
  await page.getByLabel("Contraseña").fill(process.env.MYGYM_E2E_PASSWORD!);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.getByRole("link", { name: /Gym Titan/ }).click();
  await page.route("**/gym/expiries/?**", (route) =>
    route.fulfill({
      json: {
        count: 1,
        next: null,
        previous: null,
        reference_date: "2026-10-02",
        timezone: "America/Guayaquil",
        results: [
          {
            client_id: "00000000-0000-4000-8000-000000000001",
            full_name: "Vencimiento ficticio",
            status: "EXPIRED",
            coverage_end: null,
            previous_end: "2026-10-01",
            next_start: null,
            last_day: null,
            calendar_days_remaining: null,
          },
        ],
      },
    }),
  );
  await page.getByRole("link", { name: "Vencimientos y reportes" }).click();
  await page.getByLabel("Estado del servicio").selectOption("EXPIRED");
  await expect(
    page.getByText("Último día cubierto: 30/09/2026", { exact: true }),
  ).toBeVisible();
});
