import { useEffect, useState } from "react";

import { createBudget, deleteBudget, listBudgets, updateBudget } from "../../api/budgets";
import { listCategories } from "../../api/categories";
import { extractErrorMessage } from "../../api/client";
import type { Budget, Category } from "../../types";
import { currentMonth, formatMoney, monthToFirstOfMonthDate } from "../../utils/month";

export function BudgetsPage() {
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [expenseCategories, setExpenseCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [monthFilter, setMonthFilter] = useState(currentMonth());

  const [editing, setEditing] = useState<Budget | null>(null);
  const [categoryId, setCategoryId] = useState<number | "">("");
  const [month, setMonth] = useState(currentMonth());
  const [limitAmount, setLimitAmount] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function loadCategories() {
    const res = await listCategories("expense");
    setExpenseCategories(res.data.results);
  }

  async function loadBudgets() {
    setLoading(true);
    setError(null);
    try {
      const res = await listBudgets(monthFilter || undefined);
      setBudgets(res.data.results);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    loadBudgets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [monthFilter]);

  function startEdit(budget: Budget) {
    setEditing(budget);
    setCategoryId(budget.category);
    setMonth(budget.month.slice(0, 7));
    setLimitAmount(budget.limit_amount);
  }

  function resetForm() {
    setEditing(null);
    setCategoryId("");
    setMonth(currentMonth());
    setLimitAmount("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!categoryId) {
      setError("Select a category.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const payload = { category: Number(categoryId), month: monthToFirstOfMonthDate(month), limit_amount: limitAmount };
      if (editing) {
        await updateBudget(editing.id, payload);
      } else {
        await createBudget(payload);
      }
      resetForm();
      await loadBudgets();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this budget?")) return;
    setError(null);
    try {
      await deleteBudget(id);
      await loadBudgets();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Budgets</h1>
      </div>

      <div className="card">
        <div className="form-row">
          <label>
            Month
            <input type="month" value={monthFilter} onChange={(e) => setMonthFilter(e.target.value)} />
          </label>
        </div>
      </div>

      <div className="card">
        <form className="inline-form" onSubmit={handleSubmit}>
          <label>
            Category
            <select value={categoryId} onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : "")} required>
              <option value="">Select...</option>
              {expenseCategories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </label>
          <label>
            Month
            <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} required />
          </label>
          <label>
            Limit amount
            <input type="number" step="0.01" min="0.01" value={limitAmount} onChange={(e) => setLimitAmount(e.target.value)} required />
          </label>
          <button type="submit" disabled={submitting}>{editing ? "Save" : "Add budget"}</button>
          {editing && <button type="button" className="secondary" onClick={resetForm}>Cancel</button>}
        </form>
        {error && <div className="form-error">{error}</div>}
      </div>

      <div className="card">
        {loading ? (
          <p>Loading...</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Month</th>
                <th>Category</th>
                <th>Limit</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {budgets.map((b) => (
                <tr key={b.id}>
                  <td>{b.month.slice(0, 7)}</td>
                  <td>{b.category_name}</td>
                  <td>{formatMoney(b.limit_amount)}</td>
                  <td className="actions">
                    <button className="secondary" onClick={() => startEdit(b)}>Edit</button>
                    <button className="danger" onClick={() => handleDelete(b.id)}>Delete</button>
                  </td>
                </tr>
              ))}
              {budgets.length === 0 && (
                <tr><td colSpan={4} className="muted">No budgets for this month.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
