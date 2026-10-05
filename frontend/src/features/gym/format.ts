import { ApiError } from "../../shared/api/client";

export function planAvailability(
  plan: {
    is_active: boolean;
    available_from: string | null;
    available_until: string | null;
  },
  date: string,
) {
  if (!plan.is_active) return "Inactivo";
  if (plan.available_from && date < plan.available_from) return "Programado";
  if (plan.available_until && date > plan.available_until)
    return "Venta finalizada";
  return "Disponible";
}

export function message(error: unknown) {
  return error instanceof ApiError
    ? [error.message, ...Object.values(error.fields).flat()].join(" ")
    : "No se pudo completar. Revisa la conexión y vuelve a intentar.";
}
export function localDate(zone: string) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: zone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const part = (type: string) => parts.find((p) => p.type === type)!.value;
  return `${part("year")}-${part("month")}-${part("day")}`;
}
export function shiftDate(date: string, days: number) {
  const parsed = new Date(`${date}T12:00:00Z`);
  parsed.setUTCDate(parsed.getUTCDate() + days);
  return parsed.toISOString().slice(0, 10);
}
export function displayDate(date: string | null) {
  if (!date) return "Sin días de servicio";
  const [year, month, day] = date.split("-");
  return `${day}/${month}/${year}`;
}
