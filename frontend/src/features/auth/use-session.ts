import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "../../shared/api/client";
import { reconcileIdentity } from "./session";

export type User = { id: number; username: string };
export function useSession() {
  return useQuery({
    queryKey: ["me"],
    queryFn: async ({ signal }) => {
      try {
        const user = await api<User>("auth/me/", { signal });
        reconcileIdentity(user.id);
        return user;
      } catch (error) {
        if (error instanceof ApiError && error.status === 403) {
          reconcileIdentity(null);
          return null;
        }
        throw error;
      }
    },
  });
}
