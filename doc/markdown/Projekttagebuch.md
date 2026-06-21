# Projekttagebuch – RAT-Backend

Laufend geführtes Projekttagebuch (wer / wann / was). Die Einträge sind aus den
git-Commits dieses Repositories abgeleitet und im selben Stil wie das Frontend
geführt (`ADDED` / `FIXED` / `CHANGED` / `DOCS`).

Mitwirkende:

- **Christof** (git: `sumpfel`) – NetworkObject-, NetworkObjectConnection-,
  NetworkObjectPermission-, Login-/SNMP-Logik, Projektplanung
- **Tobias** (git: `Pir4t3141`) – Datenbank/Models, User- und UserSettings-Logik,
  Auth/Token

KI-Markierungen (`KI-N`) verweisen auf die ausführliche Dokumentation in
[AI_usage.md](AI_usage.md).

---

## 2026-05-20

**Christof**
- ADDED: Projektplanung und Datenbankstruktur (ERM, erste Tabellen-Skizzen)
- Initial commit / Repository angelegt

## 2026-05-28

**Tobias**
- ADDED: Basis-Projektstruktur (FastAPI-Grundgerüst)
- ADDED: weitere Models in `models.py`, Namenskonventionen vereinheitlicht
- ADDED: `uvicorn.run()` zum Starten von `main.py`
- ADDED: User-Pydantic-Klassen `UserBase` und `UserCreate`
- FIXED: Models – `notnull:True` → `nullable=False`; fehlenden Primary Key für
  `DBNetworkObjectSnmpCommunity` ergänzt

**Christof**
- ADDED: Models für `User` und `UserSettings`

## 2026-06-10

**Christof**
- ADDED: Router für NetworkObject, NetworkObjectConnection und NetworkObjectConnectionLogin (nO / nOC / nOCL)

**Tobias**
- FIXED: FOREIGN KEYs in den Models zeigten auf die falschen Tabellen
- ADDED: Login per Token (speichert Username und Privilege)

## 2026-06-14

**Tobias**
- UPDATED: `models.py` und mehrere Router überarbeitet
- UPDATED: Security für `user.py`; Grundlagen von `networkObject.py` und
  `networkObjectConnection.py`

**Christof**
- ADDED: UserSettings-Route
- CHANGED: Datenbank-Layout-Zeichnungen aktualisiert

## 2026-06-16

**Christof**
- ADDED: Router mit einfachem Add/Edit/Delete für NetworkObjectInterface,
  NetworkObjectPermission und SNMPSettings
- ADDED: zentrales Berechtigungssystem (Hidden/See/Edit/Admin/Owner) – jeder User
  bekommt nur das für seine Berechtigung Vorgesehene; Default-Admin-User beim
  ersten Start (**KI-1 bis KI-9**)
- ADDED: `GET /user/` (Userliste) und `can_create` in den User-DTOs für den
  C#-Client (**KI-10**)
- FIXED: `network_object_connection_id` eines Interfaces ist jetzt optional
  (vorher Crash der GET-Liste bei nicht verbundenen Interfaces) (**KI-10**)
- FIXED: Löschen eines NetworkObjects löscht nun kaskadierend Interfaces, deren
  Connections sowie Logins/SNMP auf den Permission-Rows (verwaiste Rows hatten den
  Graph-Load im C#-Client zerstört) (**KI-11**)

## 2026-06-17

**Christof**
- ADDED: `PUT /user/{id}` zum Bearbeiten eines Users – globale Admins ändern jedes
  Feld jedes Users, ein normaler User nur eigenen Namen + Passwort
  (`is_admin`/`can_create` werden beim Self-Edit ignoriert, fremde User → 403) (**KI-12**)

**Tobias**
- CHANGED: Token läuft jetzt nach 30 statt 15 Minuten ab
- ADDED: Logging (zunächst in `rat.tail`)
- CHANGED: `.tail`-Dateien zur `.gitignore` hinzugefügt

## 2026-06-18

**Christof**
- ADDED: Passwort-Policy im Backend (≥ 8 Zeichen, mind. ein Buchstabe + eine
  Ziffer) in `register()` und beim Passwortwechsel in `edit_user()`; gibt bei
  Verstoß HTTP 400 mit klarer Meldung zurück (spiegelt `RAT_Logic.PasswordPolicy`
  des Clients) (**KI-13**)
- ADDED: `DELETE /user/{id}` (nur globale Admins) – räumt Permissions, Logins,
  SNMP-Settings und die UserSettings des Users mit auf; ein Admin kann sich nicht
  selbst löschen (**KI-14**)
- ADDED: plattformübergreifende Start-Skripte (`run.bat` / `run.ps1` / `run.sh`):
  legen `.venv` an, installieren `requirements.txt`, starten den Server
  (Host/Port konfigurierbar, optionaler Auto-Reload)
- DOCS: README-Quickstart, der auf die Run-Skripte zeigt
- CHANGED: `requirements.txt` aufgeräumt (python-jose/passlib/python-multipart
  gepinnt, ungenutztes django entfernt)

**Tobias**
- CHANGED: Beim Anlegen eines NetworkObjects mit bereits vergebenem Namen wird nun
  HTTP 409 statt eines Internal Server Errors zurückgegeben
- UPDATED: `requirements.txt`

## 2026-06-21

**Christof** (mit KI-Unterstützung, siehe [AI_usage.md](AI_usage.md) KI-15 bis KI-19)
- FIXED: Logging schreibt jetzt in `api.log` (statt `rat.tail`) und protokolliert
  zusätzlich Fehler (ERROR) über einen globalen Exception-Handler; INFO für jeden
  Request, Ausgabe in Konsole **und** Datei (**KI-15**)
- ADDED: Aggregations-/Statistik-Endpunkte unter `/statistics` (GROUP BY mit
  COUNT/SUM/AVG): Zusammenfassung, Geräte je Typ, Connections je Typ,
  Interfaces je Gerät (**KI-16**)
- ADDED: erweiterte Filterung, Sortierung und Pagination (`limit`/`offset`) für die
  GET-Listen von NetworkObject, NetworkObjectInterface, NetworkObjectConnection und
  User (**KI-17**)
- ADDED: Cloud-DB-Vorbereitung – `DATABASE_URL` aus Umgebungsvariable/`.env`
  (Fallback auf lokales SQLite), inkl. `.env.example` (**KI-18**)
- FIXED: erfolgreiche PUT/DELETE geben jetzt eine normale 200-Antwort zurück statt
  eine HTTPException(200) zu *werfen* (Exceptions sind nur für Fehler); zugleich
  Refresh-vor-Commit-Bug in `PUT /networkObjectPermission/{id}` behoben, der die
  Änderung verworfen hatte (**KI-19**)
