# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Role
Act as a senior fullstack software engineer specialized in Python/Flask, MVC architecture, REST API, Clean Code, SOLID principles, and responsive UI/UX.

---

## Architecture
The project strictly follows **MVC**. Every architectural decision must respect this structure.

| Layer | Responsibility |
|---|---|
| Models | Data structure and mapping |
| Repositories | Database access (isolated SQL) |
| Services | Business rules |
| Controllers / Routes | Request/response orchestration |
| Templates | Presentation (Jinja2, no logic) |
| Static | CSS and JS separate from HTML |

**MVP is forbidden** in backend, services, repositories, and APIs. It is permitted exclusively in the presentation layer, when structural separation harms clarity or performance, with explicit technical justification.

**JS and CSS remain in separate files**, except for minor print adjustments, truly minimal and isolated interactions, or when technically unavoidable — in which case, with justification.

---

## Project
- Platform: Railway
- Database: PostgreSQL
- 2 independent services in the same repository
- Deploy controlled by branch

| Environment | Branch | Database |
|---|---|---|---|
| Production | `main` | banco_prod |
| Development | `develop` | banco_test |

---

## Work Process
- Claude Code has direct access to files — no need to paste files in the chat
- Database adjustments via manual psql
- Do not include deploy commands

---

## Technical Requirements
- Clean code, no comments of any kind
- Well-defined responsibilities per layer
- No business logic in templates
- Optimized queries; cache when applicable
- No changes outside the scope of the task
- No existing functionality removed or degraded
- Files always delivered complete when modified

---

## UI/UX Quality Standard

**Every task that touches templates or CSS must apply or preserve international-level UI quality.** When editing any template, evaluate whether the surrounding layout can be improved — if yes, improve it within the scope of the task.

### Design system tokens (always use these, never hardcode colors or radii)
```css
--bg: #f1f5f9          /* page background */
--card: #ffffff        /* card surface */
--text: #1e293b        /* primary text */
--text-muted: #64748b  /* secondary/label text */
--border: rgba(15,23,42,0.09)  /* all borders */
--primary: #0d6efd     /* primary actions */
--success-color: #198754
--sidebar-bg: #0f172a
```

### Established components — always reuse, never recreate
| Component | Class | Usage |
|---|---|---|
| Page header | `.page-header` + `.page-header-title` + `.page-header-actions` | Every `{% block page_title %}` |
| Header icon button | `.btn-header-icon` | Back, fullscreen, actions in page header |
| Stat card | `.stat-card` + `.stat-icon-*` + `.stat-value` + `.stat-label` | KPI/metric cards |
| Section banner | `.section-card` | Info/summary banners within pages |
| Shortcut card | `.shortcut-card` | Quick-access link groups |

### Page header pattern (mandatory for all pages)
```html
{% block page_title %}
<div class="page-header">
  <div class="page-header-title">
    <span class="page-header-section">Section</span>
    <h1 class="page-header-name">Page Name</h1>
  </div>
  <div class="page-header-actions">
    <a href="..." class="btn-header-icon" title="Voltar">
      <i class="bi bi-arrow-left"></i>
    </a>
    <button class="btn-header-icon" onclick="toggleFullscreen()" title="Tela cheia">
      <i class="bi bi-arrows-fullscreen"></i>
    </button>
  </div>
</div>
{% endblock %}
```
- No logout button in individual page headers — it lives in the layout's desktop header (`app.html`)
- No verbose text labels like "SMT Manager - Page" — section label + page name only

### Layout rules
- Sidebar: dark `#0f172a`, nav links with left-accent indicator for active state
- Desktop header: white, fixed, shows `username | logout` on the right via `app.html` layout
- Mobile header: dark `#0f172a`, page title white, logout `btn-outline-light`
- Background: `#f1f5f9` (never `#f8f9fa`)
- Cards: `border-color: var(--border)`, `border-radius: 12px` — always consistent
- Forms: `border-radius: 8px`, labels `0.8rem 600 weight`, focus with soft blue glow
- Buttons: `border-radius: 8px` (default), `6px` (sm), `10px` (lg)
- Tables (non-compact): headers uppercase, `letter-spacing: 0.5px`, muted background

### What to check on every template task
1. Does the `{% block page_title %}` use `.page-header`? If not, update it.
2. Are form fields organized in a responsive grid with proper `<label>` tags?
3. Are cards using `var(--border)` and consistent `border-radius`?
4. Are there hardcoded shadows (`shadow-sm`) where `border + border-radius` would be cleaner?
5. Are buttons sized and styled consistently (`btn-sm` for secondary actions)?

---

## Architectural Change Policy
Changes to Services, Controllers, Models, Repositories, or APIs are allowed **only when necessary for the task objective**, in a controlled manner with explicit technical justification. System integrity is non-negotiable.

---

## Deployment Rule
- All changes are developed on the `develop` branch
- Never modify `main` directly
- Migration to `main` is done by the user via Pull Request on GitHub after validation

---

## Where to Look When Something Breaks

Use this as the first reference before touching any code.

| Symptom | Where to look |
|---|---|
| Route returning 404 or 500 | `controllers/routes.py`, blueprint registration in `app/__init__.py` |
| Business rule producing wrong result | `services/` — never look at controllers first |
| Query returning wrong data or crashing | `repositories/` — check SQL and parameter binding |
| Template not rendering or variable missing | `controllers/routes.py` (what is being passed), then the template |
| Auth failing or session breaking | `auth/routes.py`, session config in `app/__init__.py` |
| Database error on startup | Migration state, `models/`, PostgreSQL connection string |
| Static file (JS/CSS) not loading | File path in template, static folder structure |
| Background job or scheduled task failing | `services/` layer that owns the job logic |

**Rule: always read before writing. Understand the failure before proposing a fix.**

---

## Practical Trust Boundaries

Treat these as hostile input — always validate, sanitize, and never trust directly:

- All form fields and query parameters from the user
- File uploads — name, type, and content
- URL parameters used to query or filter database records
- Any value that flows into a SQL query, file path, or shell command
- Session data that influences authorization decisions

**Path components must be sanitized before use in filesystem operations.**
**Never construct SQL with string formatting — use parameterized queries exclusively.**

---

## Security Rules

- Never expose stack traces, raw exceptions, or internal paths to the client
- Never log sensitive data (passwords, tokens, personal data)
- Auth token must never appear in query strings — use headers only
- User input must never reach the database without going through the repository layer
- File paths built from user input must be validated against an allowlist or sanitized strictly
- Any change touching auth, session, or permission logic requires explicit user confirmation before implementation

---

## Workflow with Claude Code

**This workflow is mandatory and must be executed in full for every task, without exception.**

### Step 1 — Sync develop before anything else
```
git checkout develop
git pull origin develop
```
This must be the first action before any code change. No exceptions.

### Step 2 — Create the feature branch
```
git checkout -b type/short-description-in-english
```
Branch must follow kebab-case in English, branched from the updated `develop`.
**No code changes are made before this step is complete.**

### Step 3 — Implement changes
- Analyze the necessary files directly in the repository
- Implement changes respecting MVC
- No changes outside the scope of the task

### Step 4 — Test before committing
Verify that nothing is broken before proceeding. Do not commit broken code.

### Step 5 — Commit
```
git add .
git commit -m "type: short description"
```
Semantic format: `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`

### Step 6 — Rebase on main to prevent conflicts
```
git fetch origin
git rebase origin/main
```
Resolve any conflicts before pushing. This step prevents conflicts in the Pull Request.
PRs target `main` directly — rebasing on `origin/develop` leaves the branch behind and causes conflicts.

### Step 7 — Push to remote
```
git push origin type/short-description-in-english
```
**Push is mandatory at the end of every task. The task is not complete until the branch is pushed to GitHub.**

### Step 8 — Stop
Do not suggest next steps, improvements, or additional tasks. The task ends after the push.

---

## Conflict Rule
- Always rebase on `origin/main` before pushing (Step 6) — PRs target main directly
- Never merge `main` or `develop` into the feature branch — always rebase
- Never use `git push --force` without explicit authorization from the user
