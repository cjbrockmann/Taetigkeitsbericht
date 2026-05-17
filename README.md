# Tätigkeitsbericht

Die Zeitaufschreibung soll nach den Kriterien der Clean-Architektur passieren, sodass die Programmbestandteile 
wiederverwendet werden können. 

Das Programm soll sich die Feiertage aus einer bekannten JSON-Adresse von Google herunter laden können, 
und die entsprechende Tage damit markieren. 

## Model

Tabelle Zeiteinträge (name=tblZeiteintraege) 

- Datum: Date
- Uhrzeit_Von: Time
- Uhrzeit_Bis: Time
- Unterbrechung_Beginn: Time
- Unterbrechung_Ende: Time
- Anmerkung: String(80)

Tabelle Stundenplan (name=tblStundenplan)

- Wochentag: int (1 = Montag, 7 = Sonntag) 
- Uhrzeit_Von: Time
- Uhrzeit_Bis: Time
- Unterbrechung_Beginn: Time
- Unterbrechung_Ende: Time
- Anmerkung: String(80)

Tabelle "Feiertage" (name=tblFeiertage)

- Datum: Date
- Feiertagname: String(80)

## Sollstunden in der Zeiterfassung

Die Sollwerte, Tages-Flags (Urlaub, Feiertag, …) und Kommentarregeln werden in der Anwendungsschicht (`ZeiteintragAnwendungDTO` in `src/Core/Application/zeiteintrag_anwendung.py`) berechnet und als `ZeiteintragsDTO` an die Desktop-Tabelle übergeben. Die GUI mappt DTOs auf Tabellenzeilen und zeigt sie an; bei Datumsänderungen ruft das ViewModel `anreichere_eintraege_fuer_tag` erneut auf.

### Sollstunden nach Vertrag

- Quelle: ausschließlich `[sollstunden].wochenstunden` in `src/config.toml` (Zuordnung Wochentag → Stunden, 1 = Montag … 7 = Sonntag, inkl. Samstag und Sonntag).
- Anzeige nur in der **ersten Tabellenzeile** je Kalendertag.
- Kein Wert, wenn für den Wochentag in der Config kein Eintrag steht oder die Zeit `0:00` ist.
- **Feiertage:** Steuert `[sollstunden].sollstunden_an_feiertagen`. Ist der Wert `false` (Standard), entfällt das Vertrags-Soll an Feiertagen; ist er `true`, gilt wie an einem normalen Tag nur der Wochentag aus `wochenstunden`.
- **Urlaub- und Krankheitstage:** Stundenplan-Soll entfällt. In Zeile 1 je Tag werden Vertrags-Soll und **geleistete Stunden** gesetzt (`_berechne_geleistete_stunden`: gleich Vertrags-Soll, unabhängig von Von/Bis). Doppelklick zum Übernehmen aus dem Stundenplan bleibt möglich.

**Kommentar** (`_wende_kommentar_regeln_an`, aus `[sollstunden]` in der Config):
- **Krank** (`kommentar_krankheitstage`, z. B. `"K"`): wie Urlaub – leer → nur das Kürzel, sonst `K: {Text}`; nur Mo–Fr mit positivem Vertrags-Soll; nicht an Feiertagen.
- **Urlaub** (`kommentar_urlaubstage`, z. B. `"U"`): dieselben Regeln, aber nur wenn **nicht** krank (Krank hat Vorrang).
- An **Feiertagen** nur Feiertagsname im leeren Kommentar, kein K/U.

### Sollstunden nach Stundenplan

Die Soll-Arbeitszeit pro Tag ergibt sich aus der **Summe aller Stundenplan-Blöcke** des passenden Wochentags (Nettozeit je Block: Arbeitszeit minus Pausen, wie bei den geleisteten Stunden). Diese Tages-Summe wird auf die Zeiterfassungszeilen eines Tages **verteilt**, damit jede Zeile möglichst zum passenden Stundenplan-Eintrag passt (gleiche Reihenfolge wie beim Befüllen per Doppelklick auf das Datum).

**Ablauf je Kalendertag:**

1. Alle Stundenplan-Einträge des Wochentags werden nach `uhrzeit_von` sortiert (Block 1, Block 2, …).
2. Die Zeiterfassungszeilen des Tages werden in Tabellenreihenfolge nummeriert (Zeile 1, Zeile 2, …).
3. Zeile *i* erhält das Netto-Soll des Stundenplan-Blocks *i* (1:1-Zuordnung nach Index).
4. Gibt es **weniger Zeiterfassungszeilen als Stundenplan-Blöcke**, werden die Sollstunden der nicht zugeordneten Blöcke zur **letzten** Zeile des Tages addiert. So bleibt die Summe der angezeigten Sollstunden gleich der Tages-Summe aus dem Stundenplan.
5. Gibt es **mehr Zeiterfassungszeilen als Blöcke**, erhalten nur die ersten Zeilen einen Sollwert; weitere Zeilen bleiben in dieser Spalte leer.
6. An **Feiertagen** wird kein Stundenplan-Soll gesetzt.

**Beispiel** (Montag, Stundenplan: 08:00–12:00 und 13:00–17:00, je 4 Stunden netto):

| Zeiterfassungszeilen am Tag | Soll Stundenplan Zeile 1 | Soll Stundenplan Zeile 2 | Tages-Summe |
|----------------------------|--------------------------|--------------------------|-------------|
| 1 Zeile                    | 08:00                    | —                        | 08:00       |
| 2 Zeilen                   | 04:00                    | 04:00                    | 08:00       |
| 2 Zeilen, 3 Blöcke im Plan | 04:00                    | 06:00 (4 + 2 Rest)       | 10:00       |

Die Monatssumme in der Oberfläche summiert die Sollwerte **aller Zeilen**; sie entspricht damit der Summe der Stundenplan-Blöcke über alle erfassten Tage (ohne Feiertage).

Implementierung: `_stundenplan_bloecke_fuer_datum`, `_verteile_soll_stunden_nach_stundenplan`, `_setze_soll_felder_fuer_tag`.

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

## Python Setup

Empfohlen ist eine lokale virtuelle Umgebung (`venv`), damit Abhaengigkeiten isoliert sind.

### Linux (Bash)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Zum Verlassen der Umgebung:

```bash
deactivate
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Zum Verlassen der Umgebung:

```powershell
deactivate
```

### Bemerkung zum Setup

Fall zusätzliche Pakete benötigt werden, sind sie im "pip install -r requirements.txt" mit drin... 