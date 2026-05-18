# Tests – Tätigkeitsbericht

Diese Dokumentation beschreibt die Test-Suite unter `test/`. Die Struktur folgt der Schichtenarchitektur von `src/` (Core / External), damit Unit-, Integrations- und Präsentationstests klar getrennt bleiben.

## Schnellstart

```powershell
# Einmalig: Entwicklungsabhängigkeiten
pip install -r requirements-dev.txt

# Alle Tests
py -m pytest test/

# Mit Kurzbericht und fehlgeschlagenen Details
py -m pytest test/ -ra

# Einzelne Schicht
py -m pytest test/core/
py -m pytest test/external/

# Eine Datei oder ein Test
py -m pytest test/core/application/test_zeiteintrag_dto_kommentar.py -k urlaub
```

Konfiguration: Projektroot `pytest.ini` (`pythonpath = src .`, `testpaths = test`).

## Verzeichnisstruktur

```
test/
├── README_tests.md          ← diese Datei
├── conftest.py              ← gemeinsamer pytest-Einstieg (optional erweiterbar)
├── support/                 ← Hilfen, keine Testfälle
│   ├── db.py                ← In-Memory-SQLite-Engine und Session-Fixture
│   ├── fakes.py             ← In-Memory-Repositories, dto_anwendung()-Factory
│   └── factories.py         ← Zeiteintrag, DTO, Urlaub, Feiertag, …
├── core/
│   ├── domain/              ← Modelle, Domain-Services (ohne DB, ohne Qt)
│   └── application/         ← Anwendungslogik (DTO, Kommentar, Soll/Geleistet)
└── external/
    ├── infrastructure/
    │   └── repositories/    ← SQLModel + SQLite :memory:
    └── presentation/
        └── desktop/         ← reine Python-Hilfen (ohne Event-Loop)
```

### Prinzipien

| Regel | Bedeutung |
|--------|-----------|
| **Spiegelung von `src/`** | `test/core/…` testet `src/Core/…`, `test/external/…` testet `src/External/…`. |
| **`support/` ist kein Test** | Nur Fixtures, Fakes und Factories – pytest sammelt dort keine `test_*.py`. |
| **Kein Mischmasch** | Domain-Logik nicht in Repository-Tests; Qt nicht in Domain-Tests. |
| **Schnelle Tests zuerst** | Die meisten Fälle laufen ohne GUI und ohne echte Datei-DB. |

## Abhängigkeiten (`requirements-dev.txt`)

| Paket | Zweck |
|--------|--------|
| **pytest** | Test-Runner, Fixtures, Parametrisierung |
| **pytest-mock** | `mocker`-Fixture (bei Bedarf für gezieltes Mocking) |
| **pytest-cov** | Abdeckungsberichte (`py -m pytest test/ --cov=src --cov-report=term-missing`) |
| **pytest-qt** | Vorbereitet für PySide6-GUI-Tests (Marker `qt`, siehe unten) |

Laufzeitabhängigkeiten kommen aus `requirements.txt` (u. a. sqlmodel, PySide6).

## `support/` – gemeinsame Hilfen

### `db.py`

- **`sqlite_engine`** – leere In-Memory-Datenbank, alle Tabellen aus `External.Infrastructure.sqlmodel_tables`.
- **`db_session`** – SQLModel-`Session` pro Test (Isolation zwischen Tests).

Verwendung in `test/external/infrastructure/` (über `conftest.py` re-exportiert).

### `fakes.py`

- **`InMemoryZeiteintragRepository`** – vollständiges In-Memory-Repository für `ZeiteintragService`.
- **`dto_anwendung(...)`** – baut `ZeiteintragAnwendungDTO` mit konfigurierbaren Listen (Urlaub, Krank, Feiertage, Stundenplan, …) und Standard-Vertragssoll (Mo–Fr 8:00).

Ideal für Application-Tests ohne SQLite und ohne Qt.

### `factories.py`

Kurzfabriken für wiederkehrende Domain-Objekte (`zeiteintrag`, `zeiteintrags_dto`, `urlaub`, `krank`, `feiertag`, `stundenplan_montag`).

## Was wo getestet wird

### `test/core/domain/`

| Datei | Inhalt |
|--------|--------|
| `test_models_worktime.py` | Pydantic-Validierung (`Zeiteintrag`, `ZeiteintragsDTO`, `Urlaubsantrag`, `Krankmeldung`) |
| `test_zeiteintrag_service.py` | Speichern, Überschneidungsprüfung am selben Tag |
| `test_feiertag_service.py` | Nur ein Feiertag pro Datum |

**Typ:** Unit-Tests, Millisekunden, keine Datenbank.

### `test/core/application/`

| Datei | Inhalt |
|--------|--------|
| `test_zeiteintrag_anwendung.py` | Stundenplan ↔ Wochentag beim Erfassen |
| `test_zeiteintrag_dto_kommentar.py` | Urlaub/Krank (Kürzel/Präfix), Ü-Frei, Feiertagsname, Wochenende |
| `test_zeiteintrag_dto_geleistet.py` | Netto-Arbeitszeit, Soll-Parsing, Urlaub-Geleistet, `liste_im_monat` |

**Typ:** Unit-Tests mit `dto_anwendung()` aus `support/fakes.py`.  
**Fixture:** `dto_app` in `conftest.py`.

### `test/external/infrastructure/repositories/`

| Datei | Inhalt |
|--------|--------|
| `test_zeiteintrag_sqlmodel_repository.py` | save, list nach Jahr/Monat, delete_by_id |
| `test_feiertag_sqlmodel_repository.py` | FeiertagService + SQLModel-Repository |

**Typ:** Integrationstests gegen **SQLite In-Memory** (`support/db.py`).

### `test/external/presentation/desktop/`

| Datei | Inhalt |
|--------|--------|
| `test_arbeitszeit_berechnung.py` | `parse_uhrzeit_minuten`, `netto_arbeitsminuten`, … |
| `test_zeiteintrag_excel_clipboard.py` | Excel-Serialzahlen, TSV, SpreadsheetML `ss:Index` für blank-Spalten |

**Typ:** Unit-Tests **ohne** `QApplication` – nur reine Funktionen.

## PySide6 / GUI (optional, vorbereitet)

Aktuell gibt es **keine** Fenster- oder ViewModel-Tests mit Event-Loop. Dafür ist vorgesehen:

- Paket **pytest-qt** in `requirements-dev.txt`
- Marker in `pytest.ini`: `qt`

Beispiel für spätere Erweiterung:

```python
import pytest

@pytest.mark.qt
def test_beispiel(qtbot):
  ...
```

Neue GUI-Tests gehören nach `test/external/presentation/desktop/` und sollten sparsam sein (kritische Signale/Dialoge), während Logik in ViewModels/Application bleibt und dort getestet wird.

## Neue Tests anlegen

1. **Schicht wählen** – Domain, Application, Infrastructure oder Presentation.
2. **Dateiname** – `test_<modul>.py` im passenden Unterordner.
3. **Hilfen nutzen** – `factories` / `dto_anwendung` / `db_session` statt Copy-Paste.
4. **Importe** – Module aus `src` wie in der App: `from Core.…`, `from External.…`; Hilfen: `from test.support.…`.

### Beispiel Application-Test

```python
from datetime import date, time
from test.support.factories import zeiteintrags_dto, urlaub
from test.support.fakes import dto_anwendung

def test_mein_fall():
    montag = date(2025, 3, 10)
    app = dto_anwendung(urlaub=[urlaub(montag, montag)])
    dto = zeiteintrags_dto(datum=montag, uhrzeit_von=time(8, 0), uhrzeit_bis=time(12, 0))
    app.anreichere_eintraege_fuer_tag([dto])
    assert dto.anmerkung == "U"
```

### Beispiel Repository-Test

```python
from datetime import date, time
from Core.Domain.models.models_worktime import Zeiteintrag
from External.Infrastructure.repositories.zeiteintrag_sqlmodel_repository import SqlZeiteintragRepository

def test_mein_fall(db_session):
    repo = SqlZeiteintragRepository(db_session)
    repo.save(Zeiteintrag(datum=date(2025, 1, 1), uhrzeit_von=time(8, 0), uhrzeit_bis=time(12, 0)))
    assert len(repo.get_by_datum(date(2025, 1, 1))) == 1
```

## Abdeckung und CI

```powershell
py -m pytest test/ --cov=src --cov-report=html
```

HTML-Bericht liegt danach unter `htmlcov/`. Für CI reicht oft:

```powershell
py -m pytest test/ --cov=src --cov-report=term-missing --cov-fail-under=0
```

(`--cov-fail-under` nach Bedarf erhöhen, wenn die Suite wächst.)

## Was bewusst nicht in `test/` liegt

- Keine Tests gegen die produktive `taetigkeitsbericht.db` (nur In-Memory-SQLite).
- Keine API-Import-Tests für Feiertage (`FeiertagService.lade_feiertage_aus_api`) – Netzwerk wäre flaky.
- Keine `__pycache__`- oder `.pytest_cache`-Dateien im Repo (in `.gitignore`).

## Kurz-Checkliste für gute Tests

- [ ] Liegt die Datei in der richtigen Schicht unter `test/`?
- [ ] Nutzt der Test `support/` statt duplizierter Setup-Logik?
- [ ] Ist der Test ohne GUI lauffähig, wenn es keine UI-Frage ist?
- [ ] Prüft ein Repository-Test echte SQL-Pfade (In-Memory)?
- [ ] Ist der Testname beschreibend (`test_urlaub_ohne_arbeitszeit_nur_kuerzel`)?

---

*Stand: Suite mit 36 Tests – Domain, Application, SQLModel-Repositories und Desktop-Hilfsfunktionen.*
