# Hilfe: Stundenplan

Der **Stundenplan** ist die **Wochenvorlage** für Ihre Arbeitszeiten (mehrere Blöcke pro Wochentag möglich). Aus ihm können Sie im Reiter **Zeiteinträge** per **Doppelklick auf das Datum** Zeiten in eine Zeile **übernehmen** (passender Wochentag und n-te Zeile am Tag).

---

## Kein Jahresfilter

Der Stundenplan gilt **wiederkehrend pro Woche** und wird **für alle Wochentage** geladen und gespeichert – unabhängig vom Monat in den Zeiteinträgen.

---

## Schaltflächen

| Aktion | Bedeutung |
|--------|-----------|
| **Zeile hinzufügen** | Fügt eine neue Zeile ein (Wochentag richtet sich nach der **Markierung** bzw. der letzten Zeile). |
| **Markierte Zeile(n) löschen** | Entfernt die ausgewählten Zeilen aus der Ansicht; endgültig nach **Speichern**. |
| **Alle Zeilen speichern** | Schreibt den **gesamten** Stundenplan in die Datenbank und lädt danach neu ein. |

---

## Tabelle

- **Wochentag**: **Mo** bis **So** – welcher Wochentag dieser Zeile zugeordnet ist.
- **Arbeitsphase**: **Von** und **Bis** (Arbeitsbeginn und -ende), üblicherweise im Format **HH:MM**.
- **Pause** und **Pause 2**: jeweils **Von** und **Bis** – optional; Pausen werden bei der **Soll**-Anzeige berücksichtigt.
- **Soll**: **berechnete** Netto-Arbeitszeit der Zeile (nur Anzeige).
- **Kommentar**: kurzer Freitext pro Zeile.

Sie können Zellen **direkt bearbeiten**; bei Zeitfeldern genügt oft die **Stundeneingabe** (z. B. `8`), die Anwendung kann sie in ein Uhrzeitformat umsetzen.

**Strg+C** kopiert die **markierten Zellen** in die Zwischenablage (schneller Ausschnitt, nicht derselbe Ablauf wie der Excel-Export in den Zeiteinträgen).

---

## Summe und Status

- **Unten rechts**: Summe der **Soll**-Zeiten über alle Zeilen (Orientierung).
- **Unten links**: Meldungen nach Speichern/Laden oder bei Fehlern.

**Rote Schrift** in Zeilen: noch **nicht gespeicherte** Änderungen oder neue Zeilen.

---

## Reiterwechsel

Beim Verlassen des Reiters mit **ungespeicherten** Änderungen kann eine **Abfrage** erscheinen; vorher **Alle Zeilen speichern**, wenn der Stand erhalten bleiben soll.
