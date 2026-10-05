import { api, ApiError } from "../../shared/api/client";
import { clearPrivateData } from "./session";

export async function endSession() {
  try {
    await api("auth/logout/", { method: "POST", body: "{}" });
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 403) throw error;
    try {
      await api("auth/me/");
    } catch (checkError) {
      if (checkError instanceof ApiError && checkError.status === 403) {
        clearPrivateData();
        return;
      }
      throw checkError;
    }
    // A live session means the original 403 may be CSRF failure; do not claim logout.
    throw error;
  }
  clearPrivateData();
}
