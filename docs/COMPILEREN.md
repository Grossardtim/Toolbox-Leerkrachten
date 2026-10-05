# Windows-executable bouwen en gebruiken

De gebouwde toepassing staat in `dist/LeerkrachtenTool.exe`.
Kopieer dit bestand naar een lokale map op een Windows-computer en dubbelklik.
Python, Node.js en Codex zijn op de ontvangende computer niet nodig, ook niet
voor Excel-export. De eerste start kan even duren terwijl het programma uitpakt.
De toepassing opent automatisch in een eigen gemaximaliseerd Windows-venster. Sluit via X of de knop Tool afsluiten. Met --browser opent ze in je gewone browser.

Bij een lege installatie maak je eerst zelf een beheerdersaccount aan.
Daarna voeg je via **Leerkrachten & toegang** accounts en moduletoegang toe.
De executable bevat geen bestaande accounts, wachtwoorden of leerlinggegevens.

## Zelf opnieuw compileren

Sla je werk op en sluit de bestaande Leerkrachten Tool volledig af vóór het
bouwen. Alleen een browsertabblad sluiten stopt de lokale server niet.
Het script controleert vooraf of de executable vervangen kan worden. Bij
`WinError 5` kan de oude executable nog actief zijn (ook op de achtergrond).
Controleer dit in Taakbeheer. Stop een proces pas nadat je werk is opgeslagen.

Op de bouwcomputer is Python 3.12 nodig. Dubbelklik in de hoofdmap op
**Build-exe.bat**. Dit installeert de bouwpakketten (internet vereist) en maakt
opnieuw `dist/LeerkrachtenTool.exe`. De bestaande ontwikkelgegevens blijven
in `data` staan. De gebouwde executable is voor Windows; een Mac-versie moet
op een Mac worden gebouwd. De Mac-build is hier niet getest.

## Gegevens en updates

De executable bewaart gegevens standaard in
`%LOCALAPPDATA%\Leerkrachtenportaal`, buiten het programma. Een nieuwe exe
vervangt die map niet. Bij een databasewijziging maakt de toepassing vóór de
migratie automatisch een SQLite-back-up in de submap `backups`.
Bewaar daarnaast regelmatig een externe back-up van de gegevensmap.

Om de huidige projectgegevens mee te nemen: stop beide servers, maak een
back-up en kopieer `data/schoolportal.sqlite3` en `data/.secret` naar de lege
gegevensmap van de executable. Bestaande accounts en wachtwoorden blijven
dan gelden. Overschrijf geen andere gevulde installatie.

Je kunt een eigen lokale gegevensmap of andere poort kiezen vanuit PowerShell:

```powershell
.\LeerkrachtenTool.exe --data-dir "C:\MijnPortaalData" --port 8001
```

Start met fictieve demo-inhoud in een nieuwe gegevensmap:

```powershell
.\LeerkrachtenTool.exe --data-dir "C:\PortaalDemo" --demo
```

De willekeurige demowachtwoorden staan dan in `demo-toegang.txt` in die map.
`--demo` overschrijft geen bestaande accounts. `--no-browser` onderdrukt het
automatisch openen. `--check` controleert database, pagina en Excel zonder
een server te starten.

Dit is een lokale toepassing op `http://127.0.0.1:8000/`. De ontwikkelserver en
executable kunnen niet tegelijk dezelfde poort gebruiken; stop de ene of kies
8001 voor de andere. Gebruik geen actieve gegevensmap via gedeelde
Google Drive/OneDrive-synchronisatie. Gedeeld gebruik door meerdere computers
vraagt nog centrale hosting.

De Windows-build is lokaal gecontroleerd. Een afzonderlijke schone computer
en een Mac zijn nog niet getest. De executable is niet digitaal ondertekend;
Windows kan daarom bij een eerste start een melding tonen.

De appmodus gebruikt pywebview 6.2.1 en Microsoft Edge WebView2. WebView2 moet op de ontvangende Windows-computer aanwezig zijn. De build maakt een venstertoepassing zonder console. Opstartfouten verschijnen in een melding. Er is in deze wijzigingsronde niet gecompileerd.
