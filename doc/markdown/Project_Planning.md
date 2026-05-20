# 1. Team & Projektidee
## Team
- Tobias & Christof
## Projektidee
- Projekt: RAT - Remote Access Topology
```
Unser Project heißt Remote Access Topology (RAT). Es ist eine Software mit der man Zentral sein eigenes
reales Neztwerk überwachen, überprüfen und konfigurieren kann (z.B. duch SNMP). Es sollte so ähnlich
aussehen wie Cisco Packet Tracer. Ursprünglich wollten wir auch machen das man per GUI Ports und alles
konfigurieren kann, aber der Projektumfang wäre deswegen zu viel für die gegebene Zeit und wir
konzentrieren uns erstmal auf Automatische verbindung per SSH, Telnet und FTP auf Mausclick und SNMP
Funktionen
```

## Verwaltet
- user im netzwerk die auf verschiedene Geräte zugreifen sollen und derren Logindaten auf den jeweilgen Geräten
- nicht jeder user kann alles machen also auch rechte

## Überlegunge identitäten und beziehungen
### Tabellen:
- Users (Mit gehasten Passwörtern) (es gibt normale und admins)
- Usersettings 1:1 zu User (Speichert die Settings vom Account)
- NetworkObject (Netzwerkobjekt)
- NetworkObjectConnection (Kabel zwischen Netzwerk Geräten)
- NetworkObjectUserPermissions (Ob User dieses Objekt sehen darf, offene Ports, Interfaces, Neighbours, ssh, etc)
- NetworkObjectUserPasswords (Speichert ssh Login etc vom User für dieses eine Netzwerk Object)


## must haves vs nice to haves
### must
- User crud
- UserSettings crud
- NetworkObject crud
- NetworkObjectConnection crud
- NetworkObjectUserPermissions crud
- NetworkObjectUserPasswords crud

### nice
- Statistiken anzeigenlassen wieviele kabel Geräte etc
- Bottlenecks anzeigenlassen (ein switch der den speed vom ganzen Netzwerk verkleinert)

- vom backend commands auf netzwerkgeräten ausführen damit user vom program das passwort nicht braucht sondern nur erlaubnis vom admin das er das machen darf

### wer macht was?

Beide:
- Plannung
- ERM

Tobias:
- Datenbank Erstellen
- Logik für User crud
- Logik für UserSettings crud
Christof:
- Logik für NetworkObject crud
- Logik für NetworkObjectConnection crud
- Logik für NetworkObjectUserPermissions crud
- Logik für NetworkObjectUserPasswords crud