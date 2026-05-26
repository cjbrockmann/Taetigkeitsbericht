# Hilfe: Zeiteinträge

Dieses Fenster dient der **monatlichen Erfassung** Ihrer Arbeitszeiten. Die Tabelle zeigt die Tage des gewählten Monats; Sie tragen Arbeitsbeginn, -ende und Pausen ein. Zusätzliche Informationen (Urlaub, Feiertag, Krankheit usw.) werden automatisch angezeigt, sobald die dazu passenden Daten in den anderen Reitern gepflegt sind.

---

## Jahr und Monat

- **Jahr** und **Monat** wählen Sie oben links.
- Beim Wechsel von Jahr oder Monat wird der **neue Monat aus der Datenbank geladen**. Ungespeicherte Änderungen am aktuellen Monat gehen dabei verloren; Sie werden vorher gefragt, ob Sie fortfahren möchten.

---

## Schaltflächen in der Werkzeugleiste


| Aktion                         | Bedeutung                                                                                                                                                                                                                                                    |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Zurücksetzen**               | Lädt den aktuellen Monat erneut aus der Datenbank und **verwirft** alle noch nicht gespeicherten Änderungen in der Tabelle. Die Schaltfläche ist nur aktiv, wenn es **ungespeicherte** Änderungen gibt. Vor dem Ausführen erscheint eine Sicherheitsabfrage. |
| **Für Excel kopieren**         | Kopiert den Monat für Excel in die Zwischenablage (**vorgesehene Spalten und Formate**). Details siehe Abschnitt „Export nach Excel und Zwischenablage“.                                                                                                     |
| **Zeile hinzufügen**           | Fügt am Ende der Tabelle eine neue Zeile ein (z. B. zweiter Arbeitsblock am selben Tag).                                                                                                                                                                     |
| **Markierte Zeile(n) löschen** | Löscht die ausgewählten Zeilen aus der Ansicht. **Erst nach „Alle Zeilen speichern“** werden Löschungen und andere Änderungen dauerhaft in der Datenbank gesichert.                                                                                          |
| **Alle Zeilen speichern**      | Speichert den **gesamten** Monat: neue Zeilen, Änderungen und Löschungen. Bei Erfolg erscheint eine kurze Meldung in der Statuszeile unten links.                                                                                                            |


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
- Ist das **Kommentar**-Feld der Zeile noch leer, kann die **Anmerkung aus dem Stundenplan** übernommen werden – **nicht** bei `[kommentar].kommentar_urlaub_krank_modus = "kuerzel"` in `config.toml` (dann nur Zeiten/Pausen).
- Spalte **Info**: zeigt beim Laden den Stundenplan-Kommentar zur passenden Zeilenposition (Wochentag, n-te Zeile am Tag) – nur an Werktagen ohne Feiertag; wird **nicht** gespeichert (für späteren Excel-Export vorgesehen).

---

## Export nach Excel und Zwischenablage

- **Empfohlen:** Verwenden Sie die Schaltfläche **„Für Excel kopieren“** in der Werkzeugleiste. So landen **alle Tage des Monats** in der Zwischenablage in der **vorgesehenen Spaltenfolge** (laut `cell_spec` in `config.toml`) – unabhängig davon, welche Spalten in der Tabelle gerade sichtbar oder ausgeblendet sind. Anschließend in der Tabellenkalkulation **einfügen** (üblicherweise **Strg+V**).
- **Strg+C** in der Tabelle kopiert nur den **aktuell markierten Zellbereich** wie in der Ansicht; Spaltenauswahl und Format entsprechen **nicht** dem Excel-Export. Nutzen Sie Strg+C höchstens für kurze Auszüge – für den Monats-Export sollten Sie **immer „Für Excel kopieren“** verwenden.
- Der Button **„Für Excel kopieren“** legt **immer tab-getrennten Text (TSV)** in die Zwischenablage; optional zusätzlich **Excel-XML** (`spreadsheet_xml_formatierung` in `config.toml`). **Leere exportierte Zellen** (ohne `"blank"`) werden im TSV als `**" "`** (Leerzeichen) ausgegeben – Calc und Excel überschreiben damit bestehende Inhalte an diesen Positionen beim Einfügen.

### LibreOffice / OpenOffice Calc

Calc liest das Excel-Zwischenablageformat (**XML Spreadsheet**) beim Einfügen **nicht**; es wird der **TSV** verwendet  (`spreadsheet_xml_formatierung = false`). Durch die `" "`**-Platzhalter** in leeren Spalten müssen Sie den Zielbereich **nicht mehr vorher löschen**: Markieren Sie die obere linke Zelle des Monatsblocks und fügen Sie mit **Strg+V** ein.

Spalten mit **Formeln** in Ihrer Calc-Datei (z. B. Geleistet/Soll, in `config.toml` als `"blank"` markiert) erscheinen im TSV **ohne** Wert und werden beim Einfügen **nicht** überschrieben – Ihre Formeln bleiben erhalten.

### Microsoft Excel

Bei **Microsoft Excel** kann zusätzlich **XML Spreadsheet** genutzt werden (`spreadsheet_xml_formatierung = true`): Dann bleiben `"blank"`-Spalten per `ss:Index` unangetastet (Formeln erhalten). Der TSV-Teil der Zwischenablage verhält sich wie in Calc (leere Felder als `" "`). Ein vorheriges Löschen des Bereichs ist in der Regel **nicht** nötig; nur wenn nach dem Einfügen noch unerwartete Restwerte stehen, Zielbereich leeren und erneut einfügen.

---

## Reiter und ungespeicherte Änderungen

- Das Programm hat mehrere **Reiter** (Zeiteinträge, Stundenplan, Urlaub, …). Beim **Wechsel** von einem Reiter zu einem anderen werden **ungespeicherte Änderungen** im bisherigen Reiter verworfen, sofern Sie das in der Abfrage bestätigen. Wechseln Sie also zuerst zurück und speichern, wenn etwas erhalten bleiben soll.
- Beim **Schließen** des Fensters mit ungespeicherten Änderungen erscheint ebenfalls eine Abfrage.

---

## Statuszeile und Summen

- **Unten links** erscheinen kurze **Hinweise** (z. B. nach dem Speichern oder Kopieren). Die Meldung verschwindet nach einiger Zeit von selbst.
- **Unten rechts** sehen Sie **Summen** für die geleistete Zeit sowie die Sollwerte nach Stundenplan und nach Vertrag für den **aktuell angezeigten Monat** (über alle sichtbaren Zeilen).

