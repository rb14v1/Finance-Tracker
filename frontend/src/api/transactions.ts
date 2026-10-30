import { apiClient } from "./client";
import type { CategoryType, Paginated, Transaction } from "../types";

export interface TransactionFilters {
  month?: string;
  category?: number;
  type?: CategoryType;
}

export interface TransactionInput {
  category: number;
  amount: string;
  type: CategoryType;
  date: string;
  note?: string;
}

export function listTransactions(filters: TransactionFilters = {}) {
  return apiClient.get<Paginated<Transaction>>("/transactions/", { params: filters });
}

export function createTransaction(data: TransactionInput) {
  return apiClient.post<Transaction>("/transactions/", data);
}

export function updateTransaction(id: number, data: TransactionInput) {
  return apiClient.put<Transaction>(`/transactions/${id}/`, data);
}

export function deleteTransaction(id: number) {
  return apiClient.delete(`/transactions/${id}/`);
}
