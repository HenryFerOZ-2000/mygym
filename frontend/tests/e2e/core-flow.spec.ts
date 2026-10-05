import { expect, test } from "@playwright/test";

test("login form is accessible", async ({ page }) => {
  await page.goto("/login");
  await expect(
    page.getByRole("heading", { name: "Tu gimnasio, en orden." }),
  ).toBeVisible();
  await expect(page.getByLabel("Usuario")).toBeVisible();
  await expect(page.getByLabel("Contraseña")).toBeVisible();
  await expect(page.getByRole("button", { name: "Entrar" })).toBeVisible();
});

test("real API, two workspaces, edit and logout across tabs", async ({
  page,
  context,
}) => {
  if (!process.env.MYGYM_E2E_PASSWORD)
    throw new Error("MYGYM_E2E_PASSWORD is required; no fixed test passwords.");
  await page.goto("/login");
  await page.getByLabel("Usuario").fill("demo.owner");
  await page.getByLabel("Contraseña").fill(process.env.MYGYM_E2E_PASSWORD);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(
    page.getByRole("heading", { name: "Elige tu espacio" }),
  ).toBeVisible();
  await page.getByRole("link", { name: /Gym Titan/ }).click();
  const aUrl = page.url();
  const second = await context.newPage();
  await second.goto("/workspaces");
  await second.getByRole("link", { name: /Gym Aurora/ }).click();
  const name = `Cliente ficticio ${Date.now()}`;
  await page.getByRole("button", { name: "Nuevo cliente" }).click();
  await page.getByLabel("Nombre completo").fill(name);
  await page.getByRole("button", { name: "Guardar cliente" }).click();
  await expect(page.getByText(name, { exact: true })).toBeVisible();
  await second.reload();
  await expect(second.getByText(name, { exact: true })).toHaveCount(0);
  await expect(page).toHaveURL(aUrl);
  await page.getByRole("button", { name: `Editar ${name}` }).click();
  await page.getByLabel("Teléfono").fill("0991234567");
  await page.getByRole("button", { name: "Guardar cambios" }).click();
  await expect(
    page
      .getByRole("row")
      .filter({ has: page.getByText(name, { exact: true }) })
      .getByText("0991234567"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page.getByLabel("Usuario")).toBeVisible();
  await expect(second.getByLabel("Usuario")).toBeVisible();
  await expect(second.getByText(name, { exact: true })).toHaveCount(0);
});

test("mobile layout does not overflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/login");
  await expect(page.getByRole("button", { name: "Entrar" })).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});

test("mobile clients remain readable and editable", async ({ page }) => {
  if (!process.env.MYGYM_E2E_PASSWORD) throw new Error("E2E password required");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/login");
  await page.getByLabel("Usuario").fill("demo.owner");
  await page.getByLabel("Contraseña").fill(process.env.MYGYM_E2E_PASSWORD);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.getByRole("link", { name: /Gym Titan/ }).click();
  const name = page.getByText("Ana Ejemplo", { exact: true });
  await expect(name).toBeVisible();
  expect((await name.boundingBox())!.height).toBeLessThan(50);
  const edit = page.getByRole("button", {
    name: "Editar Ana Ejemplo",
    exact: true,
  });
  const box = (await edit.boundingBox())!;
  expect(box.x + box.width).toBeLessThanOrEqual(390);
  await edit.click();
  await expect(page.getByLabel("Nombre completo")).toHaveValue("Ana Ejemplo");
});

test("logout clears a session that was invalidated elsewhere", async ({
  page,
}) => {
  if (!process.env.MYGYM_E2E_PASSWORD) throw new Error("E2E password required");
  await page.goto("/login");
  await page.getByLabel("Usuario").fill("demo.owner");
  await page.getByLabel("Contraseña").fill(process.env.MYGYM_E2E_PASSWORD);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.getByRole("link", { name: /Gym Titan/ }).click();
  await expect(
    page.getByRole("heading", { name: "Tu comunidad" }),
  ).toBeVisible();
  const csrf = await (await page.request.get("/api/v1/auth/csrf/")).json();
  const logout = await page.request.post("/api/v1/auth/logout/", {
    data: {},
    headers: { "X-CSRFToken": csrf.csrfToken },
  });
  expect(logout.status()).toBe(200);
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page.getByLabel("Usuario")).toBeVisible();
});

test("identity discovered without BroadcastChannel discards the previous form", async ({
  page,
}) => {
  if (!process.env.MYGYM_E2E_PASSWORD) throw new Error("E2E password required");
  await page.addInitScript(() => {
    Object.defineProperty(window, "BroadcastChannel", { value: undefined });
  });
  await page.goto("/login");
  await page.getByLabel("Usuario").fill("demo.owner");
  await page.getByLabel("Contraseña").fill(process.env.MYGYM_E2E_PASSWORD);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.getByRole("link", { name: /Gym Titan/ }).click();
  await page
    .getByRole("button", { name: "Editar Ana Ejemplo", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  const csrf = await (await page.request.get("/api/v1/auth/csrf/")).json();
  const login = await page.request.post("/api/v1/auth/login/", {
    data: { username: "demo.coach", password: process.env.MYGYM_E2E_PASSWORD },
    headers: { "X-CSRFToken": csrf.csrfToken },
  });
  expect(login.status()).toBe(200);
  await page.evaluate(() =>
    window.dispatchEvent(new Event("visibilitychange")),
  );
  await expect(page.getByText("demo.coach", { exact: true })).toBeVisible();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Acceso no disponible" }),
  ).toBeVisible();
});
