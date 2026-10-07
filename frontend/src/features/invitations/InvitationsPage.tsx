import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { api } from "../../api/client";
import type { components } from "../../api/schema";
import { InvitationForm } from "./InvitationForm";

type Out = components["schemas"]["InvitationOut"];
type Sort = "name" | "-name" | "-updated" | "status";
const field = "rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm";
const BADGE: Record<string, string> = {
  no_response: "bg-stone-100 text-stone-600", coming: "bg-green-100 text-green-800",
  not_coming: "bg-red-100 text-red-800", maybe: "bg-amber-100 text-amber-800",
};

export function InvitationsPage() {
  const { t, i18n } = useTranslation();
  const eventId = Number(useParams().eventId);
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [groupId, setGroupId] = useState("");
  const [missing, setMissing] = useState(false);
  const [invalid, setInvalid] = useState(false);
  const [sort, setSort] = useState<Sort>("name");
  const [editing, setEditing] = useState<Out | "new" | null>(null);

  const query = {
    q: q || undefined, rsvp_status: (status || undefined) as Out["rsvp_status"] | undefined,
    group_id: groupId ? Number(groupId) : undefined, missing_phone: missing || undefined, invalid_phone: invalid || undefined,
  };
  const groups = useQuery({
    queryKey: ["groups", eventId],
    queryFn: async () => (await api.GET("/api/events/{event_id}/groups", { params: { path: { event_id: eventId } } })).data ?? [],
  });
  const list = useQuery({
    queryKey: ["invitations", eventId, query, sort],
    queryFn: async () => (await api.GET("/api/events/{event_id}/invitations", { params: { path: { event_id: eventId }, query: { ...query, sort } } })).data,
  });
  const remove = useMutation({
    mutationFn: (id: number) => api.DELETE("/api/invitations/{invitation_id}", { params: { path: { invitation_id: id } } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["invitations"] }),
  });
  const exportUrl = `/api/events/${eventId}/invitations/export?` + new URLSearchParams(
    Object.entries({ lang: i18n.language, ...query }).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)]));
  const filtered = Object.values(query).some(Boolean);

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <input className={`${field} min-w-48 flex-1`} dir="auto" placeholder={t("invitations.search")} value={q} onChange={(e) => setQ(e.target.value)} />
        <select className={field} value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">{t("invitations.allStatuses")}</option>
          {Object.keys(BADGE).map((s) => <option key={s} value={s}>{t(`rsvp.status.${s}`)}</option>)}
        </select>
        <select className={field} value={groupId} onChange={(e) => setGroupId(e.target.value)}>
          <option value="">{t("invitations.allGroups")}</option>
          {groups.data?.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
        </select>
        <select className={field} value={sort} onChange={(e) => setSort(e.target.value as Sort)}>
          {(["name", "-name", "-updated", "status"] as const).map((s) => <option key={s} value={s}>{t(`invitations.sort.${s}`)}</option>)}
        </select>
        <label className="flex items-center gap-1 text-sm"><input type="checkbox" checked={missing} onChange={(e) => setMissing(e.target.checked)} />{t("invitations.missingPhone")}</label>
        <label className="flex items-center gap-1 text-sm"><input type="checkbox" checked={invalid} onChange={(e) => setInvalid(e.target.checked)} />{t("invitations.invalidPhone")}</label>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-sm text-stone-500">{t("invitations.total", { count: list.data?.total ?? 0 })}</span>
        <div className="flex gap-2">
          <a href={exportUrl} className="rounded-lg border border-stone-300 px-3 py-2 text-sm">{t("invitations.export")}</a>
          {!editing && <button onClick={() => setEditing("new")} className="rounded-lg bg-stone-900 px-4 py-2 text-sm text-white">{t("invitations.new")}</button>}
        </div>
      </div>
      {editing && (
        <InvitationForm key={editing === "new" ? "new" : editing.id} eventId={eventId} groups={groups.data ?? []}
          invitation={editing === "new" ? undefined : editing} onDone={() => setEditing(null)} />
      )}
      {list.data?.total === 0 && <p className="rounded-2xl border border-dashed border-stone-300 p-8 text-center text-stone-500">{filtered ? t("invitations.noResults") : t("invitations.empty")}</p>}
      <ul className="flex flex-col gap-2">
        {list.data?.items.map((inv) => (
          <li key={inv.id} className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-stone-200 bg-white p-4">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium" dir="auto">{inv.display_name}</span>
                <span className={`rounded-full px-2 py-0.5 text-xs ${BADGE[inv.rsvp_status]}`}>{t(`rsvp.status.${inv.rsvp_status}`)}</span>
                {inv.attendee_count != null && inv.rsvp_status === "coming" && <span className="text-xs text-stone-500">{inv.attendee_count} {t("invitations.attendees")}</span>}
                {inv.group_name && <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs text-stone-600" dir="auto">{inv.group_name}</span>}
              </div>
              <div className="truncate text-sm text-stone-500" dir="auto">
                {inv.members.map((m) => m.name).join(", ")}
                {inv.contacts.length > 0 && " · "}
                {inv.contacts.map((c, i) => (
                  <span key={c.id}>{i > 0 && ", "}<bdi dir="ltr" className={c.phone_valid ? "" : "text-red-700"}>{c.phone_e164 ?? c.phone_raw}</bdi></span>
                ))}
              </div>
            </div>
            <div className="flex gap-3 text-sm">
              <button onClick={() => setEditing(inv)} className="text-stone-600">{t("common.edit")}</button>
              <button onClick={() => confirm(t("invitations.confirmDelete")) && remove.mutate(inv.id)} className="text-red-700">{t("common.delete")}</button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
