export type ClientInput = { full_name: string; phone: string; email: string };
export function validateClient(data: ClientInput): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!data.full_name.trim() || data.full_name.trim().length > 200)
    errors.full_name = "Escribe un nombre de hasta 200 caracteres.";
  if (data.phone.trim().length > 32) errors.phone = "Usa hasta 32 caracteres.";
  if (
    data.email.trim() &&
    (data.email.trim().length > 254 ||
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email.trim()))
  )
    errors.email = "Escribe un correo válido.";
  return errors;
}
