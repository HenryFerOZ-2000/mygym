import type { Workspace } from "../workspaces/use-workspaces";

export function operationAccess(workspace?: Workspace) {
  const operator =
    workspace?.role === "OWNER" || workspace?.role === "RECEPTION";
  const owner = workspace?.role === "OWNER";
  const has = (cap: string) => !!workspace?.capabilities.includes(cap);
  const gym = workspace?.kind === "GYM";
  return {
    owner,
    clients: !!(operator && has("clients.manage")),
    plans: !!(gym && operator && has("gym.manage")),
    attendance: !!(gym && operator && has("gym.attendance")),
    expiries: !!(gym && operator && has("gym.manage")),
    attendanceReport: !!(gym && owner && has("gym.reports")),
    financialReport: !!(
      owner &&
      has("receivables.reports") &&
      has("receivables.manage")
    ),
  };
}

export function workspaceStart(workspace: Workspace) {
  const access = operationAccess(workspace);
  const section = access.clients
    ? "clients"
    : access.attendance
      ? "attendance"
      : access.plans
        ? "plans"
        : access.attendanceReport || access.financialReport
          ? "reports"
          : "clients";
  return `/workspaces/${workspace.id}/${section}`;
}
