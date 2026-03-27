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
|---|---|---|
| Production | `main` | banco_prod |
| Development | `develop` | banco_test |

---

## Work Process
- Claude Code has direct access to files — no need to paste files in the chat
- Database adjustments via manual psql
- Do not include deploy commands

---

## Technical Requirements
- Clean code. Avoid comments; code should be self-explanatory.
- Inline comments are forbidden unless strictly necessary.
- Well-defined responsibilities per layer
- No business logic in templates
- Optimized queries; cache when applicable
- No changes outside the scope of the task, except when required to restore compliance with the rules defined in CLAUDE.md.
- No existing functionality removed or degraded
- Files always delivered complete when modified

---

## CLAUDE.md Compliance Authority

This document is the **authoritative engineering standard** for this repository.

Claude Code must treat the rules defined in this file as **mandatory architectural and engineering constraints**.

### Compliance Review

Before implementing any task, Claude Code must:

1. Read the relevant parts of the existing codebase.
2. Evaluate whether the current implementation complies with the rules defined in this document.
3. Identify structural violations of:
   - MVC architecture
   - Layer responsibilities
   - Security rules
   - Password policy
   - UI/UX design system
   - Repository / service separation
   - Clean code and SOLID principles

### Authorized Refactoring for Compliance

If the existing implementation **does not comply with the rules defined in this document**, Claude Code is **explicitly authorized to refactor the code** in order to restore compliance.

This may include:

- Moving business logic from controllers to services
- Moving SQL out of controllers into repositories
- Removing logic from templates
- Standardizing UI components
- Applying password policy enforcement
- Fixing violations of security rules
- Aligning code with MVC responsibilities

These refactors are considered **compliance corrections**, not scope expansion.

### Safety Constraints

When performing compliance refactoring:

- Existing functionality **must not be removed**
- System behavior **must remain equivalent**
- Changes must remain **minimal and controlled**
- Refactoring must **only target rule violations defined in this document**

### Guiding Principle

If a conflict exists between:

- existing code
- and the rules defined in `CLAUDE.md`

**The rules in `CLAUDE.md` always take precedence.**

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

## UI Layout Design System

This system uses a **fixed sidebar + fixed header + mobile bottom navigation** layout pattern. Every page must implement this structure. If any part of the project does not follow this pattern, Claude Code must refactor it to comply.

### Layout Structure

**Desktop (≥768px):**
- Fixed dark sidebar (`240px` wide, full height, `--sidebar-bg: #0f172a`)
- Fixed white top header (`56px`)
- Main content with `margin-left: 240px` and `padding-top: calc(56px + 24px)`

**Mobile (<768px):**
- Fixed dark top header (`56px`) with logo avatar, page title, username, and logout button (`btn-outline-light`)
- Sidebar hidden (`d-none d-md-flex`)
- Fixed bottom navigation bar (`64px`) with 5 primary shortcuts
- Main content padded between header and bottom nav: `padding-bottom: calc(64px + 16px)`

### CSS Tokens (complete set — always define in `:root`, never hardcode)

```css
:root {
  --sidebar-width: 240px;
  --header-height: 56px;
  --bottom-nav-height: 64px;

  --bg: #f1f5f9;
  --card: #ffffff;
  --text: #1e293b;
  --text-muted: #64748b;
  --border: rgba(15, 23, 42, 0.09);
  --primary: #0d6efd;
  --success-color: #198754;

  --sidebar-bg: #0f172a;
  --sidebar-border: rgba(255, 255, 255, 0.07);
  --sidebar-text: rgba(255, 255, 255, 0.55);
  --sidebar-text-hover: rgba(255, 255, 255, 0.90);
  --sidebar-text-active: #ffffff;
  --sidebar-hover-bg: rgba(255, 255, 255, 0.07);
  --sidebar-active-bg: rgba(59, 130, 246, 0.16);
  --sidebar-active-accent: #3b82f6;
}
```

### Sidebar Rules

- Background: `--sidebar-bg` (`#0f172a`)
- Nav items organized in **collapsible groups** (Bootstrap collapse plugin)
- Each group: toggle button with icon, label, and chevron rotating 180° when expanded
- Active item: **3px left accent bar** (`#3b82f6`), blue-tinted background (`rgba(59,130,246,0.16)`), white text, `fw-600`
- Hover: `rgba(255,255,255,0.07)` background, text brightens to `rgba(255,255,255,0.90)`
- All transitions: `0.12s ease`
- Logo area at the top with border separator below
- Footer area at the bottom for admin-only links
- Sidebar content is scrollable

### Typography

Font stack: `Inter, system-ui, -apple-system, "Segoe UI", Roboto, Arial`

| Element | Size | Weight |
|---|---|---|
| Page header name | 1.05rem | 700 |
| Page header section label | 0.65rem, uppercase, letter-spacing 1px | 700 |
| Card title | 0.875–1.05rem | 600–700 |
| Body text | 0.875rem | 500 |
| Form labels | 0.8rem | 600 |
| Table headers | 0.72rem, uppercase, letter-spacing 0.5px | 700 |
| Muted/secondary | 0.8rem | 500, `--text-muted` |

### Card Rules

| Component | Border Radius | Notes |
|---|---|---|
| `.card` | 12px | General content |
| `.stat-card` | 14px | KPI/metrics, hover shadow `0 4px 16px rgba(15,23,42,0.08)` |
| `.shortcut-card` | 14px | Quick-access groups |
| `.section-card` | 12px | Info/summary banners |

All cards: `border: 1px solid var(--border)`, `background: var(--card)`. No static `box-shadow` — hover-only via transition.

Stat card icon: 40×40px, `border-radius: 10px`, color-coded backgrounds:
- Blue: `rgba(13, 110, 253, 0.10)`
- Green: `rgba(25, 135, 84, 0.10)`
- Slate: `rgba(15, 23, 42, 0.07)`

### Form Rules

- Input `border-radius: 8px`
- Focus: blue border + soft glow (`box-shadow: 0 0 0 3px rgba(13,110,253,0.12)`)
- Labels: `0.8rem`, `fw-600`, color `--text`

### Table Rules

- Headers: `0.72rem`, uppercase, `letter-spacing: 0.5px`, `fw-700`, muted tinted background
- Body rows: `0.875rem`, padding `10px`
- Borders: `var(--border)`

### Fullscreen Mode

Every page must include a fullscreen toggle button in `.page-header-actions`.

`main.js` must contain:

```javascript
function toggleFullscreen() {
  const active = document.body.classList.toggle("fullscreen-mode");
  localStorage.setItem("fullscreen", active ? "1" : "");
}

document.addEventListener("DOMContentLoaded", () => {
  if (localStorage.getItem("fullscreen") === "1") {
    document.body.classList.add("fullscreen-mode");
  }
});
```

CSS:

```css
body.fullscreen-mode .sidebar { display: none !important; }
body.fullscreen-mode .main { margin-left: 0 !important; }
body.fullscreen-mode .desktop-header { left: 0 !important; }
```

### Layout Compliance Rule

If a project does not implement this layout pattern, Claude Code is **explicitly authorized to refactor** templates, CSS, and JS to restore compliance. This includes:

- Adding the sidebar with collapsible groups and active left accent
- Adding the mobile header and bottom navigation
- Implementing the `page-header` pattern on all pages
- Adding all tokens to `:root`
- Adding `toggleFullscreen()` and the fullscreen button to all page headers
- Replacing hardcoded colors with CSS variables

Existing functionality must not be removed during this refactoring.

---

## Architectural Change Policy
Changes to Services, Controllers, Models, Repositories, or APIs are allowed when necessary for the task objective or to restore compliance with CLAUDE.md rules, in a controlled manner with explicit technical justification. System integrity is non-negotiable.

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

Abaixo está um **arquivo completo pronto para adicionar ao seu `CLAUDE.md`**, focado exatamente no que você quer:

* backup **seguro**
* **não alterar nada no banco**
* evitar **todos os erros comuns**
* garantir **restauração confiável**
* manter **simplicidade operacional**

O texto é **normativo**, no mesmo estilo do seu CLAUDE.md.

---

# Database Backup & Disaster Recovery Policy

The system must implement a **safe, read-only, and reliable database backup mechanism** to guarantee that all data can be recovered in case of operational failure.

Backups must **never modify the database** and must operate strictly in **read-only mode**.

The database currently runs on **PostgreSQL hosted on Railway**.

Primary backup tool:

* `pg_dump`

Backup generation must always use PostgreSQL native tools to guarantee compatibility with restoration procedures.

---

# Fundamental Principle

Database backups must **never change the state of the database**.

Backup operations must always be **read-only operations**.

Tools such as `pg_dump` operate by performing internal `SELECT` queries to export database structure and data.

Therefore:

```id="backup_readonly_principle"
Backup operations must not execute INSERT, UPDATE, DELETE, ALTER, or DROP statements.
```

The backup process must only **extract database information** and write it to a file.

---

# PostgreSQL Connection

Backups must support PostgreSQL connection URLs.

Example connection string:

```id="postgres_connection_example"
postgresql://user:password@host:port/database
```

Example Railway connection:

```id="railway_connection_example"
postgresql://postgres:*****@caboose.proxy.rlwy.net:11094/railway
```

Backup commands must internally use this connection string.

Example concept:

```id="pg_dump_command_example"
pg_dump DATABASE_URL
```

---

# Backup Architecture (MVC Responsibility)

Backup infrastructure must follow the MVC architecture defined in this repository.

| Layer        | Responsibility                                        |
| ------------ | ----------------------------------------------------- |
| Controllers  | Admin interface and configuration endpoints           |
| Services     | Backup execution, scheduling, retention, verification |
| Repositories | Persist backup configuration and logs                 |
| Templates    | Admin interface for monitoring and configuration      |

Backup execution logic must **never exist in controllers or templates**.

All backup orchestration must exist in the **service layer**.

---

# Backup Configuration Interface

The system must include an administrative interface allowing configuration of backup execution.

Suggested template location:

```id="backup_template_path"
app/templates/admin/backups.html
```

The interface must allow administrators to configure:

| Field                   | Description                               |
| ----------------------- | ----------------------------------------- |
| Database connection URL | PostgreSQL connection string              |
| Backup frequency        | daily, weekly, monthly, bimonthly, yearly |
| Execution time          | hour and minute                           |
| Retention policy        | number of days backups are preserved      |

Only authorized administrators may configure backup behavior.

---

# Backup Scheduling

The system must support scheduled backup execution.

Supported frequencies:

| Frequency | Description      |
| --------- | ---------------- |
| Daily     | once per day     |
| Weekly    | once per week    |
| Monthly   | once per month   |
| Bimonthly | every two months |
| Yearly    | once per year    |

Scheduling mechanisms may include:

* cron jobs
* background workers
* internal schedulers

Scheduling logic must exist **within the service layer**.

---

# Backup Generation

Backups must be generated using `pg_dump`.

Example conceptual command:

```id="pg_dump_pipeline"
pg_dump DATABASE_URL | gzip > backup.sql.gz
```

Backup files must be **compressed** to reduce storage usage.

File format:

```id="backup_format"
.sql.gz
```

Example filename:

```id="backup_filename_example"
backup_2026-03-13_02-00.sql.gz
```

Timestamped filenames prevent overwriting previous backups.

---

# Backup Storage Structure

Backups must be stored using a structured directory layout.

Suggested structure:

```id="backup_directory_structure"
/backups
    /daily
    /weekly
    /monthly
    /yearly
```

File paths must be **controlled by the application**.

User input must never directly define filesystem paths.

---

# Backup Logging

Every backup execution attempt must be recorded.

Backup logs must contain:

| Field         | Description           |
| ------------- | --------------------- |
| id            | unique identifier     |
| timestamp     | execution time        |
| status        | success or failure    |
| file_path     | backup file location  |
| size          | backup size           |
| duration      | execution duration    |
| checksum      | file integrity hash   |
| error_message | failure reason if any |

Logs must be persisted through the repository layer.

---

# Backup Integrity Verification

Every generated backup must be verified.

Immediately after backup generation, the system must compute a cryptographic checksum.

Recommended algorithm:

```id="checksum_algorithm"
SHA-256
```

Example command:

```id="checksum_command"
sha256sum backup.sql.gz
```

Checksum values must be stored in backup logs.

Integrity verification allows detection of corrupted backup files.

---

# Backup Encryption

Backups must be encrypted before being stored or transferred externally.

Recommended encryption standard:

```id="backup_encryption_standard"
AES-256
```

Example conceptual pipeline:

```id="backup_encryption_pipeline"
pg_dump → gzip → encryption → storage
```

Encryption example concept:

```id="backup_encryption_command"
pg_dump DATABASE_URL | gzip | openssl enc -aes-256-cbc > backup.sql.gz.enc
```

Encryption keys must:

* never be stored in source code
* be stored in environment variables or secret storage
* never appear in logs

---

# Offsite Backup Storage

Backups must never rely exclusively on the same infrastructure that hosts the database.

A secondary **offsite backup location** must exist.

Examples:

* cloud object storage (S3 compatible)
* encrypted remote storage
* internal backup server
* secure file storage system

Backup pipeline:

```id="offsite_backup_pipeline"
backup generation
↓
checksum verification
↓
encryption
↓
offsite transfer
```

Offsite transfer success or failure must be logged.

---

# Backup Verification

Backups must periodically be verified to ensure they are restorable.

Verification methods include:

| Method              | Description                          |
| ------------------- | ------------------------------------ |
| checksum validation | detect corruption                    |
| metadata validation | confirm file size and structure      |
| test restore        | restore backup to temporary database |

At minimum, checksum validation must run automatically.

Backups failing verification must be marked **invalid**.

---

# Backup Retention Policy

Retention policies ensure storage does not grow indefinitely while preserving historical recovery capability.

Default retention rules:

| Backup Type | Retention  |
| ----------- | ---------- |
| Daily       | 30 days    |
| Weekly      | 3 months   |
| Monthly     | 1 year     |
| Yearly      | indefinite |

Retention cleanup must run automatically.

The system must **never delete the most recent valid backup**.

---

# Disaster Recovery Requirement

The system must always maintain the ability to restore the database after catastrophic failure.

Possible failure scenarios:

* accidental deletion
* data corruption
* infrastructure loss
* hosting provider outage
* deployment failures
* security incidents

Disaster recovery requires:

| Requirement               | Description                                   |
| ------------------------- | --------------------------------------------- |
| recent backups            | backups exist within schedule                 |
| offsite storage           | backups stored outside primary infrastructure |
| integrity verification    | checksum validated                            |
| restoration compatibility | restorable using PostgreSQL tools             |

Example restore command:

```id="restore_command_example"
psql DATABASE_URL < backup.sql
```

Compressed restore:

```id="restore_compressed_example"
gunzip -c backup.sql.gz | psql DATABASE_URL
```

---

# Failure Handling

If any step in the backup pipeline fails, the system must:

1. record the failure in backup logs
2. preserve diagnostic information
3. mark the backup as failed
4. allow administrators to review errors

Possible failure scenarios include:

* `pg_dump` execution failure
* disk storage errors
* checksum mismatch
* encryption failure
* offsite transfer failure

Failures must **never interrupt the normal operation of the database**.

---

# Security Requirements

Backup infrastructure must follow strict security practices.

The system must ensure:

* database credentials never appear in logs
* encryption keys are never stored in code
* file paths are sanitized
* shell commands are protected against injection

User-provided values must never be executed directly in shell commands.

---

# Operational Safety Rule

Backup operations must be designed with the assumption that infrastructure failures will occur.

The objective of this system is to guarantee that:

```id="data_recovery_objective"
data can always be restored safely.
```

Backup capability is considered a **core operational responsibility** of the system.

---

# Mandatory Compliance Rule

If automated backup infrastructure does not exist in the system, Claude Code is authorized to:

* design backup services
* implement backup scheduling
* create backup configuration tables
* implement backup logging
* create administrative monitoring interfaces

Backup functionality is considered **mandatory operational infrastructure**, not an optional feature.

---

# Backup Infrastructure Compliance Rule

The backup policy defined in this document is **mandatory operational infrastructure**.

If the current system **does not yet contain a backup mechanism**, Claude Code must treat this as a **compliance gap**.

In this case, Claude Code is explicitly authorized to **design and implement the required backup infrastructure** in order to satisfy the rules defined in this document.

This may include creating or refactoring the following components:

| Component                  | Purpose                                               |
| -------------------------- | ----------------------------------------------------- |
| Backup service             | Execute database backup using `pg_dump`               |
| Backup scheduler           | Run backups according to configured frequency         |
| Backup repository          | Persist configuration and backup logs                 |
| Backup configuration table | Store backup schedule and retention settings          |
| Backup logs table          | Record backup execution results                       |
| Admin backup interface     | Allow administrators to configure and monitor backups |

Suggested interface location:

```
app/templates/admin/backups.html
```

The interface must provide:

* backup configuration
* backup history
* execution status
* file download access
* verification status

If existing code conflicts with the backup policy defined in this document, **the rules in `CLAUDE.md` take precedence** and the code must be refactored to restore compliance.

Backup infrastructure is considered **essential operational safety functionality** and must always exist in production systems.

---

## Password Security Policy

The system enforces a strict password security policy to protect accounts and sensitive data.

### Password Requirements

All user passwords must comply with the following rules:

- Minimum length: **10 characters**
- Must contain:
  - At least **one uppercase letter**
  - At least **one lowercase letter**
  - At least **one number**
  - At least **one special character** (e.g. `@`, `$`, `#`, `!`, `%`, `&`)
- Passwords must **not contain**:
  - The username
  - The company name
  - Obvious variations of either

Passwords composed only of letters or only of numbers are **not allowed**.

---

### Password Strength Target

The system should aim to ensure passwords reach a strength level equivalent to:

**"It would take a computer about 5 years to crack your password"**

Reference guideline used for this strength target:

https://www.security.org/how-secure-is-my-password/

Password validation mechanisms should enforce complexity strong enough to reach this approximate resistance level.

---

### Password Rotation

User passwords must be **changed every 6 months (180 days)**.

Rules:

- The system must **force password change** when the period expires.
- The new password **cannot be identical to the previous password**.
- Minor changes (for example changing a single character) are allowed as long as the password is not exactly the same as the previous one.

---

### Credential Exposure Response

If any data breach or credential leak is suspected or confirmed:

- All affected credentials must be **immediately rotated**.
- Users must be **forced to change passwords on the next login**.
- Any compromised tokens or sessions must be **invalidated**.

---

### Implementation Notes

Password policy enforcement must be implemented at the **service layer**, never inside templates.

Validation responsibilities:

| Layer | Responsibility |
|---|---|
| Controllers | Receive password input and pass to service |
| Services | Validate password policy and rotation rules |
| Repositories | Store hashed passwords only |
| Templates | Never contain validation logic |

Passwords must always be stored using **secure hashing algorithms (bcrypt, argon2, or an equivalent modern adaptive hashing algorithm)**.
Plaintext passwords must never be logged or persisted.

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

   
   
