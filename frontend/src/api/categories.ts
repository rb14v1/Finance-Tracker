import { apiClient } from "./client";
import type { Category, CategoryType, Paginated } from "../types";

export function listCategories(type?: CategoryType) {
  return apiClient.get<Paginated<Category>>("/categories/", { params: type ? { type } : {} });
}

export function createCategory(data: { name: string; type: CategoryType }) {
  return apiClient.post<Category>("/categories/", data);
}

export function updateCategory(id: number, data: { name: string; type: CategoryType }) {
  return apiClient.put<Category>(`/categories/${id}/`, data);
}

export function deleteCategory(id: number) {
  return apiClient.delete(`/categories/${id}/`);
}
