import { afterEach, expect, it, vi } from "vitest";
import { api, invalidateSessionRequests } from "./client";

afterEach(() => vi.unstubAllGlobals());

it("rejects a private response that arrives after logout", async () => {
  let release!: (value: Response) => void;
  vi.stubGlobal(
    "fetch",
    () =>
      new Promise<Response>((resolve) => {
        release = resolve;
      }),
  );
  const pending = api("workspaces/fictitious/clients/");
  invalidateSessionRequests();
  release(
    new Response(JSON.stringify({ results: [{ full_name: "Private" }] }), {
      status: 200,
    }),
  );
  await expect(pending).rejects.toMatchObject({ name: "AbortError" });
});
