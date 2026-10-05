# Leerkrachten Tool - Atheneum Tungrorum

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2.17](https://img.shields.io/badge/django-5.2.17-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Leerkrachten Tool** is een modulair webportaal voor leerkrachten om **leerlingenevaluaties** te beheren. Ontwikkeld voor **Atheneum Tungrorum**, maar inzetbaar voor elke school.

---

##  Features

-  **Gebruikersbeheer**: Persoonlijke accounts per leerkracht met admin-rechten
-  **Schoolstructuur**: Schooljaren, studierichtingen, klassen, vakken en leerlingen
-  **Leerplandoelen**: BK's (Basiscompetenties) met subdoelen per studierichting en graad
-  **Lessen & Evaluaties**: Doelen slepen, scores invoeren (0/20/40/60/80/Afwezig)
-  **Automatische berekeningen**: Totalen, gemiddelden, afwezigheden
-  **Excel-export**: Klasoverzicht en individuele leerlingrapporten (A4-formaat)
-  **Backups**: Lokale SQLite-backups met herstelfunctionaliteit
-  **Multi-user**: Scheiding tussen leerkrachten, admin kan inzage beperken
-  **Desktop-modus**: Optioneel WebView2-venster voor Windows

---

##  Snelle Start (Lokaal)

###  Vereisten
- Python 3.12+
- Git (optioneel)

###  Installatie (Windows)

1. **Kloon de repository** (of download als ZIP):
   ```bash
   git clone https://github.com/Grossardtim/Toolbox-Leerkrachten.git
   cd Toolbox-Leerkrachten
   ```

2. **Maak een virtual environment aan**:
   ```bash
   python -m venv .venv
   ```

3. **Activeer de virtual environment**:
   ```bash
   .\.venv\Scripts\activate
   ```

4. **Installeer dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Initialiseer de database**:
   ```bash
   python manage.py migrate
   ```

6. **Maak demo-gegevens aan** (optioneel, alleen voor ontwikkeling):
   ```bash
   python manage.py create_demo
   ```
   *Opmerking: Demo-gegevens bevatten fictieve leerlingen. Gebruik dit niet voor echte data!*

7. **Start de ontwikkelserver**:
   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```

8. **Open in browser**:
   Ga naar [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

###  Installatie (Mac/Linux)

Volg dezelfde stappen als Windows, maar gebruik:
```bash
# Virtual environment activeren
source .venv/bin/activate

# Server starten
python manage.py runserver 127.0.0.1:8000
```

---

##  Gebruikershandleiding

Voor gedetailleerde instructies, zie:
- [docs/LEESMIJ.md](docs/LEESMIJ.md) (Nederlandstalige handleiding)
- [docs/INSTALLATIE-ANDERE-COMPUTER.md](docs/INSTALLATIE-ANDERE-COMPUTER.md) (Installatie op andere computers)

---

##  Inloggegevens (Demo)

Na het uitvoeren van `create_demo`:
- **Demo-leerkracht**: `demo.leerkracht` (wachtwoord: zie `data/demo-toegang.txt`)
- **Admin**: `beheerder` (wachtwoord: afspreken met beheerder)

---

##  Startscripts

Het project bevat handige startscripts:

| Script | Platform | Actie |
|--------|----------|-------|
| `Start-tool.bat` | Windows | Start server + opent browser |
| `start-mac.sh` | Mac/Linux | Start server |
| `Build-exe.bat` | Windows | Bouw Windows-executable |

---

##  Project Structuur

```
Toolbox-Leerkrachten/
├── accounts/               # Gebruikersbeheer (Django app)
├── evaluations/            # Evaluaties, lessen, doelen (Django app)
├── exports/                # Excel-export (Django app)
├── schoolportal/           # Hoofd Django project
│   ├── settings.py         # Configuratie
│   ├── urls.py             # URL routing
│   └── releases.py         # Versiegeschiedenis
├── templates/              # HTML sjablonen
├── static/                 # CSS, JS, afbeeldingen
├── docs/                   # Documentatie
│   ├── LEESMIJ.md          # Nederlandstalige handleiding
│   ├── COMPILEREN.md       # Bouwinstructies
│   └── ...
├── tools/                  # Hulpscripts
├── requirements.txt        # Python dependencies
└── manage.py               # Django management
```

---

##  Bijdragen

1. Fork de repository
2. Maak een feature branch (`git checkout -b feature/naam`)
3. Commit je wijzigingen (`git commit -m 'Voeg functie toe'`)
4. Push naar de branch (`git push origin feature/naam`)
5. Open een Pull Request

---

##  Licentie

Dit project is gelicenseerd onder de **MIT Licentie** - zie [LICENSE](LICENSE) voor details.

---

##  Contact

Voor vragen over dit project, neem contact op met de beheerder.

---

**Versie**: 1.2.001 (5 oktober 2026) | **Django**: 5.2.17 | **Python**: 3.12+
