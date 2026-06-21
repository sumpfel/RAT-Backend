<div align="center">

<img src="doc/assets/logo.png" alt="RAT logo" width="180">

# RAT-Backend

### **R**emote **A**ccess **T**opology

*Map your network. Manage your devices. All from one burrow.*

<br>

![Status](https://img.shields.io/badge/status-working-3f7d3f?style=for-the-badge&labelColor=3b2418)
![Course](https://img.shields.io/badge/course-DBI-5a3a28?style=for-the-badge&labelColor=3b2418)
![Year](https://img.shields.io/badge/2025--2026-school_project-8a5a3c?style=for-the-badge&labelColor=3b2418)
![API](https://img.shields.io/badge/FastAPI-REST-c97a4a?style=for-the-badge&labelColor=3b2418)

<br>

[**Bedienungsanleitung**](doc/markdown/Bedienungsanleitung.md) &nbsp;•&nbsp;
[**Datenbank-Design**](doc/markdown/Database_Sketches.md) &nbsp;•&nbsp;
[**Projekttagebuch**](doc/markdown/Projekttagebuch.md) &nbsp;•&nbsp;
[**Doku**](doc/markdown/)

</div>

---

## 🐀 About

**RAT-Backend** is the server side of a network-topology management platform.
Users build a model of their own network — its devices, connections and
hierarchies — and store the credentials (SSH/Telnet/FTP logins, SNMP settings)
needed to administer those devices. A role-based permission system controls who
may see and change what; a companion **C# desktop frontend**
([RAT-Client](https://github.com/sumpfel/RAT-Client)) talks to this API over HTTP.

> School project for the **DBI** (Databases) course, 2025–2026 — and a real,
> working application. The normalized database design (1NF → 3NF, ERM, RM) is part
> of the grade, see **[Datenbank-Design](doc/markdown/Database_Sketches.md)**.

---

## ⚡ Quick start

The fastest way to get running on **Windows** — clone, set host/port and start in one line:

```bat
git clone https://github.com/sumpfel/RAT-Backend.git && cd RAT-Backend && set HOST=0.0.0.0 && set PORT=8080 && run.bat
```

**Linux / macOS:**
```bash
git clone https://github.com/sumpfel/RAT-Backend.git && cd RAT-Backend && ./run.sh
```

The run scripts create a virtual environment (`.venv`), install
`src/requirements.txt` and start the FastAPI server. Then open:

- **API:** http://127.0.0.1:8000 &nbsp;(or your chosen host/port)
- **Swagger UI:** http://127.0.0.1:8000/docs
- **Logs:** console **and** `src/api.log`

> Requires **Python 3** on PATH. The first run installs dependencies and may take a minute.
> A fresh database auto-creates an admin account **`admin` / `admin`** — change the
> password after the first login.

| Script | Platform | Run it |
|--------|----------|--------|
| [`run.bat`](run.bat) | Windows (cmd / double-click) | `run.bat` |
| [`run.ps1`](run.ps1) | Windows (PowerShell) | `powershell -ExecutionPolicy Bypass -File run.ps1` |
| [`run.sh`](run.sh) | Linux / macOS | `./run.sh` |

Host/port are configurable without editing code (`HOST` / `PORT` env vars, or
`-BindHost` / `-Port` for `run.ps1`); `RELOAD=1` / `-Reload` enables auto-reload.

Full usage with example `curl` requests: **[Bedienungsanleitung.md](doc/markdown/Bedienungsanleitung.md)**.

---

## ✨ Features

- 🌐 **Network topology modeling** — devices, interfaces and connections (cables)
- 👥 **Users & privileges** — per-object roles: Hidden / See / Edit / Admin / Owner
- 🔐 **Credential vault** — per-user SSH/Telnet/FTP logins and SNMP settings per device
- 🔎 **Filtering, sorting & pagination** — query params (`name`, `type`, `sort_by`, `limit`, `offset`, …)
- 📊 **Statistics & aggregation** — `GROUP BY` + `COUNT` / `SUM` / `AVG` endpoints
- 🪵 **Logging** — every request (INFO) and error (ERROR) to console **and** `api.log`
- ☁️ **Cloud-DB ready** — point at Postgres/MySQL via `DATABASE_URL` (SQLite by default)
- 🗂️ **Normalized schema** — 1NF → 3NF with full ERM/RM diagrams

---

## 🔌 API overview

All endpoints (except login/register) require a JWT: `Authorization: Bearer <token>`.

| Method & path | Purpose |
|---|---|
| `POST /user/login` | get a JWT (OAuth2 form login) |
| `POST /user/register` · `GET /user/` · `GET /user/me` | create / list / current user |
| `PUT /user/{id}` · `DELETE /user/{id}` | edit / delete user (admin rules apply) |
| `GET/POST/PUT/DELETE /networkObject/` | devices (CRUD, filter/sort/paginate) |
| `GET/POST/PUT/DELETE /networkObjectInterface/` | device interfaces |
| `GET/POST/PUT/DELETE /networkObjectConnection/` | connections (cables) |
| `GET/POST/PUT/DELETE /networkObjectPermission/` | per-object access control |
| `GET/POST/PUT/DELETE /login/` · `/snmpSettings/` | per-device logins / SNMP |
| `GET /user/settings/` · `PUT /user/settings/` | per-user UI settings |
| `GET /statistics/summary` · `/objects-by-type` · `/connections-by-type` · `/interfaces-per-object` | aggregation / stats |

**Status codes:** `200` ok · `201` created · `400` validation · `401` auth ·
`403` forbidden · `404` not found · `409` conflict.

---

## 🗺️ Project structure

```
RAT-Backend/
├── run.sh / run.bat / run.ps1   # launchers (create .venv, install, start server)
├── doc/
│   ├── assets/                  # logo, sketches, DrawIO diagrams
│   │   └── drawio/DB_Sketches_v2.drawio   # editable ERM / RM diagram
│   ├── markdown/
│   │   ├── Bedienungsanleitung.md   # usage + example requests
│   │   ├── Database_Sketches.md     # normalization, ERM, RM
│   │   ├── Projekttagebuch.md       # project diary (who/when/what)
│   │   ├── Project_Planning.md
│   │   ├── AI_usage.md              # documented AI usage
│   │   └── style/                   # "rats" markdown theme (CSS + template)
│   └── pdf/                     # PDF exports of the docs
└── src/
    ├── main.py                  # FastAPI app, logging, router registration
    ├── database.py              # engine (DATABASE_URL / .env), session
    ├── models.py                # SQLAlchemy models (the schema)
    ├── auth.py                  # JWT + password hashing
    ├── permissions.py           # per-object permission helpers
    ├── requirements.txt
    └── routers/                 # one module per resource (+ statistics.py)
```

---

## 🧬 Database design

Normalization steps (1NF → 3NF), the ERM and the RM (with PK underlined / FK
italic) are documented in **[Database_Sketches.md](doc/markdown/Database_Sketches.md)**;
the editable diagram is
[`doc/assets/drawio/DB_Sketches_v2.drawio`](doc/assets/drawio/DB_Sketches_v2.drawio).

| Stage | What it shows |
| --- | --- |
| 1NF | atomic attributes |
| 2NF | full functional dependency on the key |
| 3NF | no transitive dependencies |
| ERM | entity-relationship model |
| RM | relational model (tables & FKs) |

---

## 🔗 Related repositories

- **[RAT-Client](https://github.com/sumpfel/RAT-Client)** — C# desktop frontend (WPF)

---

<div align="center">
  <br>
  <img src="doc/assets/logo.png" alt="" width="60">
  <br>
  <sub><b>RAT-Backend</b> · DBI 2025–2026 · school + real project</sub>
</div>
