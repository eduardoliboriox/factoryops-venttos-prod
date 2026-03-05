.ts-card {
  border: 1px solid rgba(15, 23, 42, 0.10);
  border-radius: 14px;
  background: #fff;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.ts-card .ts-header {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  background: linear-gradient(180deg, rgba(25, 135, 84, 0.10), transparent);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.ts-muted {
  color: rgba(15, 23, 42, 0.65);
  font-size: 12px;
}

.ts-badge {
  font-weight: 800;
}

.ts-table th {
  white-space: nowrap;
  text-align: center;
  vertical-align: middle;
}

.ts-table td {
  vertical-align: middle;
  text-align: center;
}

.ts-table .ts-col-op {
  text-align: left !important;
}

.ts-status-pill {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-weight: 900;
  font-size: 12px;
  line-height: 1.1;
  letter-spacing: 0.3px;
  min-width: 86px;
  text-align: center;
}

.ts-status-ok {
  background: #198754;
  color: #fff;
}

.ts-status-balance {
  background: #dc3545;
  color: #fff;
}

.ts-row-balance {
  background: rgba(220, 53, 69, 0.14);
  box-shadow: inset 5px 0 0 rgba(220, 53, 69, 0.75);
}

.ts-kpi-note {
  background: rgba(13, 110, 253, 0.06);
  border: 1px solid rgba(13, 110, 253, 0.10);
  border-radius: 12px;
  padding: 10px 12px;
}

.ts-mini-help {
  font-size: 11.5px;
  color: rgba(15, 23, 42, 0.72);
  margin-top: 6px;
  line-height: 1.25;
}

.ts-mini-help strong {
  color: rgba(15, 23, 42, 0.92);
}

.ts-balance-summary {
  background: rgba(220, 53, 69, 0.06);
  border: 1px solid rgba(220, 53, 69, 0.12);
  border-radius: 12px;
  padding: 10px 12px;
}

/* ============================
   Pills (HC Status)
   ============================ */
.ts-pill {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-weight: 900;
  font-size: 11px;
  line-height: 1.1;
  letter-spacing: 0.3px;
  border: 1px solid transparent;
  white-space: nowrap;
}

.ts-pill-ok {
  background: rgba(25, 135, 84, 0.10);
  color: #146c43;
  border-color: rgba(25, 135, 84, 0.18);
}

.ts-pill-warn {
  background: rgba(255, 193, 7, 0.16);
  color: #a06a00;
  border-color: rgba(255, 193, 7, 0.28);
}

.ts-pill-info {
  background: rgba(13, 110, 253, 0.10);
  color: #0b5ed7;
  border-color: rgba(13, 110, 253, 0.20);
}

/* ============================
   Subtle help icon (i)
   ============================ */
.ts-label-row {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.ts-help-icon {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;

  border: 1px solid rgba(15, 23, 42, 0.16);
  background: rgba(15, 23, 42, 0.04);
  color: rgba(15, 23, 42, 0.65);

  font-size: 11px;
  font-weight: 900;
  line-height: 1;
  padding: 0;
  cursor: pointer;

  transition: background 120ms ease, border-color 120ms ease, color 120ms ease, transform 120ms ease;
}

.ts-help-icon:hover {
  background: rgba(15, 23, 42, 0.07);
  border-color: rgba(15, 23, 42, 0.22);
  color: rgba(15, 23, 42, 0.85);
}

.ts-help-icon:active {
  transform: scale(0.96);
}

.ts-help-icon:focus-visible {
  outline: none;
  box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.12);
}

@media (max-width: 768px) {
  .ts-docfit-wrapper {
    overflow: hidden;
  }

  .ts-table-responsive {
    overflow: visible !important;
  }
}
