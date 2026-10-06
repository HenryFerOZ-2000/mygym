import { test, expect } from "@playwright/test";

test("Local sirve el build, conserva API y recarga rutas sin Vite", async ({ page, request }) => {
  const html = await (await request.get("/login")).text();
  expect(html).toContain("/assets/");
  expect(html).not.toContain("/@vite/client");
  await page.goto("/login");
  await page.reload();
  await expect(page.getByLabel("Usuario")).toBeVisible();
  await expect(page.getByRole("button", { name: "Entrar" })).toBeVisible();
  await page.screenshot({ path: "../.local/local-login.png", fullPage: true });
  expect((await request.get("/api/v1/health/")).status()).toBe(200);
  for (const route of ["/api/missing", "/api", "/.env", "/assets/missing.js"]) {
    const response = await request.get(route);
    expect(response.status()).toBe(404);
    expect(response.headers()["content-type"]).toContain("application/json");
  }
});
