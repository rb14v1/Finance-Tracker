import { createBrowserRouter, Navigate } from "react-router-dom";

import { ProtectedRoute } from "../auth/ProtectedRoute";
import { Dashboard } from "../features/dashboard/Dashboard";
import { BudgetsPage } from "../features/budgets/BudgetsPage";
import { CategoriesPage } from "../features/categories/CategoriesPage";
import { TransactionsPage } from "../features/transactions/TransactionsPage";
import { AppLayout } from "../layouts/AppLayout";
import { LoginPage } from "../pages/LoginPage";
import { RegisterPage } from "../pages/RegisterPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: "/", element: <Dashboard /> },
          { path: "/transactions", element: <TransactionsPage /> },
          { path: "/categories", element: <CategoriesPage /> },
          { path: "/budgets", element: <BudgetsPage /> },
        ],
      },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
