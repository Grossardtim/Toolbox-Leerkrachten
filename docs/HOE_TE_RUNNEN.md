# Hoe Run Je het Project Lokaal? 

Dit document leg je **stap voor stap** uit hoe je **Leerkrachten Tool** op je eigen computer kunt laten draaien.

---

##  Snelle Samenvatting (voor gevorderden)

```bash
# 1. Virtual environment maken
python -m venv .venv

# 2. Activeren (Windows)
.\.venv\Scripts\activate

# 2. Activeren (Mac/Linux)
source .venv/bin/activate

# 3. Dependencies installeren
pip install -r requirements.txt

# 4. Database initialiseren
python manage.py migrate

# 5. Demo-gegevens maken (optioneel)
python manage.py create_demo

# 6. Server starten
python manage.py runserver 127.0.0.1:8000
```

Open daarna [http://127.0.0.1:8000](http://127.0.0.1:8000) in je browser.

---

##  Gedetailleerde Stappen (Windows)

###  Stap 1: Python Installeren

1. Download **Python 3.12** van [python.org](https://www.python.org/downloads/)
2. **Belangrijk**: Zet een vinkje bij **"Add Python to PATH"** tijdens installatie!
3. Open **Command Prompt** (cmd) en test of Python geinstalleerd is:
   ```bash
   python --version
   ```
   Je zou iets als `Python 3.12.x` moeten zien.

---

###  Stap 2: Project Downloaden

**Optie A: Met Git (aanbevolen)**
1. Installeer [Git](https://git-scm.com/downloads) als je dat nog niet hebt
2. Open Command Prompt en navigeer naar waar je het project wilt opslaan:
   ```bash
   cd C:\Users\timgr\OneDrive\Bureaublad\Evaluaties
   ```
3. Kloon de repository:
   ```bash
   git clone https://github.com/Grossardtim/Toolbox-Leerkrachten.git
   cd Toolbox-Leerkrachten
   ```

**Optie B: Zonder Git (ZIP-bestand)**
1. Ga naar [GitHub](https://github.com/Grossardtim/Toolbox-Leerkrachten)
2. Klik op **Code → Download ZIP**
3. Pak het ZIP-bestand uit in `C:\Users\timgr\OneDrive\Bureaublad\Evaluaties`
4. Open Command Prompt en navigeer naar de map:
   ```bash
   cd C:\Users\timgr\OneDrive\Bureaublad\Evaluaties\Toolbox-Leerkrachten
   ```

---

###  Stap 3: Virtual Environment Maken

Een virtual environment zorgt ervoor dat de Python-pakketten voor dit project **gescheiden** blijven van andere projecten.

```bash
python -m venv .venv
```

Je ziet nu een map `.venv` in je project verschijnen.

---

###  Stap 4: Virtual Environment Activeren

```bash
.\.venv\Scripts\activate
```

Je weet dat het gelukt is als je in je Command Prompt **`(.venv)`** voor je pad ziet staan:
```
(.venv) C:\Users\timgr\OneDrive\Bureaublad\Evaluaties\Toolbox-Leerkrachten>
```

---

###  Stap 5: Dependencies Installeren

De dependencies (benodigde Python-pakketten) staan in `requirements.txt`.

```bash
pip install -r requirements.txt
```

Dit installeert:
- Django 5.2.17 (het webframework)
- psycopg (voor PostgreSQL-ondersteuning)
- waitress (webserver)
- XlsxWriter (voor Excel-export)

---

###  Stap 6: Database Initialiseren

Django gebruikt een **SQLite-database** (een bestand op je computer).

```bash
python manage.py migrate
```

Dit maakt alle benodigde tabellen aan.

---

###  Stap 7: Demo-Gegevens Maken (Optioneel)

Als je **testgegevens** wilt (fictieve leerkrachten, klassen, leerlingen):
```bash
python manage.py create_demo
```

**Belangrijk**: Deze demo-gegevens zijn **alleen voor testen**! Gebruik ze niet voor echte leerlingdata.

De inloggegevens voor de demo staan in:
- `data/demo-toegang.txt` (in je projectmap)

---

###  Stap 8: Server Starten

```bash
python manage.py runserver 127.0.0.1:8000
```

Je ziet nu:
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
October 5, 2026 - 23:30:00
Django version 5.2.17, using settings 'schoolportal.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-C.
```

---

###  Stap 9: Open in Browser

Open je browser en ga naar:
🔗 [http://127.0.0.1:8000](http://127.0.0.1:8000)

Je ziet nu het **inlogscherm** van Leerkrachten Tool!

---

##  Inloggen

###  Demo-Accounts (na `create_demo`)
| Gebruikersnaam | Wachtwoord | Rol |
|----------------|------------|-----|
| `demo.leerkracht` | Zie `data/demo-toegang.txt` | Leerkracht (met fictieve klasgegevens) |
| `beheerder` | Afspreken met beheerder | Admin (ziet alles) |

###  Eigen Account Maken

Als je **geen demo** hebt gemaakt, kun je een admin-account aanmaken:
```bash
python manage.py createsuperuser
```

Volg de instructies om een gebruikersnaam en wachtwoord in te voeren.

---

##  Startscripts (Eenvoudiger!)

Het project bevat **handige batch-bestanden** zodat je niet alles handmatig hoeft te doen:

| Bestandsnaam | Wat het doet | Platform |
|--------------|--------------|----------|
| `Start-tool.bat` | Start de server + opent automatisch de browser | Windows |
| `start-mac.sh` | Start de server | Mac/Linux |
| `Build-exe.bat` | Bouw een Windows-executable | Windows |

###  Gebruik van Start-tool.bat (Aanbevolen voor Windows)

1. Dubbelklik op **`Start-tool.bat`** in de projectmap
2. Het script:
   - Start de Django-server
   - Wacht tot de server klaar is
   - Opent automatisch [http://127.0.0.1:8000](http://127.0.0.1:8000) in je standaardbrowser

**Voordelen**:
- Geen Command Prompt nodig
- Geen handmatige commando's
- Automatische browseropening

---

##  Server Stoppen

Om de server te stoppen:
1. Ga terug naar het **Command Prompt-venster** waar de server draait
2. Druk op **`CTRL + C`** (Control + C)
3. Bevestig met **`Y`** (Yes) als gevraagd

---

##  Veelvoorkomende Problemen & Oplossingen

###  Probleem: "Python is not recognized"
**Oorzaak**: Python staat niet in je PATH.
**Oplossing**:
1. Herinstalleer Python en **zet een vinkje bij "Add Python to PATH"**
2. Of voeg Python handmatig toe aan je PATH:
   - Ga naar **Systeeminstellingen → Geavanceerd → Omgevingsvariabelen**
   - Zoek `Path` onder **Systeemvariabelen**
   - Klik op **Bewerken** en voeg toe: `C:\Python312\` en `C:\Python312\Scripts\`

---

###  Probleem: "ModuleNotFoundError: No module named 'django'"
**Oorzaak**: Je hebt de dependencies niet geinstalleerd of de virtual environment niet geactiveerd.
**Oplossing**:
1. Zorg dat je in de projectmap bent:
   ```bash
   cd C:\Users\timgr\OneDrive\Bureaublad\Evaluaties\Toolbox-Leerkrachten
   ```
2. Activeer de virtual environment:
   ```bash
   .\.venv\Scripts\activate
   ```
3. Installeer de dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

###  Probleem: "Port 8000 is already in use"
**Oorzaak**: Er draait al een applicatie op poort 8000.
**Oplossing**:
1. Stop de andere applicatie (als je weet welke)
2. OF gebruik een andere poort:
   ```bash
   python manage.py runserver 127.0.0.1:8001
   ```
   Open dan [http://127.0.0.1:8001](http://127.0.0.1:8001)

---

###  Probleem: "Database does not exist"
**Oorzaak**: Je hebt `migrate` niet uitgevoerd.
**Oplossing**:
```bash
python manage.py migrate
```

---

###  Probleem: "No such file or directory: 'data/schoolportal.sqlite3'"
**Oorzaak**: De `data/` map bestaat niet.
**Oplossing**:
1. Maak de map aan:
   ```bash
   mkdir data
   ```
2. Voer migraties uit:
   ```bash
   python manage.py migrate
   ```

---

##  Tips voor Gebruik

###  1. Altijd Virtual Environment Gebruiken
- **Nooit** `pip install` doen zonder de virtual environment geactiveerd te hebben!
- Dit zorgt voor conflicts tussen projecten.

###  2. Wijzigingen Opslaan
- **Django-server moet draaien** om wijzigingen in de applicatie te zien.
- **Sla altijd op** voordat je de server herstart.

###  3. Demo-Gegevens Verwijderen
Als je **echte data** wilt gebruiken, verwijder dan eerst de demo:
```bash
# Verwijder de database (LET OP: dit verwijdert ALLE data!)
rm data/schoolportal.sqlite3

# Maak een nieuwe database
python manage.py migrate

# Maak een admin-account
python manage.py createsuperuser
```

###  4. Backups Maken
Je kunt een backup maken van je database:
```bash
python manage.py backup_local --output backups
```

Dit maakt een backup in de `backups/` map.

---

##  Mac/Linux Instructies

De stappen zijn bijna hetzelfde als voor Windows, met kleine verschillen:

###  Virtual Environment Activeren
```bash
source .venv/bin/activate
```

###  Startscript Gebruiken
```bash
sh start-mac.sh
```

###  Bestandsrechten
Als je een fout krijgt over **rechten**, voer dan uit:
```bash
chmod +x start-mac.sh
```

---

##  Samenvatting: Commando's Overzicht

| Actie | Commando |
|-------|----------|
| Virtual environment maken | `python -m venv .venv` |
| Virtual environment activeren (Windows) | `.\.venv\Scripts\activate` |
| Virtual environment activeren (Mac/Linux) | `source .venv/bin/activate` |
| Dependencies installeren | `pip install -r requirements.txt` |
| Database initialiseren | `python manage.py migrate` |
| Demo-gegevens maken | `python manage.py create_demo` |
| Server starten | `python manage.py runserver 127.0.0.1:8000` |
| Admin-account maken | `python manage.py createsuperuser` |
| Backup maken | `python manage.py backup_local --output backups` |
| Server stoppen | `CTRL + C` |

---

##  Veel Succes!

Als je **vragen** hebt of **problemen** tegenkomt, laat het dan weten!

**Belangrijk**: Gebruik de **demo-gegevens alleen voor testen**. Voor echte leerlingdata, maak een **nieuwe database** aan en gebruik **`createsuperuser`**.
