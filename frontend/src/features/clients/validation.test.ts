import { describe, expect, it } from "vitest";
import { validateClient } from "./validation";

describe("client form", () => {
  it("accepts missing contacts and rejects whitespace names", () => {
    expect(validateClient({ full_name: "Ana", phone: "", email: "" })).toEqual(
      {},
    );
    expect(
      validateClient({ full_name: "  ", phone: "", email: "" }),
    ).toHaveProperty("full_name");
  });
  it("rejects overlong values and invalid email", () => {
    expect(
      validateClient({
        full_name: "A".repeat(201),
        phone: "1".repeat(33),
        email: "bad",
      }),
    ).toEqual({
      full_name: expect.any(String),
      phone: expect.any(String),
      email: expect.any(String),
    });
  });
});
