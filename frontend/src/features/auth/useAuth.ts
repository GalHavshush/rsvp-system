import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";

export function useAuth() {
  return useQuery({
    queryKey: ["auth"],
    queryFn: async () => {
      const me = await api.GET("/api/auth/me");
      if (me.data) return { user: me.data, needsSetup: false };
      const status = await api.GET("/api/auth/status");
      return { user: null, needsSetup: status.data?.needs_setup ?? false };
    },
    retry: false,
  });
}
