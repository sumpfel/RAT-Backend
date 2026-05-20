<div align="center">

<img src="doc/assets/logo.png" alt="RAT logo" width="180">

# RAT-Backend

### **R**emote **A**ccess **T**opology

*Map your network. Manage your devices. All from one burrow.*

<br>

![Status](https://img.shields.io/badge/status-in_development-c97a4a?style=for-the-badge&labelColor=3b2418)
![Course](https://img.shields.io/badge/course-DBI-5a3a28?style=for-the-badge&labelColor=3b2418)
![Year](https://img.shields.io/badge/2025--2026-school_project-8a5a3c?style=for-the-badge&labelColor=3b2418)

<br>

[**Documentation**](doc/markdown/) &nbsp;•&nbsp; [**Database Sketches**](doc/markdown/Database_Sketches.md) &nbsp;•&nbsp; [**Theme**](doc/markdown/style/)

</div>

---

## 🐀 About

**RAT-Backend** is the server side of a network-topology management platform.
Users build a model of their own network — its devices, connections, and
hierarchies — and store the credentials (SSH logins, configs, secrets) needed
to actually administer those devices. The backend then lets them push
configuration changes to their devices through a single, controlled interface.

A companion **frontend** lives in a separate repository *(link coming soon)*.

> **Note:** This is a school project for the **DBI** (Databases) course, 2025–2026.
> It's also a real working application — the database design is graded, but
> the system is built to be used.

---

## ✨ Features

- 🌐 **Network topology modeling** — define your own devices, links, and groups
- 👥 **Users & privileges** — role-based access control over who can see and change what
- 🔐 **Credential vault** — store SSH logins and connection details securely
- ⚙️ **Remote configuration** — push config changes to your devices from one place
- 🗂️ **Audit-friendly schema** — normalized DB design (1NF → 3NF) with full ERM/RM diagrams

---

## 🗺️ Project structure

```
RAT-Backend/
├── doc/
│   ├── assets/              # Logo & images
│   │   ├── logo.png
│   │   └── images/
│   │       ├── sketches/    # ERM, RM, normalization diagrams
│   │       └── screenshots/
│   └── markdown/
│       ├── Database_Sketches.md
│       └── style/           # "rats" markdown theme (CSS + template)
│           ├── rats.css
│           └── template.md
├── src/                     # Backend source (in development)
└── README.md
```

---

## 🧬 Database design

The full database design — normalization steps, ERM, and RM diagrams — is
documented in **[Database_Sketches.md](doc/markdown/Database_Sketches.md)**.

| Stage          | What it shows                          |
| -------------- | -------------------------------------- |
| 1st Normal Form | Atomic attributes                      |
| 2nd Normal Form | Full functional dependency on the key  |
| 3rd Normal Form | No transitive dependencies             |
| ERM            | Entity-Relationship model              |
| RM             | Relational model (tables & FKs)        |

---

## 🎨 Documentation theme

The docs in `doc/markdown/` use a custom **rats** markdown theme — brown fur
tones, parchment background, and the project logo as a header & watermark.

- Stylesheet: [`doc/markdown/style/rats.css`](doc/markdown/style/rats.css)
- Sample document: [`doc/markdown/style/template.md`](doc/markdown/style/template.md)

To apply it to any markdown file in `doc/markdown/`, add this at the top:

```html
<link rel="stylesheet" href="style/rats.css">
```

The theme renders in VSCode's Markdown Preview, browsers, and `pandoc --css`.
GitHub strips custom CSS, so the styled version is best viewed locally.

---

## 🚧 Status

The project is in active development. Current focus:

- [x] Database design (1NF, 2NF, 3NF, ERM, RM)
- [x] Documentation theme & structure
- [ ] Backend implementation (`src/`)
- [ ] Frontend integration *(separate repo)*
- [ ] Deployment

---

## 🔗 Related repositories

- **RAT-Frontend** — *link to be added*

---

<div align="center">
  <br>
  <img src="doc/assets/logo.png" alt="" width="60">
  <br>
  <sub><b>RAT-Backend</b> · DBI 2025–2026 · school + real project</sub>
</div>
