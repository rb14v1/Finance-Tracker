import { useEffect, useState } from "react";

import { listCategories } from "../../api/categories";
import { extractErrorMessage } from "../../api/client";
import { createTransaction, deleteTransaction, listTransactions, updateTransaction } from "../../api/transactions";
import type { Category, CategoryType, Transaction } from "../../types";
import { currentMonth, formatMoney } from "../../utils/month";

export function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [monthFilter, setMonthFilter] = useState(currentMonth());
  const [categoryFilter, setCategoryFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const [editing, setEditing] = useState<Transaction | null>(null);
  const [categoryId, setCategoryId] = useState<number | "">("");
  const [amount, setAmount] = useState("");
  const [type, setType] = useState<CategoryType>("expense");
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function loadCategories() {
    const res = await listCategories();
    setCategories(res.data.results);
  }

  async function loadTransactions() {
    setLoading(true);
    setError(null);
    try {
      const res = await listTransactions({
        month: monthFilter || undefined,
        category: categoryFilter ? Number(categoryFilter) : undefined,
        type: (typeFilter as CategoryType) || undefined,
      });
      setTransactions(res.data.results);
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
    loadTransactions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [monthFilter, categoryFilter, typeFilter]);

  function startEdit(txn: Transaction) {
    setEditing(txn);
    setCategoryId(txn.category);
    setAmount(txn.amount);
    setType(txn.type);
    setDate(txn.date);
    setNote(txn.note);
  }

  function resetForm() {
    setEditing(null);
    setCategoryId("");
    setAmount("");
    setType("expense");
    setDate(new Date().toISOString().slice(0, 10));
    setNote("");
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
      const payload = { category: Number(categoryId), amount, type, date, note };
      if (editing) {
        await updateTransaction(editing.id, payload);
      } else {
        await createTransaction(payload);
      }
      resetForm();
      await loadTransactions();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this transaction?")) return;
    setError(null);
    try {
      await deleteTransaction(id);
      await loadTransactions();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  const categoriesForType = categories.filter((c) => c.type === type);

  return (
    <div>
      <div className="page-header">
        <h1>Transactions</h1>
      </div>

      <div className="card">
        <div className="form-row">
          <label>
            Month
            <input type="month" value={monthFilter} onChange={(e) => setMonthFilter(e.target.value)} />
          </label>
          <label>
            Category
            <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
              <option value="">All</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </label>
          <label>
            Type
            <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
              <option value="">All</option>
              <option value="income">Income</option>
              <option value="expense">Expense</option>
            </select>
          </label>
        </div>
      </div>

      <div className="card">
        <form className="inline-form" onSubmit={handleSubmit}>
          <label>
            Type
            <select value={type} onChange={(e) => { setType(e.target.value as CategoryType); setCategoryId(""); }}>
              <option value="expense">Expense</option>
              <option value="income">Income</option>
            </select>
          </label>
          <label>
            Category
            <select value={categoryId} onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : "")} required>
              <option value="">Select...</option>
              {categoriesForType.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </label>
          <label>
            Amount
            <input type="number" step="0.01" min="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} required />
          </label>
          <label>
            Date
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
          </label>
          <label>
            Note
            <input value={note} onChange={(e) => setNote(e.target.value)} />
          </label>
          <button type="submit" disabled={submitting}>{editing ? "Save" : "Add transaction"}</button>
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
                <th>Date</th>
                <th>Category</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Note</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((t) => (
                <tr key={t.id}>
                  <td>{t.date}</td>
                  <td>{t.category_name}</td>
                  <td>{t.type}</td>
                  <td>{formatMoney(t.amount)}</td>
                  <td>{t.note}</td>
                  <td className="actions">
                    <button className="secondary" onClick={() => startEdit(t)}>Edit</button>
                    <button className="danger" onClick={() => handleDelete(t.id)}>Delete</button>
                  </td>
                </tr>
              ))}
              {transactions.length === 0 && (
                <tr><td colSpan={6} className="muted">No transactions for this filter.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
