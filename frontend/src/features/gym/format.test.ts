import { describe, expect, it } from "vitest";
import { planAvailability } from "./format";

describe("disponibilidad de venta", () => {
  it("incluye ambos límites y diferencia ofertas programadas y finalizadas", () => {
    const plan = {
      is_active: true,
      available_from: "2026-10-01",
      available_until: "2026-10-10",
    };
    expect(planAvailability(plan, "2026-09-30")).toBe("Programado");
    expect(planAvailability(plan, "2026-10-01")).toBe("Disponible");
    expect(planAvailability(plan, "2026-10-10")).toBe("Disponible");
    expect(planAvailability(plan, "2026-10-11")).toBe("Venta finalizada");
  });
  it("un plan desactivado no se ofrece aunque sus fechas sean válidas", () => {
    expect(
      planAvailability(
        { is_active: false, available_from: null, available_until: null },
        "2026-09-30",
      ),
    ).toBe("Inactivo");
  });
});
