import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";
import { api, errorCode } from "../../api/client";
import type { components } from "../../api/schema";

type Sheet = components["schemas"]["ParsedSheet"];
type Preview = components["schemas"]["Preview"];
type Action = "skip" | "update" | "new";
const select = "rounded-lg border border-stone-300 bg-white px-2 py-1 text-sm";
const PILL: Record<string, string> = {
  ok: "bg-green-100 text-green-800", warning: "bg-amber-100 text-amber-800",
  conflict: "bg-blue-100 text-blue-800", error: "bg-red-100 text-red-800",
};

export function ImportPage() {
  const { t } = useTranslation();
  const eventId = Number(useParams().eventId);
  const path = { event_id: eventId };
  const [sheet, setSheet] = useState<Sheet | null>(null);
  const [mapping, setMapping] = useState<string[]>([]);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [actions, setActions] = useState<Record<number, Action>>({});
  const [result, setResult] = useState<components["schemas"]["CommitResult"] | null>(null);

  const upload = useMutation({
    mutationFn: async (file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`/api/events/${eventId}/imports/parse`, { method: "POST", body: fd, headers: { "X-Requested-With": "rsvp" } });
      if (!res.ok) throw new Error(errorCode(await res.json().catch(() => undefined)));
      return (await res.json()) as Sheet;
    },
    onSuccess: (s) => { setSheet(s); setMapping(s.mapping); setPreview(null); setResult(null); },
  });
  const runPreview = useMutation({
    mutationFn: async () => {
      const r = await api.POST("/api/events/{event_id}/imports/preview", { params: { path }, body: { mapping, rows: sheet!.rows } });
      if (r.error) throw new Error(errorCode(r.error));
      return r.data;
    },
    onSuccess: (p) => { setPreview(p); setActions({}); },
  });
  const commit = useMutation({
    mutationFn: async () => {
      const r = await api.POST("/api/events/{event_id}/imports/commit", { params: { path }, body: { mapping, rows: sheet!.rows, actions } });
      if (r.error) throw new Error(errorCode(r.error));
      return r.data;
    },
    onSuccess: (r) => { setResult(r); setSheet(null); setPreview(null); },
  });
  const error = upload.error ?? runPreview.error ?? commit.error;

  // Target options: fixed ones plus person/phone N up to the highest N currently used (+1).
  const maxN = Math.max(3, ...mapping.map((m) => Number(m.split(":")[1]) || 0)) + 1;
  const targets = ["ignore", "invitation_name", "group", "note",
    ...Array.from({ length: maxN }, (_, i) => `person:${i + 1}`), ...Array.from({ length: maxN }, (_, i) => `phone:${i + 1}`)];
  const label = (tg: string) => { const [k, n] = tg.split(":"); return t(`import.target.${k}`, { n }); };

  if (result) return (
    <div className="flex flex-col items-start gap-3 rounded-2xl border border-stone-200 bg-white p-6">
      <h2 className="text-lg font-semibold">{t("import.done")}</h2>
      <p>{t("import.result", result)}</p>
      <Link to={`/events/${eventId}/invitations`} className="rounded-lg bg-stone-900 px-4 py-2 text-white">{t("import.toInvitations")}</Link>
    </div>
  );

  return (
    <section className="flex flex-col gap-4">
      {!sheet && (
        <div className="flex flex-col items-start gap-3 rounded-2xl border border-dashed border-stone-300 bg-white p-8">
          <h2 className="text-lg font-semibold">{t("import.title")}</h2>
          <p className="text-stone-600">{t("import.hint")}</p>
          <label className="cursor-pointer rounded-lg bg-stone-900 px-4 py-2 text-white">
            {t("import.choose")}
            <input type="file" accept=".xlsx,.csv" className="sr-only" onChange={(e) => e.target.files?.[0] && upload.mutate(e.target.files[0])} />
          </label>
        </div>
      )}
      {sheet && !preview && (
        <div className="flex flex-col gap-3 rounded-2xl border border-stone-200 bg-white p-4">
          <h2 className="text-lg font-semibold">{t("import.mapTitle")}</h2>
          <p className="text-sm text-stone-600">{t("import.hint")} {t("import.mapHint")} ({t("import.rows", { count: sheet.rows.length })})</p>
          <div className="overflow-x-auto">
            <table className="w-full text-start text-sm">
              <tbody>
                {sheet.headers.map((h, i) => (
                  <tr key={i} className="border-t border-stone-100">
                    <td className="py-2 pe-4 font-medium" dir="auto">{h || "—"}</td>
                    <td className="py-2 pe-4 text-stone-500" dir="auto">{sheet.rows.slice(0, 2).map((r) => r[i]).filter(Boolean).join(" · ")}</td>
                    <td className="py-2">
                      <select className={select} value={mapping[i]} onChange={(e) => setMapping(mapping.map((m, j) => (j === i ? e.target.value : m)))}>
                        {targets.map((tg) => <option key={tg} value={tg}>{label(tg)}</option>)}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex gap-2">
            <button onClick={() => runPreview.mutate()} disabled={runPreview.isPending} className="rounded-lg bg-stone-900 px-4 py-2 text-white disabled:opacity-50">{t("import.preview")}</button>
            <button onClick={() => setSheet(null)} className="px-4 py-2 text-stone-600">{t("common.cancel")}</button>
          </div>
        </div>
      )}
      {sheet && preview && (
        <div className="flex flex-col gap-3 rounded-2xl border border-stone-200 bg-white p-4">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="me-auto text-lg font-semibold">{t("import.preview")}</h2>
            {Object.entries(preview.counts).map(([k, n]) => <span key={k} className={`rounded-full px-2 py-0.5 text-xs ${PILL[k]}`}>{t(`import.counts.${k}`)}: {n}</span>)}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-start text-sm">
              <thead><tr className="text-stone-500">
                {["colRow", "colName", "colPeople", "colIssues", "colAction"].map((c) => <th key={c} className="py-1 pe-3 text-start font-normal">{t(`import.${c}`)}</th>)}
              </tr></thead>
              <tbody>
                {preview.rows.map((r) => {
                  const action = actions[r.index] ?? r.default_action;
                  return (
                    <tr key={r.index} className="border-t border-stone-100 align-top">
                      <td className="py-2 pe-3 text-stone-500">{r.index + 1}</td>
                      <td className="py-2 pe-3" dir="auto">{r.draft?.display_name ?? "—"}</td>
                      <td className="py-2 pe-3 text-stone-600" dir="auto">{r.draft?.members.map((m) => m.name).join(", ")}</td>
                      <td className="py-2 pe-3">
                        <div className="flex flex-col gap-1">
                          {r.issues.map((i, k) => <span key={k} className={`w-fit rounded-full px-2 py-0.5 text-xs ${PILL[i.level === "conflict" ? "conflict" : i.level]}`}>{t(`issues.${i.code}`, { detail: i.detail })}</span>)}
                          {r.conflict && <span className="text-xs text-stone-500" dir="auto">{t("import.conflictWith", { name: r.conflict.invitation_name })}</span>}
                        </div>
                      </td>
                      <td className="py-2">
                        {r.status !== "error" && (r.conflict || r.default_action === "skip") && (
                          <select className={select} value={action} onChange={(e) => setActions({ ...actions, [r.index]: e.target.value as Action })}>
                            <option value="skip">{t("import.action.skip")}</option>
                            {r.conflict && <option value="update">{t("import.action.update")}</option>}
                            <option value="new">{t("import.action.new")}</option>
                          </select>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="flex gap-2">
            <button onClick={() => commit.mutate()} disabled={commit.isPending} className="rounded-lg bg-stone-900 px-4 py-2 text-white disabled:opacity-50">{t("import.confirm")}</button>
            <button onClick={() => setPreview(null)} className="px-4 py-2 text-stone-600">{t("import.back")}</button>
          </div>
        </div>
      )}
      {error && <p role="alert" className="text-sm text-red-700">{t(`errors.${error.message}`, t("errors.generic"))}</p>}
    </section>
  );
}
