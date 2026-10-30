export type CategoryType = "income" | "expense";

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  date_joined: string;
}

export interface Category {
  id: number;
  name: string;
  type: CategoryType;
  created_at: string;
}

export interface Transaction {
  id: number;
  category: number;
  category_name: string;
  amount: string;
  type: CategoryType;
  date: string;
  note: string;
  created_at: string;
}

export interface Budget {
  id: number;
  category: number;
  category_name: string;
  month: string;
  limit_amount: string;
  created_at: string;
}

export interface DashboardCategoryRow {
  category: number;
  category_name: string;
  spent: string;
  budget_limit: string | null;
  remaining: string | null;
}

export interface DashboardSummary {
  month: string;
  total_income: string;
  total_expenses: string;
  net: string;
  categories: DashboardCategoryRow[];
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
