import { queryClient } from "../../app/query-client";
import { invalidateSessionRequests } from "../../shared/api/client";

const channel =
  typeof BroadcastChannel !== "undefined"
    ? new BroadcastChannel("mygym-session")
    : null;

let validatedIdentity: number | null = null;

export function reconcileIdentity(identity: number | null) {
  if (validatedIdentity === identity) return;
  validatedIdentity = identity;
  invalidateSessionRequests();
  void queryClient.cancelQueries({
    predicate: (query) => query.queryKey[0] !== "me",
  });
  queryClient.removeQueries({
    predicate: (query) => query.queryKey[0] !== "me",
  });
  queryClient.getMutationCache().clear();
}

export function clearPrivateData(broadcast = true) {
  validatedIdentity = null;
  invalidateSessionRequests();
  void queryClient.cancelQueries();
  queryClient.setQueryData(["me"], null);
  queryClient.removeQueries({
    predicate: (query) => query.queryKey[0] !== "me",
  });
  queryClient.getMutationCache().clear();
  if (broadcast) channel?.postMessage({ type: "logout" });
}

if (channel)
  channel.onmessage = (event: MessageEvent) => {
    if (event.data?.type === "logout") clearPrivateData(false);
    if (event.data?.type === "login") {
      clearPrivateData(false);
      void queryClient.invalidateQueries({ queryKey: ["me"] });
    }
  };

export function announceLogin() {
  channel?.postMessage({ type: "login" });
}
