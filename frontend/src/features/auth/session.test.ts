import { QueryObserver } from "@tanstack/react-query";
import { expect, it } from "vitest";
import { queryClient } from "../../app/query-client";
import { clearPrivateData, reconcileIdentity } from "./session";

it("notifies mounted auth observers and removes private records on logout", async () => {
  queryClient.setQueryData(["me"], { id: 1, username: "fictional" });
  queryClient.setQueryData([1, "workspace-a", "clients"], {
    results: [{ full_name: "Private" }],
  });
  const observer = new QueryObserver(queryClient, {
    queryKey: ["me"],
    enabled: false,
  });
  let observed: unknown = observer.getCurrentResult().data;
  const unsubscribe = observer.subscribe((result) => {
    observed = result.data;
  });
  clearPrivateData(false);
  await new Promise((resolve) => setTimeout(resolve, 10));
  expect(observed).toBeNull();
  expect(
    queryClient.getQueryData([1, "workspace-a", "clients"]),
  ).toBeUndefined();
  unsubscribe();
});

it("keeps same-identity data but purges it on the first expired revalidation", () => {
  clearPrivateData(false);
  reconcileIdentity(7);
  queryClient.setQueryData(["me"], { id: 7, username: "fictional" });
  queryClient.setQueryData([7, "workspace", "clients"], {
    results: ["private"],
  });
  reconcileIdentity(7);
  expect(queryClient.getQueryData([7, "workspace", "clients"])).toEqual({
    results: ["private"],
  });
  reconcileIdentity(null);
  expect(queryClient.getQueryData([7, "workspace", "clients"])).toBeUndefined();
});
