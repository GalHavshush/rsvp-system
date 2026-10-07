import { useTranslation } from "react-i18next";

export function LanguageSwitcher() {
  const { t, i18n } = useTranslation();
  return (
    <button className="text-sm text-stone-600 hover:text-stone-900" onClick={() => i18n.changeLanguage(i18n.language === "he" ? "en" : "he")}>
      {t("common.language")}
    </button>
  );
}
