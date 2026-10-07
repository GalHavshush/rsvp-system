import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../api/client";
import type { components } from "../../api/schema";

type Out = components["schemas"]["InvitationOut"];
type Group = components["schemas"]["GroupOut"];
type ContactState = { phone: string; member: number | null };
const input = "w-full rounded-lg border border-stone-300 bg-white px-3 py-2";

function initial(inv?: Out) {
  if (!inv) return { name: "", group: "", notes: "", members: [""], contacts: [] as ContactState[] };
  return {
    name: inv.display_name, group: inv.group_name ?? "", notes: inv.notes ?? "",
    members: inv.members.map((m) => m.name),
    contacts: inv.contacts.map((c) => {
      const i = inv.members.findIndex((m) => m.id === c.member_id);
      return { phone: c.phone_raw, member: i >= 0 ? i : null };
    }),
  };
}

export function InvitationForm({ eventId, invitation, groups, onDone }: {
  eventId: number; invitation?: Out; groups: Group[]; onDone: () => void;
}) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [f, setF] = useState(initial(invitation));
  const save = useMutation({
    mutationFn: async () => {
      // Blank people are dropped; contacts pointing at them are re-indexed.
      const keep = f.members.map((m, i) => (m.trim() ? i : -1));
      const remap = (i: number | null) => (i === null || keep[i] < 0 ? null : keep.slice(0, i).filter((k) => k >= 0).length);
      const body = {
        display_name: f.name, group_name: f.group || null, notes: f.notes || null,
        members: f.members.filter((m) => m.trim()).map((name) => ({ name })),
        contacts: f.contacts.filter((c) => c.phone.trim()).map((c) => ({ phone: c.phone, member_index: remap(c.member) })),
      };
      const r = invitation
        ? await api.PUT("/api/invitations/{invitation_id}", { params: { path: { invitation_id: invitation.id } }, body })
        : await api.POST("/api/events/{event_id}/invitations", { params: { path: { event_id: eventId } }, body });
      if (r.error) throw new Error("generic");
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["invitations"] }); qc.invalidateQueries({ queryKey: ["groups"] }); onDone(); },
  });
  const onSubmit = (e: FormEvent) => { e.preventDefault(); save.mutate(); };
  const setMember = (i: number, v: string) => setF((p) => ({ ...p, members: p.members.map((m, j) => (j === i ? v : m)) }));
  const removeMember = (i: number) => setF((p) => ({
    ...p, members: p.members.filter((_, j) => j !== i),
    contacts: p.contacts.map((c) => ({ ...c, member: c.member === null || c.member === i ? null : c.member > i ? c.member - 1 : c.member })),
  }));
  const setContact = (i: number, patch: Partial<ContactState>) =>
    setF((p) => ({ ...p, contacts: p.contacts.map((c, j) => (j === i ? { ...c, ...patch } : c)) }));
  const lbl = "mb-1 block text-sm text-stone-600";
  const link = "text-sm text-stone-600 hover:text-stone-900";
  return (
    <form onSubmit={onSubmit} className="grid gap-4 rounded-2xl border border-stone-200 bg-white p-4 sm:grid-cols-2">
      <label><span className={lbl}>{t("invitations.form.name")}</span>
        <input required className={input} dir="auto" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></label>
      <label><span className={lbl}>{t("invitations.form.group")}</span>
        <input list="group-options" className={input} dir="auto" value={f.group} onChange={(e) => setF({ ...f, group: e.target.value })} />
        <datalist id="group-options">{groups.map((g) => <option key={g.id} value={g.name} />)}</datalist></label>
      <fieldset className="flex flex-col gap-2">
        <legend className={lbl}>{t("invitations.form.members")}</legend>
        {f.members.map((m, i) => (
          <div key={i} className="flex gap-2">
            <input className={input} dir="auto" placeholder={t("invitations.form.memberName")} value={m} onChange={(e) => setMember(i, e.target.value)} />
            <button type="button" className={link} onClick={() => removeMember(i)} aria-label={t("invitations.form.remove")}>✕</button>
          </div>
        ))}
        <button type="button" className={`${link} self-start`} onClick={() => setF({ ...f, members: [...f.members, ""] })}>+ {t("invitations.form.addMember")}</button>
      </fieldset>
      <fieldset className="flex flex-col gap-2">
        <legend className={lbl}>{t("invitations.form.phones")}</legend>
        {f.contacts.map((c, i) => (
          <div key={i} className="flex gap-2">
            <input dir="ltr" className={input} placeholder={t("invitations.form.phone")} value={c.phone} onChange={(e) => setContact(i, { phone: e.target.value })} />
            <select className={input} value={c.member ?? ""} onChange={(e) => setContact(i, { member: e.target.value === "" ? null : Number(e.target.value) })}>
              <option value="">{t("invitations.form.noMember")}</option>
              {f.members.map((m, j) => m.trim() && <option key={j} value={j}>{m}</option>)}
            </select>
            <button type="button" className={link} onClick={() => setF({ ...f, contacts: f.contacts.filter((_, j) => j !== i) })} aria-label={t("invitations.form.remove")}>✕</button>
          </div>
        ))}
        <button type="button" className={`${link} self-start`} onClick={() => setF({ ...f, contacts: [...f.contacts, { phone: "", member: null }] })}>+ {t("invitations.form.addPhone")}</button>
      </fieldset>
      <label className="sm:col-span-2"><span className={lbl}>{t("invitations.form.notes")}</span>
        <input className={input} dir="auto" value={f.notes} onChange={(e) => setF({ ...f, notes: e.target.value })} /></label>
      {save.error && <p role="alert" className="text-sm text-red-700 sm:col-span-2">{t("errors.generic")}</p>}
      <div className="flex gap-2 sm:col-span-2">
        <button disabled={save.isPending} className="rounded-lg bg-stone-900 px-4 py-2 text-white disabled:opacity-50">{t("common.save")}</button>
        <button type="button" onClick={onDone} className="rounded-lg px-4 py-2 text-stone-600">{t("common.cancel")}</button>
      </div>
    </form>
  );
}
