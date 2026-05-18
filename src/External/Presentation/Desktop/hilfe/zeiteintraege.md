# Hilfe: Zeiteinträge

Dieses Fenster dient der **monatlichen Erfassung** Ihrer Arbeitszeiten. Die Tabelle zeigt die Tage des gewählten Monats; Sie tragen Arbeitsbeginn, -ende und Pausen ein. Zusätzliche Informationen (Urlaub, Feiertag, Krankheit usw.) werden automatisch angezeigt, sobald die dazu passenden Daten in den anderen Reitern gepflegt sind.

---

## Jahr und Monat

- **Jahr** und **Monat** wählen Sie oben links.
- Beim Wechsel von Jahr oder Monat wird der **neue Monat aus der Datenbank geladen**. Ungespeicherte Änderungen am aktuellen Monat gehen dabei verloren; Sie werden vorher gefragt, ob Sie fortfahren möchten.

---

## Schaltflächen in der Werkzeugleiste

| Aktion | Bedeutung |
|--------|-----------|
| **Zurücksetzen** | Lädt den aktuellen Monat erneut aus der Datenbank und **verwirft** alle noch nicht gespeicherten Änderungen in der Tabelle. Die Schaltfläche ist nur aktiv, wenn es **ungespeicherte** Änderungen gibt. Vor dem Ausführen erscheint eine Sicherheitsabfrage. |
| **Für Excel kopieren** | Kopiert den Monat für Excel in die Zwischenablage (**vorgesehene Spalten und Formate**). Details siehe Abschnitt „Export nach Excel und Zwischenablage“. |
| **Zeile hinzufügen** | Fügt am Ende der Tabelle eine neue Zeile ein (z. B. zweiter Arbeitsblock am selben Tag). |
| **Markierte Zeile(n) löschen** | Löscht die ausgewählten Zeilen aus der Ansicht. **Erst nach „Alle Zeilen speichern“** werden Löschungen und andere Änderungen dauerhaft in der Datenbank gesichert. |
| **Alle Zeilen speichern** | Speichert den **gesamten** Monat: neue Zeilen, Änderungen und Löschungen. Bei Erfolg erscheint eine kurze Meldung in der Statuszeile unten links. |

---

## Tabelle: Spalten im Überblick

- **Tag** und **Datum**: Der Wochentag wird aus dem Datum abgeleitet. Datum im Format **TT.MM.JJJJ** (z. B. 18.05.2026). Am **Wochentag** erscheint ein kleines Symbol, wenn es sich um einen **Feiertag** handelt.
- **F, U, K, Sf, Bf**: Schmale Spalten mit **Kennzeichen** (Symbole) für Feiertag, Urlaub, Krankheit, Schulferien und Betriebsferien. Diese Werte kommen aus den Stammdaten; Sie bearbeiten sie hier nicht direkt. Mit der Maus über ein aktives Symbol fahren zeigt oft einen **Kurztext** (z. B. Feiertagsname).
- **Von** und **Bis**: Arbeitsbeginn und -ende im Format **HH:MM** (z. B. 08:30 und 17:00).
- **Zwei Pausenpaare** (je **Von** / **Bis**): Optional. Wenn Sie eine Pause erfassen, tragen Sie **Beginn und Ende** ein; einzelne halbe Paare sind nicht vorgesehen. Die Pausen werden bei der Berechnung der geleisteten Zeit abgezogen.
- **Geleistet**: Die **errechnete** Netto-Arbeitszeit aus Von/Bis minus Pausen (nur Anzeige, keine direkte Eingabe).
- **Soll** und **Vertrag**: Anzeige der **Sollzeiten** nach Stundenplan bzw. nach vertraglicher Vorgabe (abhängig von Kalendertag und Konfiguration). Details variieren je nach Tag (z. B. Feiertag, Urlaub).
- **Kommentar**: Freitext (begrenzte Länge), z. B. Tätigkeit oder Hinweise. Unter bestimmten Bedingungen kann der Eintrag **automatisch ergänzt** werden (z. B. Kennzeichen für Urlaub/Krankheit).
- **Tag** (zweite Spalte mit diesem Namen), **Feiertagsname**, **Schulferienname**: Zusatzinformationen, teils für den Export nach Excel; Feiertags- und Feriennamen werden aus der Anwendungsschicht übernommen (nicht gespeichert).

Zeilen mit **roter Schrift** sind **noch nicht gespeichert** oder weichen vom zuletzt geladenen Stand ab.

---

## Schneller Übernahme aus dem Stundenplan

- **Doppelklick auf die Zelle „Datum“** (nicht auf andere Spalten) einer Zeile übernimmt für diesen Tag und diese **Zeilenposition** die passende Vorlage aus dem Reiter **Stundenplan** (gleicher Wochentag, n-te Zeile am Tag entspricht dem n-ten Block im Stundenplan).
- An **Feiertagen** ist diese Übernahme nicht vorgesehen.
- Wenn im Stundenplan für diesen Wochentag **kein** passender Eintrag existiert oder die Zeile nicht zur „n-ten“ Zeile des Tages passt, passiert nichts.
- Ist das **Kommentar**-Feld der Zeile noch leer, kann die **Anmerkung aus dem Stundenplan** übernommen werden.

---

## Export nach Excel und Zwischenablage

- **Empfohlen:** Verwenden Sie die Schaltfläche **„Für Excel kopieren“** in der Werkzeugleiste. So landen **alle Tage des Monats** in der Zwischenablage in der **vorgesehenen Spaltenfolge** (laut `cell_spec` in `config.toml`) – unabhängig davon, welche Spalten in der Tabelle gerade sichtbar oder ausgeblendet sind. Anschließend in der Tabellenkalkulation **einfügen** (üblicherweise **Strg+V**).
- **Strg+C** in der Tabelle kopiert nur den **aktuell markierten Zellbereich** wie in der Ansicht; Spaltenauswahl und Format entsprechen **nicht** dem Excel-Export. Nutzen Sie das höchstens für kurze Auszüge – für den Monats-Export sollten Sie **immer „Für Excel kopieren“** verwenden.

### LibreOffice / OpenOffice Calc

Calc liest das spezielle Excel-Zwischenablageformat (**XML Spreadsheet**) beim Einfügen **nicht**. Es wird **tab-getrennter Text** eingefügt. Dabei bleiben in Calc oft **alte Zellinhalte** stehen, wenn die App für einen Tag **keinen** Wert liefert (z. B. leeres Wochenende) – Calc überschreibt solche Zellen beim Einfügen **nicht** mit „leer“.

**Praktischer Ablauf in Calc:** Markieren Sie in der Monatstabelle **zuerst genau den Bereich**, den Sie neu befüllen wollen (alle Zeilen und Spalten des Monats, die aus der App kommen sollen), **löschen** Sie diesen Bereich (Entf), und **fügen** Sie danach aus der Zwischenablage ein (**Strg+V**). So verschwinden alte Einträge an Tagen ohne neue Daten zuverlässig.

Spalten mit **Formeln** in Ihrer Calc-Datei (z. B. Geleistet/Soll, in der Konfiguration als `"blank"` markiert) werden beim tab-getrennten Einfügen **mit erfasst**; schützen Sie sie ggf. durch die Auswahl beim Löschen/Einfügen oder stellen Sie Formeln danach wieder her.

### Microsoft Excel

Unter **Microsoft Excel** kann das Einfügen anders reagieren (u. a. über das Format **XML Spreadsheet**): Leere exportierte Felder werden dort oft **direkt** als leere Zellen übernommen, und in `config.toml` als `"blank"` gekennzeichnete Spalten sollen **nicht** überschrieben werden (Formeln bleiben erhalten). Ob Sie in Excel **denselben** Schritt „Bereich vorher löschen“ brauchen, hängt von Ihrer Vorlage ab – wenn nach dem Einfügen noch alte Werte an leeren Tagen stehen, löschen Sie den Zielbereich wie in Calc **vor** dem Einfügen und fügen Sie erneut ein.

---

## Reiter und ungespeicherte Änderungen

- Das Programm hat mehrere **Reiter** (Zeiteinträge, Stundenplan, Urlaub, …). Beim **Wechsel** von einem Reiter zu einem anderen werden **ungespeicherte Änderungen** im bisherigen Reiter verworfen, sofern Sie das in der Abfrage bestätigen. Wechseln Sie also zuerst zurück und speichern, wenn etwas erhalten bleiben soll.
- Beim **Schließen** des Fensters mit ungespeicherten Änderungen erscheint ebenfalls eine Abfrage.

---

## Statuszeile und Summen

- **Unten links** erscheinen kurze **Hinweise** (z. B. nach dem Speichern oder Kopieren). Die Meldung verschwindet nach einiger Zeit von selbst.
- **Unten rechts** sehen Sie **Summen** für die geleistete Zeit sowie die Sollwerte nach Stundenplan und nach Vertrag für den **aktuell angezeigten Monat** (über alle sichtbaren Zeilen).
