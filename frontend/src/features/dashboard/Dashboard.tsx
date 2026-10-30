import { useEffect, useState } from "react";

import { fetchDashboard } from "../../api/dashboard";
import { extractErrorMessage } from "../../api/client";
import type { DashboardSummary } from "../../types";
import { currentMonth, formatMoney } from "../../utils/month";

export function Dashboard() {
  const [month, setMonth] = useState(currentMonth());
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchDashboard(month)
      .then((res) => setSummary(res.data))
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [month]);

  const net = summary ? parseFloat(summary.net) : 0;

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <label>
          Month{" "}
          <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} />
        </label>
      </div>

      {error && <div className="form-error">{error}</div>}

      {loading || !summary ? (
        <p>Loading...</p>
      ) : (
        <>
          <div className="summary-grid">
            <div className="summary-tile">
              <div className="label">Income</div>
              <div className="value positive">{formatMoney(summary.total_income)}</div>
            </div>
            <div className="summary-tile">
              <div className="label">Expenses</div>
              <div className="value negative">{formatMoney(summary.total_expenses)}</div>
            </div>
            <div className="summary-tile">
              <div className="label">Net</div>
              <div className={`value ${net >= 0 ? "positive" : "negative"}`}>{formatMoney(summary.net)}</div>
            </div>
          </div>

          <div className="card">
            <h2>Expense categories</h2>
            {summary.categories.length === 0 && <p className="muted">No expense activity for this month.</p>}
            {summary.categories.map((row) => {
              const spent = parseFloat(row.spent);
              const limit = row.budget_limit ? parseFloat(row.budget_limit) : null;
              const pct = limit ? Math.min(100, (spent / limit) * 100) : null;
              const over = limit !== null && spent > limit;
              return (
                <div className="budget-row" key={row.category}>
                  <div className="budget-row-header">
                    <span>{row.category_name}</span>
                    <span>
                      {formatMoney(row.spent)}
                      {limit !== null && ` / ${formatMoney(row.budget_limit!)}`}
                      {row.remaining !== null && (
                        <span className="muted"> ({over ? "over by " : "remaining "}{formatMoney(Math.abs(parseFloat(row.remaining)))})</span>
                      )}
                    </span>
                  </div>
                  {limit !== null && (
                    <div className="budget-bar-track">
                      <div className={`budget-bar-fill ${over ? "over" : ""}`} style={{ width: `${pct}%` }} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
