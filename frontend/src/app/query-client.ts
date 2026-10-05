import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      staleTime: 0,
      gcTime: 5 * 60_000,
      refetchOnWindowFocus: "always",
    },
    mutations: { retry: false },
  },
});
