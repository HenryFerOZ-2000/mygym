import { useQuery } from "@tanstack/react-query";
import { api } from "../../shared/api/client";

export type Workspace = {
  id: string;
  name: string;
  kind: "GYM" | "COACH";
  timezone: string;
  role: string;
  capabilities: string[];
};
export function useWorkspaces(userId: number) {
  return useQuery({
    queryKey: [userId, "workspaces"],
    queryFn: ({ signal }) => api<Workspace[]>("me/workspaces/", { signal }),
  });
}
