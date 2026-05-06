# Agent Vision — North Star für jede Session

DevCD's **Vision Layer** gibt AI-Agenten eine persistente Orientierung, die über
Session-Grenzen hinweg erhalten bleibt. Statt nach jedem Kontextverlust neu zu
starten, trägt jeder Agent eine klare *North Star*-Aussage in seinem
Action Packet und Continuity Packet.

---

## Konzept

Ohne eine persistente Vision navigieren Agenten jede neue Session blind.
Der Vision Layer löst dieses Problem, indem er eine einmalig definierte
North-Star-Aussage automatisch in jedes von DevCD erzeugte Packet injiziert —
policy-gefiltert und auditierbar.

```
devcd vision init → vision.json → injected into ActionPacket.vision
                                  injected into ContinuityPacket.vision
```

---

## Erste Schritte

### Vision initialisieren

```bash
# Direkt (schnell)
devcd vision init --domain "my-project" --north-star "Build the best regression detection tool for Python projects."

# Geführt (interaktiv, 4 Fragen)
devcd vision init --guided
```

### Aktuelle Vision anzeigen

```bash
devcd vision show
devcd vision show --json    # maschinenlesbar
```

### Vision aktualisieren

```bash
devcd vision update "New north star statement." --reason "Pivot to enterprise market."
```

Die alte Aussage wird automatisch in die History verschoben.

### History einsehen

```bash
devcd vision history
devcd vision history --limit 5
```

---

## Vision im Action Packet

Ist eine Vision konfiguriert, enthält jedes `ActionPacket` und `ContinuityPacket`
ein `vision`-Feld vom Typ `VisionBlock`:

```json
{
  "vision": {
    "domain": "my-project",
    "north_star": "Build the best regression detection tool.",
    "active_since": "2026-05-07T10:00:00Z",
    "policy_reason": "vision injection into local agent surface is allowed by default policy",
    "withheld": false
  }
}
```

Wenn `withheld: true`, hat die Policy die Ausgabe blockiert.
Wenn `vision: null`, wurde kein Vision Record angelegt.

---

## Policy

Die Vision-Injektion folgt dem DevCD-Policy-Prinzip:

| Condition | Ergebnis |
|-----------|----------|
| `allow_local_storage=True` (Default) | Vision wird injiziert |
| `allow_local_storage=False` | Vision wird nicht injiziert (`null`) |

Jede Injektion wird im Event Ledger als `vision_injected`-Event aufgezeichnet.

---

## Speicherort

Der Vision Record wird lokal in `.devcd/vision.json` gespeichert.
Die Datei ist UTF-8-kodiert und enthält ein vollständiges Audit-Trail
(History der North-Star-Versionen mit Zeitstempel und optionalem Grund).

---

## Referenz

| Modell | Beschreibung |
|--------|--------------|
| `VisionRecord` | Persistierter Record in `.devcd/vision.json` |
| `NorthStarVersion` | Historisierter Eintrag (replaced_at, statement, reason) |
| `VisionBlock` | Ausgabe-Struct im Action/Continuity Packet |

| Befehl | Beschreibung |
|--------|--------------|
| `devcd vision init` | Vision initialisieren |
| `devcd vision update <statement>` | North Star updaten |
| `devcd vision show` | Aktuelle Vision anzeigen |
| `devcd vision history` | History anzeigen |
