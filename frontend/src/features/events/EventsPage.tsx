import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../api/client";
import type { components } from "../../api/schema";

type EventIn = components["schemas"]["EventIn"];
const TEXT_FIELDS = ["venue", "address", "waze_url", "maps_url", "hosts", "notes"] as const;
const LTR_FIELDS = new Set(["waze_url", "maps_url"]);
const input = "w-full rounded-lg border border-stone-300 bg-white px-3 py-2";

function EventForm({ initial, onDone }: { initial?: components["schemas"]["EventOut"]; onDone: () => void }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [v, setV] = useState<EventIn>(initial ?? { name: "", type: "wedding", default_language: "he" });
  const set = (k: keyof EventIn, val: string) => setV((p) => ({ ...p, [k]: val === "" ? null : val }));
  const save = useMutation({
    mutationFn: async () => {
      const r = initial
        ? await api.PUT("/api/events/{event_id}", { params: { path: { event_id: initial.id } }, body: v })
        : await api.POST("/api/events", { body: v });
      if (r.error) throw new Error("generic");
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["events"] }); onDone(); },
  });
  const onSubmit = (e: FormEvent) => { e.preventDefault(); save.mutate(); };
  const label = (k: string) => <span className="mb-1 block text-sm text-stone-600">{t(`events.fields.${k}`)}</span>;
  return (
    <form onSubmit={onSubmit} className="grid gap-3 rounded-2xl border border-stone-200 bg-white p-4 sm:grid-cols-2">
      <label className="sm:col-span-2">{label("name")}<input required className={input} value={v.name} onChange={(e) => set("name", e.target.value)} /></label>
      <label>{label("type")}
        <select className={input} value={v.type ?? "wedding"} onChange={(e) => set("type", e.target.value)}>
          <option value="wedding">{t("events.types.wedding")}</option><option value="other">{t("events.types.other")}</option>
        </select></label>
      <label>{label("default_language")}
        <select className={input} value={v.default_language} onChange={(e) => set("default_language", e.target.value)}>
          <option value="he">עברית</option><option value="en">English</option>
        </select></label>
      <label>{label("date")}<input type="date" className={input} value={v.date ?? ""} onChange={(e) => set("date", e.target.value)} /></label>
      <label>{label("time")}<input type="time" className={input} value={v.time ?? ""} onChange={(e) => set("time", e.target.value)} /></label>
      <label>{label("rsvp_deadline")}<input type="date" className={input} value={v.rsvp_deadline ?? ""} onChange={(e) => set("rsvp_deadline", e.target.value)} /></label>
      {TEXT_FIELDS.map((k) => (
        <label key={k} className={k === "notes" ? "sm:col-span-2" : ""}>{label(k)}
          <input dir={LTR_FIELDS.has(k) ? "ltr" : "auto"} className={input} value={v[k] ?? ""} onChange={(e) => set(k, e.target.value)} />
        </label>
      ))}
      {save.error && <p role="alert" className="text-sm text-red-700 sm:col-span-2">{t("errors.generic")}</p>}
      <div className="flex gap-2 sm:col-span-2">
        <button disabled={save.isPending} className="rounded-lg bg-stone-900 px-4 py-2 text-white disabled:opacity-50">{t("common.save")}</button>
        <button type="button" onClick={onDone} className="rounded-lg px-4 py-2 text-stone-600">{t("common.cancel")}</button>
      </div>
    </form>
  );
}

export function EventsPage() {
  const { t, i18n } = useTranslation();
  const qc = useQueryClient();
  const [editing, setEditing] = useState<components["schemas"]["EventOut"] | "new" | null>(null);
  const events = useQuery({ queryKey: ["events"], queryFn: async () => (await api.GET("/api/events")).data ?? [] });
  const remove = useMutation({
    mutationFn: (id: number) => api.DELETE("/api/events/{event_id}", { params: { path: { event_id: id } } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["events"] }),
  });
  const fmt = (d: string) => new Intl.DateTimeFormat(i18n.language, { dateStyle: "long" }).format(new Date(d + "T00:00"));
  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{t("events.title")}</h1>
        {!editing && <button onClick={() => setEditing("new")} className="rounded-lg bg-stone-900 px-4 py-2 text-white">{t("events.new")}</button>}
      </div>
      {editing && <EventForm initial={editing === "new" ? undefined : editing} onDone={() => setEditing(null)} />}
      {events.data?.length === 0 && !editing && <p className="rounded-2xl border border-dashed border-stone-300 p-8 text-center text-stone-500">{t("events.empty")}</p>}
      <ul className="flex flex-col gap-2">
        {events.data?.map((e) => (
          <li key={e.id} className="flex items-center justify-between rounded-2xl border border-stone-200 bg-white p-4">
            <div>
              <div className="font-medium" dir="auto">{e.name}</div>
              <div className="text-sm text-stone-500">{[e.date && fmt(e.date), e.venue].filter(Boolean).join(" · ")}</div>
            </div>
            <div className="flex gap-3 text-sm">
              <button onClick={() => setEditing(e)} className="text-stone-600">{t("common.edit")}</button>
              <button onClick={() => confirm(t("events.confirmDelete")) && remove.mutate(e.id)} className="text-red-700">{t("common.delete")}</button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
