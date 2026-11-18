# RBAC in Practice: Protecting Tasks from IDOR

This project retrofits role-based access control (RBAC) onto a multi-user task
manager and demonstrates the same task access in two modes: a vulnerable,
login-only baseline and a hardened RBAC implementation. It is a small
educational demonstration, not a production-ready task service.

## Approved project proposal

- **System:** a multi-user task management web app. Each task has an owner; users
  can create, view, edit, and delete tasks.
- **Threat:** an authenticated standard user changes or guesses a numeric task
  ID and accesses another user's task (an insecure direct object reference,
  or IDOR). The attacker can issue ordinary HTTP requests but cannot bypass
  authentication, access the database, or compromise the server.
- **Primary mechanism:** RBAC, with `user` and `admin` roles and explicit
  permissions. Standard users can operate on their own tasks; admins can
  operate on all tasks.
- **Broken state:** the baseline requires login but intentionally omits
  authorization. A standard user can read or change another user's task by
  requesting its ID. The demo makes this failure reproducible and compares it
  with the hardened state.

## Security design

| Principal | Permissions in hardened mode |
|---|---|
| Anonymous visitor | No task access |
| `user` | Create tasks and list, read, update, or delete own tasks |
| `admin` | Create tasks, manage all tasks, and open the admin task list |

`todor/authz.py` defines the permission map and checks task ownership on the
server for each read, update, and delete. The task list is also scoped by owner.
The authentication/session layer identifies the principal; it is not a
substitute for authorization. Unknown roles have no permissions. The role is
assigned by the server, not by the registration form. The protected task routes
explicitly invoke the policy helpers; a future protected route must do the same
to remain covered.

The vulnerable baseline is intentionally kept small: it uses the same
authenticated accounts and tasks but bypasses permission and ownership checks.
It is restricted to loopback addresses and should never be exposed to a network.

## Version branches

The public repository keeps the two versions on separate branches:

- `hardened` defaults to RBAC (`AUTHZ_MODE='rbac'`).
- `baseline` defaults to the intentionally vulnerable login-only mode
  (`AUTHZ_MODE='baseline'`).

Both use the same local-only guard when baseline mode is enabled. The
`hardened` branch also includes the baseline launcher for side-by-side testing.
For a version-specific checkout, use
`git clone --branch hardened https://github.com/kgajula1-stack/ITIS3200.git`
or replace `hardened` with `baseline`. If comparing separate working
directories, seed each with the same four suffixes so account and task IDs
match; never put the suffixes in Git.

## Run locally (Windows)

From this directory, create and activate a virtual environment and install the
listed dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Seed synthetic accounts and tasks. The script asks for the four group members'
last-two-digit suffixes using hidden input, derives the required
`(sum of suffixes) mod 11` seed, and does not store or print the suffixes.
The resulting usernames, task IDs, and shared demo password are printed:

```powershell
python seed_demo.py
```

Use the printed account details to demonstrate the selected branch. On the
`hardened` branch, start the hardened server:

```powershell
python run_demo.py
```

For the local vulnerable comparison on the `hardened` branch, use another
terminal:

```powershell
python run_baseline.py
```

On the `baseline` branch, `python run_demo.py` starts the baseline on
`http://127.0.0.1:5000`. The explicit baseline launcher uses port 5001. Both
servers bind only to `127.0.0.1`, and the baseline independently rejects
non-loopback requests.

## Reproduce the success and failure cases

1. **Failure (baseline):** open port 5001 and sign in as User A. Open
   `/todo/update/<User-B-task-ID>` using the ID printed by the seeder. The page
   displays User B's task; submit an edit and verify that it changes. This is
   cross-owner read and write through a direct object reference.
2. **Protected case (hardened):** sign in as User A on port 5000 and request the
   same User B task ID. The server responds `403 Forbidden`, and the task
   remains unchanged. User A can still view and update User A's own task.
3. **Role distinction:** sign in as the admin in hardened mode. The admin task
   list contains both users' tasks, and the admin can manage either one. A
   standard user receives `403 Forbidden` from `/todo/admin/tasks`.
4. **TA-selected request:** while signed in as User A in hardened mode, try a
   `GET /todo/update/<id>`, `POST /todo/update/<id>`, or
   `POST /todo/delete/<id>` for another existing task. The attempt must be
   denied and the task must remain unchanged. An ID that does not exist returns
   `404`; an owned task remains accessible to its owner.

The demo returns `403` for a known task that exists but belongs to another
user. This makes the authorization decision visible in class; a production
system may choose a uniform `404` to avoid revealing whether a forbidden task
ID exists.

The dedicated demo database is created under Flask's `instance/` directory.
The demo credentials are intentionally simple and must only be used locally.
To start over, stop both servers and remove only
`instance/courseproject_demo.db` (and its SQLite journal files, if present),
then run the seeder again. Do not put real user data in this database.

## Tests

From the project directory:

```powershell
python -m unittest discover -s tests -v
```

The tests cover cross-owner access in baseline and denial/data preservation in
RBAC mode; owner access; admin permissions; anonymous access; unknown-role
default denial; role assignment during registration; the loopback guard; and
the four-member seed formula and validation.

## Course deliverables

`docs/` contains the refined one-page proposal (DOCX/PDF), the approximately
five-page final report (DOCX/PDF, excluding references and AI appendix), a
10-minute presentation deck with speaker notes, and an individual reflection
template. Regenerate the documents and deck from the project directory with:

```powershell
python -m pip install -r docs\document-requirements.txt
python docs\build_deliverables.py
```

The source repository is
<https://github.com/kgajula1-stack/ITIS3200>. The version paths are
<https://github.com/kgajula1-stack/ITIS3200/tree/hardened/courseproject> and
<https://github.com/kgajula1-stack/ITIS3200/tree/baseline/courseproject>.
Publish both branches before submitting those links.
The approved proposal lists three group members, while the seed rule specifies
four; the group must confirm the complete roster and privately provide all four
suffixes before the live demo. Individual reflection forms must be completed
separately by each student with their own contributions and evaluations.

## Repository map

- `todor/authz.py` — role permissions and task ownership authorization
- `todor/todo.py` — task routes and role-aware task listing
- `todor/models.py` — users, roles, tasks, and ownership relationship
- `run_demo.py` / `run_baseline.py` — hardened and local-only vulnerable modes
- `seed_demo.py` — deterministic synthetic demo data
- `tests/` — focused automated regression and authorization tests
- `docs/` — proposal, final report, presentation, AI disclosure, and reflection template

## Limitations

The project focuses on the course threat model and does not implement CSRF
protection, rate limiting, production secrets management, or a full deployment
hardening process. The local baseline is deliberately vulnerable for
demonstration; it is not an alternate production configuration.
