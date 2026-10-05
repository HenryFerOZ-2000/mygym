import { test, expect } from "@playwright/test";
import { selectNewestPlan } from "./gym-helpers";

test("planes editables, inscripción, abono y devolución conservan historial", async ({
  page,
}) => {
  test.setTimeout(60000);
  await page.goto("/login");
  await page.getByLabel("Usuario").fill("demo.owner");
  await page.getByLabel("Contraseña").fill(process.env.MYGYM_E2E_PASSWORD!);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.getByRole("link", { name: /Gym Titan/ }).click();
  await page.getByRole("link", { name: "Planes y promociones" }).click();
  await page.getByRole("button", { name: "Nuevo plan" }).click();
  const name = `Oferta ${Date.now()}`;
  await page.getByLabel("Nombre del plan").fill(name);
  await page.getByLabel("Precio").fill("30.00");
  await page.getByLabel("Duración", { exact: true }).fill("30");
  await page.getByLabel("Es una promoción").check();
  await page.getByRole("button", { name: "Guardar plan" }).click();
  await expect(page.getByText(name, { exact: true })).toBeVisible();
  await page.getByRole("button", { name: `Editar ${name}` }).click();
  await page.getByLabel("Precio").fill("30.00");
  await page.getByRole("button", { name: "Guardar plan" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page
      .getByRole("article")
      .filter({ has: page.getByText(name, { exact: true }) })
      .getByText(/VERSIÓN 2/),
  ).toBeVisible();
  await page.getByRole("link", { name: "Clientes", exact: true }).click();
  await page.getByRole("button", { name: "Nuevo cliente" }).click();
  const client = `Socio ${Date.now()}`;
  await page.getByLabel("Nombre completo").fill(client);
  await page.getByRole("button", { name: "Guardar cliente" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByText("Ficha guardada correctamente.", { exact: false }),
  ).toBeVisible();
  while (
    !(await page.getByRole("link", { name: `Membresías de ${client}` }).count())
  ) {
    await expect(
      page.getByRole("link", { name: `Membresías de ${client}` }),
    ).toBeVisible();
  }
  await page.getByRole("link", { name: `Membresías de ${client}` }).click();
  await selectNewestPlan(page, { label: name });
  await page.getByRole("button", { name: "Revisar inscripción" }).click();
  await expect(page.getByText("Total del cargo: USD 30.00")).toBeVisible();
  await page.getByRole("button", { name: "Confirmar inscripción" }).click();
  await expect(page.getByText("Saldo: USD 30.00")).toBeVisible();
  await page.getByRole("button", { name: "Registrar abono" }).click();
  await page.getByLabel("Importe a cobrar").fill("10.00");
  await page.getByRole("button", { name: "Confirmar cobro" }).click();
  await expect(page.getByText("Saldo: USD 20.00")).toBeVisible();
  await page.getByRole("button", { name: "Registrar devolución" }).click();
  await page.getByLabel("Importe a devolver").fill("5.00");
  await page.getByLabel("Motivo").fill("Devolución de prueba realizada");
  await page
    .getByLabel("Confirmo que devolví el dinero fuera de MyGym")
    .check();
  await page.getByRole("button", { name: "Confirmar devolución" }).click();
  await expect(page.getByText("Saldo: USD 25.00")).toBeVisible();
  await page.screenshot({
    path: "../.local/gym-account-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../.local/gym-account-mobile.png",
    fullPage: true,
  });
});
