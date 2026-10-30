import { apiClient } from "./client";
import type { Budget, Paginated } from "../types";

export interface BudgetInput {
  category: number;
  month: string;
  limit_amount: string;
}

export function listBudgets(month?: string) {
  return apiClient.get<Paginated<Budget>>("/budgets/", { params: month ? { month } : {} });
}

export function createBudget(data: BudgetInput) {
  return apiClient.post<Budget>("/budgets/", data);
}

export function updateBudget(id: number, data: BudgetInput) {
  return apiClient.put<Budget>(`/budgets/${id}/`, data);
}

export function deleteBudget(id: number) {
  return apiClient.delete(`/budgets/${id}/`);
}
