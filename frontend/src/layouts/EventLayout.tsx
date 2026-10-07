import { NavLink, Outlet, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";

const tab = ({ isActive }: { isActive: boolean }) =>
  `rounded-lg px-3 py-1.5 text-sm ${isActive ? "bg-stone-900 text-white" : "text-stone-600 hover:bg-stone-100"}`;

export function EventLayout() {
  const { t } = useTranslation();
  const { eventId } = useParams();
  const id = Number(eventId);
  const event = useQuery({
    queryKey: ["event", id],
    queryFn: async () => (await api.GET("/api/events/{event_id}", { params: { path: { event_id: id } } })).data,
  });
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <NavLink to="/" className="text-sm text-stone-500 hover:text-stone-900">← {t("nav.back")}</NavLink>
        <h1 className="text-xl font-semibold" dir="auto">{event.data?.name}</h1>
      </div>
      <nav className="flex gap-2">
        <NavLink to="invitations" className={tab}>{t("nav.invitations")}</NavLink>
        <NavLink to="import" className={tab}>{t("nav.import")}</NavLink>
      </nav>
      <Outlet />
    </div>
  );
}
