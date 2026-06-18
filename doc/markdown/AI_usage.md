# AI useage
This file is for documenting all ai usage :D

---------

Created by claude:
doc/markdown/style/rats.css
doc/markdown/style/template.md
prompt: use the RAT logo in assets and make a cool markdown theme that is mainly it and about rats

ai question -> css template or both? -> both

---------


---------

Created by claude:
Readme.md
prompt: can you write the README.md for github also with the style if possible idk if that works on github

ai question -> has RAT a meaning? -> Remote Access Topology -> what does it do? -> Network topology with users that have diffrent privileges diffrent logins like ssh can be added to devices to change settings remote see also the Project_Planning.md file

---------


---------

Edited by claude:
doc/assets/drawio/DB_Sketches.drawio
prompt: we have done the 3 Normalform RM Diagramm and ERM Diagramm can you add us the second and first Normalform of the Database

---------


=========  PERMISSION SYSTEM  =========

Model: Claude (claude-opus-4-8) via Claude Code
Date: 2026-06-16

Overall user prompt (translated/summarized):
"NetworkObjectPermission has an integer `permissions`:
  0 = Hidden  (user may not see it; same as having no permission row at all)
  1 = See     (user can see the device + interfaces; may add their own logins/snmp settings)
  2 = Edit    (may add/edit/delete interfaces and change NO settings like name; cannot delete the NO)
  3 = Admin   (may grant/change roles of users with LOWER rights than himself, i.e. 0..2)
  4 = Owner   (may change Admins, grant/remove Owner, and delete the object)
Add the permission checks to every route so not everyone can do everything, only users
with the right level. Also document all AI usage (model, prompt, ...) and mark every
changed spot in the code with `#KI Claude + <prompt number>`. While reading the code,
note possible problems with `#KI Claude detected problem why/what:`."

How the prompt numbers map to the code markers (search for `KI Claude <KI-N>`):

<KI-1>  src/permissions.py  (NEW FILE)
        Created a central helper module with the enum constants
        (HIDDEN/SEE/EDIT/ADMIN/OWNER) plus:
          - get_permission_level(db, user, network_object_id)
              -> effective level; no row == HIDDEN; global is_admin == OWNER
          - require_permission(db, user, network_object_id, min_level)
              -> raises 404 if Hidden (so existence stays secret), 403 if too low.

<KI-2>  src/routers/networkObject.py
          - GET /          : only returns NOs where the user has See(1)+ (admins: all)
          - POST /         : requires is_admin or user.canCreate; creator is made Owner
                             of the new object (otherwise nobody could see it)
          - PUT /{id}      : requires Edit(2)+
          - DELETE /{id}   : requires Owner(4); also cleans up permission rows.
                             Removed the bogus request body from DELETE.

<KI-3>  src/routers/networkObjectInterface.py
          - GET /          : only interfaces of NOs the user may See(1)+
          - POST /         : Edit(2)+ on the target NO
          - PUT /{id}      : Edit(2)+ on both old and new NO of the interface
          - DELETE /{id}   : Edit(2)+ on the interface's NO

<KI-4>  src/routers/networkObjectConnection.py
          - GET /          : only connections touching a See(1)+ NO
          - POST /         : Edit(2)+ on the NOs of both endpoint interfaces
          - PUT /{id}      : Edit(2)+ on the NOs of all attached interfaces
          - DELETE /{id}   : same; also fixed wrong-model bug (see problems below)

<KI-5>  src/routers/networkObjectPermission.py
          - Added `target_user_id` to the input (you must say WHO you grant to).
          - assert_can_grant() enforces:
              * only Admin(3)/Owner(4) may grant
              * Admin may only touch users with strictly lower rights, and may
                only assign levels 0..2
              * Owner may assign anything incl. Admin/Owner
          - GET /          : own rows + (for Admin/Owner) all rows on managed objects
          - POST /         : grant/update with the rules above; upserts instead of
                             creating duplicate (user, object) rows
          - PUT /{id}      : same rules; forbids retargeting the row to another
                             object/user
          - DELETE /{id}   : treated as "set to Hidden(0)", same rules apply

----- Problems Claude detected (marked in code with `#KI Claude detected problem why/what:`) -----

1. networkObjectPermission.py (original): the route set `user_id = current_user.id`
   and had no level checks at all -> ANY logged-in user could POST themselves
   `permissions = 4` (Owner) on ANY object = complete privilege escalation. Fixed by
   the whole <KI-5> rewrite.

2. networkObjectConnection.py delete_item: used `models.DBNetworkObject` instead of
   `models.DBNetworkObjectConnection`, so it looked up / deleted the wrong table.
   Fixed to DBNetworkObjectConnection.

3. networkObjectConnection.py create: `models.DBNetworkObjectConnection(**nOC.model_dump())`
   included `nO1`/`nO2`, which are not columns of that table -> would raise at runtime.
   Fixed with `model_dump(exclude={"nO1","nO2"})`.

4. networkObjectPermission: no uniqueness on (user_id, network_object_id), so a user
   could accumulate several conflicting permission rows. Mitigated by upserting in POST.
   (NOTE: a real fix should be a DB UNIQUE constraint on those two columns in models.py.)

----- Further problems Claude noticed but did NOT change (out of scope / need your decision) -----

#KI Claude detected problem why/what:
 a) auth.py: SECRET_KEY is hard-coded in the source and committed to git. It should
    come from an environment variable / config file and the leaked key be rotated.
 b) routers/userSettings.py references `current_user.user_settings_id`, but DBUser in
    models.py has no such column (and DBUserSettings is never auto-created on register).
    These routes will crash. Needs a model/relationship fix.
 c) routers/user.py register() is just `pass` -> no users can be created via the API,
    and there is no "create first admin" bootstrap (the TODO in the file).
 d) UserIn uses `hashed_password` but expects a plaintext password; passwords are never
    hashed/stored on register since register is unimplemented.
 e) Login/SNMP routers only check `nOP.user_id == current_user.id` (ownership of the
    permission row). That is correct for per-user logins, but they do NOT verify the
    user still has at least See(1) on the underlying object. Probably fine, flagging it.

---------


=========  USER SETTINGS + ADMIN BOOTSTRAP  =========

Model: Claude (claude-opus-4-8) via Claude Code
Date: 2026-06-16

User prompt (translated):
"Can you fix userSettings: make every user get a userSettings on creation, and also
make it so that on first start, when there is no DB yet, an admin user is created with
password 'admin'."

Prompt-number -> code marker mapping (search `KI Claude <KI-N>`):

<KI-6>  src/models.py + src/routers/userSettings.py
          - models.py: added a one-to-one `settings` relationship between DBUser and
            DBUserSettings (the user_settings_id column the route used never existed).
          - userSettings.py: look settings up by user_id via get_or_create_settings()
            (lazily creates them for legacy users); fixed UserSettingsOut to map the
            camelCase DB columns (showPorts/showInterfaces) to the snake_case API
            fields via validation_alias; removed stray `from pip._internal...` import;
            fixed refresh-before-commit bug that discarded edits.

<KI-7>  src/routers/user.py
          - Implemented register(): rejects duplicate usernames, hashes the password,
            creates the user AND a DBUserSettings row for them.
          - Renamed the misleading `hashed_password` input field to `password`
            (the value is plaintext and is hashed server-side).

<KI-8>  src/main.py
          - create_default_admin(): on a fresh DB (no users) creates admin/admin with
            is_admin + canCreate and its settings. Registered the userSettings router
            (it was never included before).

Verified with a smoke test (throwaway sqlite DB): bootstrap admin created, settings
defaults present, relationship works, login verifies admin/admin, and UserSettingsOut
serializes showPorts->show_ports correctly.

This resolves earlier flagged problems (b), (c) and (d). Still open: (a) hard-coded
SECRET_KEY, and the default admin password 'admin' should be changed after first login.

---------


=========  PUT PERSISTENCE BUG FIX  =========

Model: Claude (claude-opus-4-8) via Claude Code
Date: 2026-06-16

User prompt (translated):
"Is anything still missing before a C# frontend UI can be attached?"
-> Frontend will be a C# desktop app (WPF/WinForms/MAUI), so CORS is not required.
   User chose to fix only the refresh-before-commit bugs now.

<KI-9>  src/routers/networkObject.py, networkObjectInterface.py,
        networkObjectConnection.py, snmpSettings.py, login.py
          - All PUT/edit handlers called self.db.refresh(obj) BEFORE self.db.commit().
            refresh() reloads the row from the DB, throwing away the in-memory edits,
            so updates were silently lost. Swapped to commit() first, then refresh().
          - (The POST/create handlers were already in the correct order.)

Verified with a throwaway-DB test: editing a NetworkObject's name now persists across
a fresh session. Compiles clean.

Noted but NOT changed (user deferred): no CORS middleware (fine for a desktop C#
client using HttpClient, needed for any browser/Blazor frontend); PUT handlers
`raise HTTPException(200)` instead of returning a success body; SECRET_KEY still
hard-coded.

---------


=========  C# FRONTEND LINK (minimal backend additions)  =========

Model: Claude (claude-opus-4-8) via Claude Code
Date: 2026-06-16

Context: the C# client (RAT-Client) got a real IDatabaseConnection implementation
(DatabaseConnection.cs) that talks to this backend over HTTP. The user asked NOT to
change the backend unless necessary. Two things were necessary and are documented here.
Marked in code with `KI Claude <KI-10>`.

<KI-10>  src/routers/user.py
          - Added `can_create` to UserBase/UserOut/UserIn (validation_alias "canCreate"
            so it maps to the DBUser.canCreate column, populate_by_name so both names
            work). The client needs to know whether a user may create NetworkObjects
            (maps to RAT_Data.User.CanCreate / NetworkUser.CanCreate).
          - register() now persists `canCreate` from the request.
          - Added `GET /user/` (list all users, auth required). The client needs it to
            resolve the user_id stored in a NetworkObjectPermission back to a username
            (Access Control tab) and to implement IDatabaseConnection.GetAllUsers().

         src/routers/networkObjectInterface.py
          #KI Claude detected problem why/what: NetworkObjectInterfaceOut.
          network_object_connection_id was typed as a non-optional `int`, but the column
          is NULL for any interface not attached to a connection. GET /networkObjectInterface/
          then crashed with a ResponseValidationError (None is not an int), which blocked
          the C# client from loading the topology. Changed the type to `int | None`.

Verified against a throwaway DB with the live server: form login -> JWT; /user/me and
/user/ return can_create; NetworkObject create/list; the creator's permission row is
Owner(4); per-device login create/list; PUT /user/settings/ returns 200; and after the
interface fix, interface + connection create/list serialize correctly. All response
shapes match the client's DTOs.

Still open (unchanged): hard-coded SECRET_KEY; default admin password 'admin'; no CORS
(not needed for the desktop HttpClient client).

---------


=========  CASCADE DELETE FOR NETWORKOBJECT  =========

Model: Claude (claude-opus-4-8) via Claude Code
Date: 2026-06-16

Context: second pass on the C# client (RAT-Client prompt 14) made it edit/delete
interfaces, connections, logins and permissions through the API. While testing the
delete path, the delete route turned out to leave dangling rows.

<KI-11>  src/routers/networkObject.py
          #KI Claude detected problem why/what: delete_item only removed the
          NetworkObject and its permission rows. Its interfaces (and the connections
          those interfaces used, plus the logins / snmp settings on the permission
          rows) stayed behind as orphans, and on the next graph load the client then
          referenced interfaces whose object no longer exists. delete_item now
          cascade-deletes: interfaces of the object -> the connections those interfaces
          used -> logins + snmp settings on the object's permission rows -> the
          permission rows -> the object itself.

Verified against a throwaway DB with the live server: created two objects with one
interface each and a connection between them, granted another user See on one object,
then deleted that object. Its interface and the connection were gone afterwards while
the other object's interface remained. (Minor, left as-is: the surviving interface's
network_object_connection_id still points at the deleted connection; harmless because
the client only rebuilds a connection when BOTH endpoints reference it.)

---------


=========  EDIT USER ENDPOINT  =========

Model: Claude (claude-opus-4-8) via Claude Code
Date: 2026-06-17

Context: the C# client needed a way to edit users (change username / password / admin /
can_create). The API only had register (create) — EditUser had no endpoint.

<KI-12>  src/routers/user.py
          - Added a `UserEdit` model (all fields optional: username / password /
            is_admin / can_create) and `PUT /user/{id}`. Authorization:
              * a global admin may edit ANY user and ANY field
              * a normal user may edit ONLY themselves, and only username + password
                (is_admin / can_create from the payload are ignored for a non-admin
                self-edit; editing any other user returns 403)
            An empty/missing password leaves the current one unchanged; the password is
            hashed server-side; username uniqueness is enforced (409 on clash).

Verified against a throwaway DB: admin renames + promotes another user (200); a normal
user self-edits name+password (200, re-login with the new password works); a normal user
editing someone else is 403; a normal user self-edit trying to set is_admin/can_create is
accepted but ignored (the row stays non-admin / can_create False).

This is what the client's IDatabaseConnection.EditUser (PUT /user/{id}) talks to, used by
the admin "Manage Users" Edit button and the per-user "Edit my account" in Settings.

---------

=========  PASSWORD POLICY  =========

Model: Claude (claude-opus-4-8) via Claude Code
Date: 2026-06-18

Context: passwords were stored without any strength check (frontend or backend). The client now
validates client-side (RAT_Logic.PasswordPolicy) and the backend must enforce the same so a weak
password can never reach the database.

<KI-13>  src/routers/user.py
          - Added validate_password(password): enforces the policy
              * at least 8 characters
              * at least one letter
              * at least one digit
            Raises HTTP 400 with a clear message otherwise.
          - Called from register() (new user) and from edit_user() when a new password is supplied
            (an empty password on edit still means "leave unchanged", so it is not checked then).

Marked in code with `KI Claude <KI-13>`. Mirrors the C# client's RAT_Logic.PasswordPolicy
(same rules) so validation is consistent on both ends.

---------
