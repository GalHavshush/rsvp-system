import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import { LanguageSwitcher } from "../components/LanguageSwitcher";

export function AdminLayout() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const logout = useMutation({
    mutationFn: () => api.POST("/api/auth/logout"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["auth"] }),
  });
  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between border-b border-stone-200 bg-white px-4 py-3">
        <strong>{t("app.name")}</strong>
        <div className="flex items-center gap-4">
          <LanguageSwitcher />
          <button className="text-sm text-stone-600 hover:text-stone-900" onClick={() => logout.mutate()}>{t("common.logout")}</button>
        </div>
      </header>
      <main className="mx-auto max-w-4xl p-4"><Outlet /></main>
    </div>
  );
}
