import createClient from "openapi-fetch";
import type { paths } from "./schema";

export const api = createClient<paths>({ headers: { "X-Requested-With": "rsvp" } });

/** Error code from the backend (`detail`), mapped to `errors.<code>` in the translations. */
export function errorCode(error: unknown): string {
  const d = (error as { detail?: unknown } | undefined)?.detail;
  return typeof d === "string" ? d : "generic";
}
