import { apiClient } from "./client";
import type { DashboardSummary } from "../types";

export function fetchDashboard(month?: string) {
  return apiClient.get<DashboardSummary>("/dashboard/", { params: month ? { month } : {} });
}
