# Tätigkeitsbericht

Die Zeitaufschreibung soll nach den Kriterien der Clean-Architektur passieren, sodass die Programmbestandteile 
wiederverwendet werden können. 

Das Programm soll sich die Feiertage aus einer bekannten JSON-Adresse von Google herunter laden können, 
und die entsprechende Tage damit markieren. 

## Model

Domain-Modelle aus `src/Core/Domain/models/models_worktime.py`. Felder mit „optional“ dürfen leer (`None`) bleiben; `id` wird von der Datenbank vergeben.

### Gemeinsame Basis `ArbeitszeitBasis`

Wird von `Zeiteintrag` und `Stundenplan` geerbt.

| Feld            | Typ           | Pflicht | Beschreibung                                  |
|-----------------|---------------|---------|-----------------------------------------------|
| uhrzeit_von     | Time          | ja      | Startzeit der Arbeit                          |
| uhrzeit_bis     | Time          | ja      | Endzeit der Arbeit                            |
| pause_beginn    | Time          | nein    | Start der ersten Unterbrechung                |
| pause_ende      | Time          | nein    | Ende der ersten Unterbrechung                 |
| pause2_beginn   | Time          | nein    | Start der zweiten Unterbrechung               |
| pause2_ende     | Time          | nein    | Ende der zweiten Unterbrechung                |
| anmerkung       | String(80)    | nein    | Freitext, max. 80 Zeichen                     |

Validierung: `uhrzeit_von ≤ uhrzeit_bis`; Pausenzeiten müssen im Arbeitszeitfenster liegen, beide Pausen-Felder paarweise gesetzt sein, `beginn < ende`, und Pause 1 und Pause 2 dürfen sich nicht überlappen.

### Tabelle `Zeiteintrag` (erbt von `ArbeitszeitBasis`)

| Feld   | Typ  | Pflicht | Beschreibung                          |
|--------|------|---------|---------------------------------------|
| id     | UUID | nein    | Primärschlüssel (DB-generiert)        |
| datum  | Date | ja      | Kalendertag des Zeiteintrags          |

### Tabelle `Stundenplan` (erbt von `ArbeitszeitBasis`)

Wochenvorlage für Soll-Arbeitszeiten je Wochentag.

| Feld       | Typ  | Pflicht | Beschreibung                                |
|------------|------|---------|---------------------------------------------|
| id         | int  | nein    | Primärschlüssel (DB-generiert)              |
| wochentag  | int  | ja      | 1 = Montag … 7 = Sonntag (Bereich 1–7)      |

### Tabelle `Feiertag`

| Feld           | Typ        | Pflicht | Beschreibung                                                  |
|----------------|------------|---------|---------------------------------------------------------------|
| datum          | Date       | ja      | Kalendertag des Feiertags (Primärschlüssel)                   |
| feiertagsname  | String(80) | ja      | Name des Feiertags                                            |
| hinweis        | String(80) | nein    | Zusatzinfo, z. B. aus Feiertags-API                           |
| ist_halber_tag | bool       | nein    | `true` = halber Tag (Standard: `false`, ganzer Tag)           |
| ist_offiziell  | bool       | nein    | `true` = gesetzlicher Feiertag (Standard: `true`)             |

Internet-Import (`Aus Internet importieren`): Feiertage von feiertage-api.de als **ganze, offizielle** Tage; zusätzlich Einträge aus `src/feiertag_zusatz_import.json` (z. B. 24.12. und 31.12. als halbe, nicht offizielle Tage). Konfiguration: `src/external_api.toml` → `feiertage_api.zusatz_import_datei`.

### Tabelle `Urlaubsantrag`

| Feld         | Typ        | Pflicht | Beschreibung                                                                  |
|--------------|------------|---------|-------------------------------------------------------------------------------|
| id           | int        | nein    | Primärschlüssel (DB-generiert)                                                |
| datum_von    | Date       | ja      | Erster Urlaubstag (`datum_von ≤ datum_bis`)                                   |
| datum_bis    | Date       | ja      | Letzter Urlaubstag                                                            |
| urlaubstyp   | String(80) | ja      | Art des Urlaubs (z. B. Erholung, Sonderurlaub)                                |
| urlaubstage  | float      | ja      | ≥ 0, nur in Halbtags-Schritten (z. B. 1, 1.5, 2, 2.5)                         |
| genehmigt    | bool       | nein    | Genehmigungs-Status (Standard: `false`)                                       |

### Tabelle `Krankmeldung`

| Feld              | Typ        | Pflicht | Beschreibung                                            |
|-------------------|------------|---------|---------------------------------------------------------|
| id                | int        | nein    | Primärschlüssel (DB-generiert)                          |
| krank_von         | Date       | ja      | Erster Krankheitstag (`krank_von ≤ krank_bis`)          |
| krank_bis         | Date       | ja      | Letzter Krankheitstag                                   |
| krankmeldungstage | int        | ja      | Anzahl Tage, ≥ 0                                        |
| anmerkung         | String(80) | nein    | Freitext, max. 80 Zeichen                               |

### Tabelle `Betriebsferien`

| Feld               | Typ        | Pflicht | Beschreibung                                          |
|--------------------|------------|---------|-------------------------------------------------------|
| id                 | int        | nein    | Primärschlüssel (DB-generiert)                        |
| datum_von          | Date       | ja      | Erster Tag (`datum_von ≤ datum_bis`)                  |
| datum_bis          | Date       | ja      | Letzter Tag                                           |
| betriebsferienname | String(80) | ja      | Bezeichnung der Betriebsferien                        |
| anmerkung          | String(80) | nein    | Freitext, max. 80 Zeichen                             |

### Tabelle `Schulferien`

| Feld            | Typ        | Pflicht | Beschreibung                                             |
|-----------------|------------|---------|----------------------------------------------------------|
| id              | int        | nein    | Primärschlüssel (DB-generiert)                           |
| datum_von       | Date       | ja      | Erster Ferientag (`datum_von ≤ datum_bis`)               |
| datum_bis       | Date       | ja      | Letzter Ferientag                                        |
| schulferienname | String(80) | ja      | Bezeichnung der Schulferien                              |
| anmerkung       | String(80) | nein    | Freitext, max. 80 Zeichen                                |

### DTO `ZeiteintragsDTO` (GUI-Anzeige)

Erweitert `Zeiteintrag` um berechnete Felder; nicht in der Datenbank gespeichert, sondern von der Anwendungsschicht für die Tabelle erzeugt. `uhrzeit_von` und `uhrzeit_bis` sind im DTO optional, damit auch unvollständige Zeilen angezeigt werden können.

| Feld                          | Typ        | Beschreibung                                                          |
|-------------------------------|------------|-----------------------------------------------------------------------|
| uhrzeit_von                   | Time?      | Startzeit (überschreibt Pflichtfeld der Basis)                        |
| uhrzeit_bis                   | Time?      | Endzeit (überschreibt Pflichtfeld der Basis)                          |
| geleistete_stunden            | Time?      | Netto-Arbeitszeit (Von/Bis minus Pausen)                              |
| soll_stunden_nach_Stundenplan | Time?      | Soll-Zeit aus dem Stundenplan, je Zeile                               |
| soll_stunden_nach_vertrag     | Time?      | Soll-Zeit aus dem Vertrag (Wochentag), nur in Zeile 1 je Tag          |
| ist_urlaub                    | bool       | Tag liegt in einem Urlaubsantrag                                      |
| ist_krank                     | bool       | Tag liegt in einer Krankmeldung                                       |
| ist_feiertag                  | bool       | Tag ist ein Feiertag                                                  |
| ist_ferien                    | bool       | Tag liegt in Schulferien                                              |
| ist_betriebsferien            | bool       | Tag liegt in Betriebsferien                                           |
| feiertagsname                 | String(80) | Name des Feiertags (falls vorhanden)                                  |
| schulferienname               | String(80) | Name der Schulferien (falls vorhanden)                                |

## Sollstunden in der Zeiterfassung

Beschreibung der Sollstunden-Berechnung (nach Vertrag und nach Stundenplan), Kommentarregeln und Tages-Flags: siehe [readme_sollstunden.md](./readme_sollstunden.md).

## Desktop-Frontend

Diese Anwendung soll eine plattformübergreifendes Desktop-Frontend ergeben, das die Zeitaufschreibung in eine SQLite-Datenbank speichert. 
Zusätzlich soll ein Export der Stunden nach MS-Excel möglich sein. 

## Web-Frontend

Über IndexedDB wird man sich die eigenen Einträge sichern, die man mit dem Backend synchronisieren kann. 

## Backend über GraphQL

Die Kommunikation soll zu einer GraphQL-API geschehen, wenn man am Monatsende die Stunden "abgeben" will und die Abrechnung für den Monat geschehen soll. 
Dann spätestens muss man sich vorher einloggen und ein Token für die Abgabe erhalten. 

## Anbindung zur Datenbank

Die Persistenz erfolgt über SQLite. Die Anbindung geschieht über ein ORM (SQLModel auf Basis von SQLAlchemy); per Dependency Injection und Repository-Pattern bleiben die Aufrufer von der konkreten Speicherung entkoppelt. 

## Tests

Automatisierte Tests (pytest, In-Memory-SQLite, Schichten unter `test/`): siehe [test/README_tests.md](./test/README_tests.md).

## Python Setup

Empfohlen ist eine lokale virtuelle Umgebung (`venv`), damit Abhaengigkeiten isoliert sind.

### Linux (Bash)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Zum Verlassen der Umgebung:

```bash
deactivate
```

Tests ausführen: `python -m pytest test/` — siehe [test/README_tests.md](./test/README_tests.md).

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Zum Verlassen der Umgebung:

```powershell
deactivate
```

Tests ausführen (nach Aktivierung der venv): `py -m pytest test/` — Details in [test/README_tests.md](./test/README_tests.md).

### Bemerkung zum Setup

Fall zusätzliche Pakete benötigt werden, sind sie im "pip install -r requirements.txt" mit drin... 