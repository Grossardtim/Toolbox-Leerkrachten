# De demo op een andere computer

Deze stappen starten een eigen lokale kopie in de browser. De gegevens op beide
computers worden niet automatisch gedeeld. Centrale hosting bespreken we later
met de beheerder; Smartschool blijft voorlopig geparkeerd.

## Snelste manier op Windows

Kopieer `dist/LeerkrachtenTool.exe` naar de andere Windows-computer en dubbelklik. De browser opent automatisch. Bij een lege installatie stel je eerst een beheerdersaccount in. Er is geen Python-, Node.js- of Codex-installatie nodig. Zie [COMPILEREN.md](COMPILEREN.md) voor de gegevensmap, demo-optie, updates en het meenemen van bestaande gegevens.

De volgende stappen zijn het alternatief vanuit de broncode, ook voor Mac.

## 1. Project kopiëren

Stop de server op de oorspronkelijke computer met Ctrl+C en kopieer de projectmap
`Bronbestanden` naar een gewone lokale map op de andere computer. Neem alle
programmamappen, `manage.py`, `requirements.txt`, `static`, `templates` en de
startbestanden mee.

- Neem `data` mee als je dezelfde accounts, wachtwoorden, klassen en evaluaties
  wilt behouden. Neem ook het verborgen bestand `data/.secret` mee.
- Laat `.venv`, `exports_engine/node_modules`, `__pycache__` en `outputs` weg.
  De Python-omgeving moet op de andere computer opnieuw aangemaakt worden.
  De bestaande `node_modules` is een verwijzing naar deze computer, geen zelfstandig pakket.
- Voor uitsluitend fictieve demogegevens: maak een nieuwe projectkopie zonder
  `data`. Wis de bestaande gegevensmap op deze computer niet.

## 2. Windows: eenmalig installeren

Installeer Python 3.12 en open PowerShell in de gekopieerde projectmap
(de map met `manage.py`). Voer uit:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
```

Als `py` niet beschikbaar is, gebruik het pad naar de geïnstalleerde Python 3.12
in de eerste opdracht. Voor de pakketinstallatie is internet nodig.

Alleen voor een lege kopie zonder bestaande accounts:

```powershell
.\.venv\Scripts\python.exe manage.py create_demo
```

De nieuwe willekeurige wachtwoorden staan dan in `data/demo-toegang.txt`.
Bij een meegenomen gegevensmap blijven de bestaande wachtwoorden gelden;
voer `create_demo` dan niet uit.

Dubbelklik daarna op **Start-tool.bat**. De server start en de browser opent
`http://127.0.0.1:8000/`. Laat het servervenster open; Ctrl+C stopt de tool.

## 3. Mac: eenmalig installeren

Installeer Python 3.12 en open Terminal in de gekopieerde projectmap:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
```

Alleen bij een lege kopie: `.venv/bin/python manage.py create_demo`.
Start vervolgens met `sh start-mac.sh`.

## Excel-export

De Python-installatie bevat via `requirements.txt` ook XlsxWriter. De Windows-executable neemt dit mee. Er zijn geen aanvullende exportpakketten uit Codex nodig. Een afzonderlijke andere computer en Mac zijn hier nog niet getest.

## Bestaande gegevens en updates

Bewaar een extra kopie van `data` vóór een update. Overschrijf deze map niet met
een lege demo. Na bijgewerkte code voer je opnieuw `manage.py migrate` uit met
de Python uit `.venv`.

Gebruik geen gedeelde actieve SQLite-database via Google Drive of OneDrive.
Voor gelijktijdig gebruik met gedeelde gegevens is één centrale server nodig.
