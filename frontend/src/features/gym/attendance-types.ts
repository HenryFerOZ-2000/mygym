export const serviceLabels: Record<string, string> = {
  ACTIVE: "Vigente",
  FROZEN: "Congelada",
  EXPIRED: "Vencida",
  FUTURE: "Programada",
  NO_MEMBERSHIP: "Sin plan",
  CLIENT_INACTIVE: "Ficha inactiva",
  EXPIRING: "Próximos a vencer",
};
export type EntryPreview = {
  client_id: string;
  full_name: string;
  status: string;
  last_day: string | null;
  previous_last_day: string | null;
  next_start: string | null;
  local_date: string;
  today_count: number;
  timezone: string;
};
export type Entry = {
  id: string;
  client_id: string;
  full_name: string;
  actor: string;
  created_at: string;
  local_date: string;
  timezone: string;
  decision: string;
  service_status: string;
  reason: string;
  voided: boolean;
  void_reason: string | null;
  void_actor: string | null;
  voided_at: string | null;
};
