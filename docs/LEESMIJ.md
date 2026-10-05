# Leerkrachten Tool · Atheneum Tungrorum

Eerste lokale versie van een modulair leerkrachtenportaal. De leerlingenevaluaties werken met persoonlijke accounts, eigen gegevens per leerkracht en schooljaar, klasbeheer, vakken, doelen, lessen, scores en feedback. Het schoollogo is opgenomen in het portaal, de aanmelding en het accountbeheer.

## Nu uitproberen op deze computer

Open **http://127.0.0.1:8000** zolang de ontwikkelserver draait.

Het account `demo.leerkracht` bevat fictieve klasgegevens; de lokale demotoegang staat in `data/demo-toegang.txt`. Het admin-account heet `beheerder`. Het adminwachtwoord is op verzoek gewijzigd; gebruik het afgesproken wachtwoord uit de chat. In nieuwe demo-installaties worden willekeurige wachtwoorden gegenereerd. De beheerder ziet alle gegevens. Per leerkracht kan de beheerder instellen wiens inhoud zichtbaar is.

Dubbelklik in de projectmap op **Start-tool.bat** (of op `start-windows.cmd`). Het script start de lokale server, wacht tot die klaar is en opent automatisch http://127.0.0.1:8000/ in je standaardbrowser. Laat het terminalvenster open. Met Ctrl+C stop je de server. Als de tool al draait, opent het script alleen de website. Een andere toepassing op poort 8000 wordt niet afgesloten. De startbestanden installeren niets en laden geen demo-inhoud. Op Mac/Linux: `sh start-mac.sh`. Je kunt optioneel `--port 8001` of `--no-browser` meegeven. De gedeelde opstartlogica staat in `tools/start_local.py`.

Het demo-account bevat fictieve leerlingen. Andere accounts kunnen eigen ingevoerde gegevens bevatten. De bestaande Excel-bronbestanden zijn niet gewijzigd of automatisch geïmporteerd.

## Werkwijze

1. Kies je actieve account in de keuzelijst op de inlogpagina en voer het wachtwoord in. De beheerder opent **Leerkrachten & toegang** om accounts toe te voegen of te wijzigen. Zet **Leerlingenevaluaties** aan en ken naar wens **Excel-export** toe. Deactiveer accounts om toegang te stoppen zonder gegevens te verwijderen. Een vergeten wachtwoord kan de beheerder via deze accountpagina opnieuw instellen; er wordt nog geen herstelmail verstuurd. Gewone leerkrachten kunnen dit beheer niet openen en kunnen geen beheerdersrechten krijgen via dit formulier.
2. De leerkracht gaat naar **Beheer** en maakt een schooljaar aan.
3. Maak unieke studierichtingen aan. Voeg per schooljaar vakken toe en koppel ze aan studierichtingen. Maak klassen met studierichting en leerjaar en selecteer hun vakken. Meerdere klassen per richting en schooljaar zijn mogelijk.
4. Voeg leerlingen toe aan een klas. Zet een leerling op inactief wanneer die niet meer in nieuwe lessen moet verschijnen.
5. Maak leerplandoelstellingen voor een studierichting en graad en voer één evaluatiepunt per regel in. Doelen zijn herbruikbaar over schooljaren en vakken. 1e graad = leerjaar 1–2, 2e graad = 3–4, 3e graad = 5–7. Een les biedt doelen aan die bij de richting en graad van de klas passen.
6. Ga naar **Lessen & evaluaties**, kies het schooljaar en maak een les aan voor een klas en vak.
7. Sleep doelen naar het evaluatievlak of gebruik **Toevoegen**. Versleep het handvat bij een doel in de puntenmatrix, of gebruik de pijlen in diezelfde doelbalk. Volgorde, scores en feedback worden samen opgeslagen.
8. Vul scores en feedback in en klik op **Scores & feedback opslaan**. Totalen en gemiddelden veranderen direct tijdens invoer; opslaan blijft nodig om de scores te bewaren. Sla invoer op voordat je doelen toevoegt of verwijdert. Verplaatsen binnen de puntenmatrix mag ook terwijl je scores invult.
9. Open de les later opnieuw om verder te werken. Leerkrachten zien standaard alle gegevens, tenzij de beheerder de inzage beperkt. Evaluaties van anderen zijn alleen-lezen.

Alle evaluatiepunten tellen even zwaar. Je kunt 0, 20, 40, 60 of 80 kiezen, of de status **Afwezig**. Een lege beoordeling betekent nog niet beoordeeld. **0 telt mee** in totalen en gemiddelden; **Afwezig en leeg tellen niet mee**. Het aantal afwezigheden wordt apart vermeld. Per leerling tonen totalen behaalde/mogelijke punten, met 80 mogelijke punten per ingevuld cijfer. Het aantal beoordeelde punten staat per leerling in de matrix. Het klasgemiddelde blijft beschikbaar; de kaart met klastotaal is verwijderd. Een gemiddelde kan bijvoorbeeld 53,3 zijn. Er vindt geen automatische omrekening naar 100 plaats. Het klasgemiddelde gebruikt alle ingevulde scores, ook als leerlingen een verschillend aantal scores hebben.

Lessen bewaren een eigen kopie van de leerlingnamen, doelen en punten. Een wijziging in Beheer verandert nieuwe lessen, maar herschrijft geen bestaande les. Het achteraf aanvullen van de leerlingenlijst van een bestaande les is in deze versie nog niet beschikbaar.

## Overzichten en filters

Beheer, lesoverzichten, leerkrachtenbeheer, exportselecties en klasresultaten hebben zoek- en sorteermogelijkheden. Klik op een kolomtitel voor oplopend/aflopend sorteren. Combineer de filters onder de kolomtitels. Het algemene zoekveld is verwijderd. Status en toegangsrechten hebben een exacte keuzelijst.

Zonder schooljaar-, klas- of tekstfilter blijven alle eigen ingaven zichtbaar, ook uit oudere schooljaren en ook inactieve of gearchiveerde beheerrecords. Er is geen verborgen beperking tot de eerste resultaten. **Alle schooljaren** verwijdert de jaarbeperking; **Alle filters wissen** bovenaan verwijdert ook de klasselectie. **Filters wissen** bij een tabel herstelt die volledige tabel binnen de gekozen context. Andere leerkrachten blijven afgeschermd.

Klassen en leerlingen staan samen onder **Beheer → Klassen & leerlingen**. Klik bij een klas op **Leerlingen** of kies een klas in de leerlingenlijst. Een nieuwe leerling krijgt die klas vooraf ingevuld.

Bij Excel-export verschijnt de leerlingkeuze uitsluitend onder **Individuele leerling** als deze optie is geselecteerd. Filters in de lessenlijst wijzigen de aangevinkte lessen niet; selecties blijven behouden.

**Leerplandoelen → Import voorbereiden** beschrijft de toekomstige importstappen. Upload en documentherkenning zijn nog niet actief: eerst is een officieel voorbeeldbestand nodig. Daarna volgen documentherkenning, een controlevoorbeeld, controles op dubbele doelcodes en expliciete bevestiging. Bestaande leskopieën worden niet overschreven.

## Opbouw voor verdere ontwikkeling

- `schoolportal/`: configuratie en centrale routes.
- `accounts/`: gebruikers, toegang en aanmeldbeveiliging.
- `evaluations/`: onderwijsgegevens, formulieren, evaluaties en berekeningslogica.
- `exports/`: selectie, privacyfiltering en download van Excel-puntenlijsten.
- `exports/workbook.py`: zelfstandige Excel-opbouw met XlsxWriter.
- `exports_engine/`: historische referentie; niet nodig voor de toepassing of executable.
- `templates/` en `static/`: Nederlandstalige interface en schoolstijl.
- `accounts/migrations/` en `evaluations/migrations/`: versieerbare databasewijzigingen.
- `data/`: lokale ontwikkelgegevens en de lokale geheime sleutel; niet opnemen in versiebeheer.
- `prompt.txt`: functionele specificatie en zichtbare voorlopige keuzes.
- `voortgang.md`: status en uitgevoerde controles.

Excel-export is beschikbaar. PDF, afdrukken, klantendiensten en stages zijn toekomstige onderdelen. Voeg nieuwe onderdelen als eigen Django-apps toe en breid de toegangscontrole expliciet uit. Er zijn nu afzonderlijke toegangsinstellingen voor Leerlingenevaluaties en Excel-export. Export vereist ook evaluatietoegang. Er is nog geen algemeen plugin-installatiesysteem.

## Excel-export

Open **Excel-export** in de zijbalk, of **Exporteren naar Excel** bij een les. Kies eerst het soort export, daarna schooljaar, klas, eventueel vak en periode, en vervolgens de gevonden lessen. Je kunt maximaal 100 lessen per bestand exporteren.

- **Klasoverzicht:** leerlingen naast elkaar, één tabblad per les, een overzicht over de selectie en een feedbackblad.
- **Individuele leerling:** alleen de gekozen leerling, met diens eigen scores en persoonlijke feedback. De gegevens van andere leerlingen worden niet in het bestand opgenomen, ook niet op verborgen tabbladen. Klasfeedback en klasgemiddelden worden weggelaten. Een les zonder inschrijving van deze leerling wordt overgeslagen.

De puntenlijsten gebruiken de indeling van het voorbeeld: doelen/evaluatiepunten in rijen, leerlingen in kolommen, totalen en gemiddelden onder de onderdelen. Het logo en de schoolkleur worden meegenomen. Formules bevatten ook berekende resultaten, zodat punten meteen zichtbaar zijn. Excel gebruikt zijn eigen taalinstellingen voor decimale tekens. Nul telt mee; leeg en Afwezig niet. Wijzigingen in Excel worden niet teruggeschreven naar het portaal.

Persoonlijke feedback wordt letterlijk overgenomen. Schrijf daarin alleen informatie die bestemd is voor de betrokken leerling.

Excel-export gebruikt XlsxWriter, opgenomen in `requirements.txt` en de Windows-executable. Node.js en Codex zijn niet nodig. De server bouwt de download in het geheugen op en levert die met `no-store`; er is geen openbare downloadmap.

De aanmelding gebruikt gehashte wachtwoorden, CSRF-bescherming en een beperking tot vijf mislukte aanmeldpogingen per accountnaam per kwartier. Eigenaarschap en moduletoegang worden bij iedere beschermde aanvraag op de server gecontroleerd. Lesformulieren hebben een revisienummer om verouderde wijzigingen te weigeren. Na een conflict blijft de ingediende invoer zichtbaar, zodat je die met de actuele versie kunt vergelijken.

## Op een andere computer

Zie [INSTALLATIE-ANDERE-COMPUTER.md](INSTALLATIE-ANDERE-COMPUTER.md) voor Windows, Mac en het meenemen van gegevens. Zie [COMPILEREN.md](COMPILEREN.md) om zelf één Windows-executable te bouwen; een gebouwde versie staat in `dist/Leerkrachtenportaal.exe`.

## Nieuwe lokale installatie (Python 3.12)

Windows, in PowerShell vanuit deze map:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py create_demo
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Mac/Linux, in Terminal vanuit deze map:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py create_demo
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

`create_demo` is uitsluitend voor een lege ontwikkelomgeving. Het weigert bestaande accounts te overschrijven. Voor een lege installatie zonder demo gebruik je `manage.py createsuperuser` in plaats van `create_demo`.

## Gegevens behouden bij updates

De programmacode en de database zijn gescheiden. Overschrijf of verwijder `data/` nooit bij een update. Je kunt met de omgevingsvariabele `DATA_DIR` een andere gegevensmap aanwijzen. De huidige bronmap staat onder OneDrive: gebruik de database hier uitsluitend als lokale demo met één actieve instantie, niet als gedeelde database via synchronisatie.

Voor elke update van een gevulde omgeving:

1. Maak en controleer een back-up. Test de migratie eerst in een afzonderlijke testdatabase.
2. Werk de code en afhankelijkheden bij.
3. Voer `manage.py migrate` uit; verwijder bestaande migraties niet en gebruik geen database-reset.
4. Controleer aanmelding, rechten, bestaande lessen, scores en feedback.
5. Bewaar de vorige codeversie en een gedocumenteerd herstelplan. Houd bij herstel rekening met invoer die sinds de back-up is toegevoegd.

Lokale SQLite-back-up:

```powershell
.\.venv\Scripts\python.exe manage.py backup_local --output backups
```

Dit commando gebruikt de SQLite-back-upfunctie voor een consistente kopie. Om lokaal terug te zetten: stop eerst alle app-processen, bewaar de huidige database apart, plaats de gewenste kopie terug als `data/schoolportal.sqlite3` en start de passende codeversie. Laat in productie herstel door de verantwoordelijke beheerder uitvoeren. Een kopie maken is op zichzelf geen bewijs dat herstel werkt.

Automatische productieback-ups, een bewaarschema, herstel tot een gekozen tijdstip en monitoring moeten nog worden ingericht bij de gekozen hostingpartij. Geen systeem kan absoluut nul risico op dataverlies garanderen.

## Hosting voor meerdere leerkrachten

Iedereen kan dezelfde webtoepassing gebruiken via een browser op Windows, Mac of andere systemen. Daarvoor is nodig:

- Eén hostingomgeving met een Python-applicatieserver en HTTPS-webadres.
- Een centrale PostgreSQL-database met beperkte toegang en back-ups.
- Een afzonderlijke testomgeving en een beheerder voor updates, herstel en accounts.

Een gedeelde Google Drive-map voert geen Python-server uit. Gebruik Drive eventueel later voor exports of afgeschermde back-upbestanden, niet voor een actief databasebestand dat door meerdere computers wordt geopend. Toegang tot Drive geeft bovendien geen toegang tot dit portaal: dat regelt het persoonlijke account.

Productie vereist minimaal `APP_ENV=production`, een sterke `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` en passend `PGSSLMODE`. Gebruik een echte WSGI-applicatieserver en een HTTPS-proxy; gebruik Django `runserver` niet voor productie. Stel de proxyconfiguratie en HTTPS-detectie volgens de gekozen infrastructuur in. Voer `collectstatic` en `check --deploy` uit. Configureer geheimen buiten de repository. De productieconfiguratie weigert zonder PostgreSQL of SECRET_KEY te starten.

De hosting en een productie-uitrol zijn nog niet gerealiseerd. De bestaande schoolaccounts, Google-aanmelding en Google Drive zijn niet gekoppeld.

## Controles

```powershell
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

De tests gebruiken een aparte tijdelijke database. Ze controleren onder andere scheiding tussen leerkrachten, intrekken van toegang, geldige scores, ontbrekende invoer, gelijke weging, historiek, feedback, revisieconflicten en CSRF. De automatische tests draaien lokaal op SQLite; productiegebruik met PostgreSQL en de browsers op Mac vraagt nog controle in die omgeving.

## Vaste bediening in de evaluatie

De rechterkolom blijft op brede schermen zichtbaar tijdens het scrollen. Bovenaan
staat **Scores & feedback opslaan**. Langere doelenlijsten kun je binnen die kolom
apart scrollen. Op smalle schermen staat de opslagknop in een vaste onderbalk.
De verticale leerlingnamen blijven boven de puntenmatrix zichtbaar wanneer je
binnen die matrix scrolt. De linkerkolom met omschrijvingen blijft ook vaststaan.
De ingelogde gebruiker, Wachtwoord en Afmelden staan nu onderaan de menukolom.

## Klassen selecteren en ingaven wissen

Klik op het keuzerondje, de klasnaam of de klasrij. De gekozen klas wordt gemarkeerd
en de pagina toont meteen de bijbehorende leerlingen. Je kunt ook een andere klas
of Alle klassen kiezen; zonder filters blijven alle eigen ingaven beschikbaar.

De actieskolom bevat **Wissen**. Je krijgt eerst een bevestigingspagina met de
naam en gevolgen. Alleen bevestigen wist de ingave. Verouderde bevestigingen en
gekoppelde gegevens blokkeren de wisactie. Schooljaren, vakken en klassen met
onderliggende gegevens moet je eerst leegmaken; een gebruikte klas kan ook worden
gearchiveerd. Een leerling met lesinschrijvingen kun je op inactief zetten.

Een les wissen verwijdert ook haar scores, lesdoelen en feedback, maar behoudt
de basisgegevens. Een beheerdoel wissen laat de kopieën in eerdere lessen intact.
Alleen de beheerder kan lege leerkrachtenaccounts wissen; accounts met gegevens
kunnen worden gedeactiveerd. Het admin-account zelf is beschermd.

## Gebruikersfeedback verwerkt

Schooljaren zijn uniek per leerkracht; studierichtingen zijn eveneens uniek per
leerkracht en worden over schooljaren hergebruikt. Klassen, leerlingeninschrijvingen
en vakken blijven aan het juiste schooljaar verbonden. Klassen selecteren alleen
vakken van hun studierichting. Migraties 0004/0005 nemen bestaande richtingsnamen
en klas-vakkoppelingen over zonder scores of leskopieën te wijzigen.

In een les kun je per doel **Verberg lege rijen** aanvinken. Alleen rijen die voor
alle leerlingen leeg zijn verdwijnen uit beeld. Nul en Afwezig blijven zichtbaar.
Dit is een weergavefilter: de velden blijven onderdeel van het opslagformulier.
Kleur 80 is felblauw, de andere scoreniveaus zijn duidelijker en doelen zijn fuchsia.

Excel laat rijen zonder cijfers weg. Voor een individuele leerling wordt uitsluitend
diens eigen score bekeken; 0 blijft opgenomen. Afwezig-only en lege rijen vervallen.
Lege doelgroepen vervallen mee. Totalen zijn ook in Excel behaald/mogelijk.
Het aantal afwezigheden in Excel betreft uitsluitend de opgenomen rijen.

Bij één les is de bestandsnaam:
- Klas: Schooljaar - Klas - Vak - Lesonderwerp - Datum les.xlsx
- Leerling: Schooljaar - Klas - Vak - Leerling - Lesonderwerp - Datum les.xlsx

Bij meerdere lessen wordt het onderwerp vervangen door het aantal lessen, met
een datumperiode. Verschillende vakken krijgen het label Meerdere vakken.
Ongeldige bestandsnaamtekens worden vervangen en lange onderdelen ingekort.
Het exportscherm bevat geen les-wisactie; wissen blijft mogelijk in het lesoverzicht.
Smartschool en centrale hosting wachten op overleg met de beheerder.

## Doelen per studierichting en graad

Migratie 0006 behoudt doel-ID’s, evaluatiepunten en leskopieën. De oude context wordt bewaard bij het doel. Bij een onduidelijke oorspronkelijke richting moet de leerkracht de richting in Beheer aanvullen. Doelen zonder volledige koppeling worden niet aangeboden bij een nieuwe les.

In Evaluaties bevat de lijst met beschikbare doelen geen **Wissen** meer. Een doel uit de huidige les verwijderen blijft mogelijk. Het brondoel verwijderen gebeurt uitsluitend in Beheer.


## Nieuwe functies (5 oktober 2026)

- **Instellingen**: persoonlijke UI-kleuren met kleurenkiezers. Scorekleuren blijven vast.
- **Doelenoverzicht**: filter op schooljaar, studierichting, klas en graad. Subdoelen staan verticaal, leerlingen horizontaal. Een vinkje betekent dat er een cijfer is; ook 0 telt. Leeg en Afwezig geven geen vinkje. De kleur volgt het gemiddelde, naar beneden afgerond naar 0/20/40/60/80. Excel-export is beschikbaar.
- Lege evaluatierijen zijn standaard ingeklapt; gebruik het driehoekje om ze te tonen. Menu en doelenkolom kunnen worden ingeklapt. De knop ⛶ schakelt browserfullscreen in; automatisch starten in een native appvenster is niet ingebouwd.
- **Beheerder / Back-ups**: download een databaseback-up of sla die op in een absoluut pad op de servercomputer. Terugzetten vraagt een upload, controle, bevestiging en het huidige adminwachtwoord. Er wordt eerst een veiligheidskopie gemaakt; daarna wordt iedereen afgemeld. Stop andere instanties die dezelfde database gebruiken. Terugzetten ondersteunt SQLite met dezelfde databasemigraties; PostgreSQL-back-ups verlopen via de hostingbeheerder.
- **Wijzigingslogboek**: registreert actor en belangrijke wijzigingen; dit is geen systeem voor het afzonderlijk ongedaan maken van iedere wijziging.
- De nieuwe exe heet na een volgende build **LeerkrachtenTool.exe**. De bestaande gegevensmap **Leerkrachtenportaal** blijft behouden. Deze aanpassingen zijn nog niet gecompileerd.


## Scherm- en exportupdate, 5 oktober 2026

Tool-administratie staat onder **Instellingen** en wordt door alle leerkrachten gedeeld. Je mag elkaars administratieve gegevens aanpassen; de oorspronkelijke maker blijft geregistreerd en de wijziging wordt op jouw naam gelogd. Bestaande gelijknamige records zijn niet automatisch samengevoegd. Lesresultaten zijn alleen bewerkbaar door de maker en de admin. De beheerder kan eventuele beperkingen op lesinzage blijven instellen; die beperken de gedeelde administratie niet.

De Excel-puntenlijsten gebruiken nu A4 liggend, één pagina breed, herhaalde tabelkoppen, echte kop- en voetteksten, verticale namen, tabelranden en scorekleuren. Kop-/voetteksten zijn zichtbaar in Excel bij Pagina-indeling of Afdrukvoorbeeld. Ze zijn niet als extra cellen boven de tabel opgenomen.

**Start-app.bat** opent de bronversie in een eigen Windows-venster met WebView2. Installeer daarvoor op de ontwikkelcomputer de bouwafhankelijkheden via `.venv\Scripts\python.exe -m pip install -r requirements-build.txt`. Dit venster gebruikt dezelfde projectmap `data` als Start-tool.bat. Sluit een eerdere instantie met deze data eerst. Start-tool.bat blijft de browserroute.

Na een volgende build opent **LeerkrachtenTool.exe** standaard het appvenster zonder console. De exe blijft de bestaande externe gegevensmap gebruiken. Met `--browser` kun je de gewone browser blijven gebruiken. Windows vereist de Microsoft Edge WebView2-runtime. Sluiten via X of **Tool afsluiten** stopt de lokale server. De afsluitknop vraagt eerst bevestiging; sla wijzigingen vooraf op. Centrale hosting heeft deze afsluitknop niet. Er is lokaal geen afzonderlijke SQL-server: SQLite bewaart alles in één databasebestand.

Deze update is niet gecompileerd. De bouwconfiguratie is voorbereid; de bestaande exe bevat de nieuwe wijzigingen nog niet.


## Desktopwerkplek — versie 1.1.000

De laatste schermherwerking vervangt de drie kolommen van Evaluaties. De puntenmatrix gebruikt de volledige werkbreedte. Via de vaste actiebalk wissel je tussen **Punten**, **Feedback** en **Klasresultaten**. Invoer blijft staan bij het wisselen; opslaan blijft nodig. De knop **Leerplandoelen** opent een breed venster met leesbare subdoelen en aparte tabbladen voor toevoegen en geselecteerde doelen. Alleen het werkgebied scrolt; navigatie, titel, actiebalk en statusbalk blijven vast staan.

Onder **Administratie > Softwarewijzigingen** ziet de admin het softwarelogboek. **Gegevenswijzigingen** blijft het afzonderlijke logboek van gebruikershandelingen. Versies staan in de navigatie en onderaan de tool: `x.x.000` bij een functie-update, `.001` enzovoort bij een bugfix. De centrale versiebron is `schoolportal/releases.py`; projectafspraken voor verdere updates staan in `AGENTS.md`.


## Leerplannen en lesselectie (1.2.000)
Open in een les **Leerplandoelen toevoegen**. Vink het hele leerplan aan, een volledige BK of afzonderlijke subdoelen. Voeg de selectie in één keer toe. Bestaande punten/scoren worden behouden. Een BK zonder subdoelen krijgt zijn eigen omschrijving als beoordelingsrij. Via **Lege rijen tonen** worden nieuwe, nog niet beoordeelde rijen zichtbaar. Sla lopende scores eerst op voordat je de lesselectie wijzigt.

Het doelenoverzicht combineert de zichtbare lessen en vakken. Een BK krijgt een vinkje als elk actueel subdoel minstens één cijfer heeft. Een nul telt mee; leeg en Afwezig niet. Dit betekent aangereikt en geëvalueerd, niet automatisch geslaagd. De totalen zijn op 100; invoerscores en gemiddelden blijven op 80.

De AppData-map blijft dezelfde. Een toekomstige nieuwe executable maakt vóór noodzakelijke migraties automatisch een back-up in de submap `backups`. Sluit de vorige instantie voordat je met dezelfde gegevens een nieuwe versie start. De migratie is op een kopie van de bestaande database getest; de originele AppData-database is nog niet gemigreerd.

De uitgebreide fictieve demo staat apart in `outputs/demo-1.2`. Start deze met `.venv\Scripts\python.exe desktop.py --data-dir outputs/demo-1.2 --port 8002 --browser`; de inloggegevens staan in de demo-map in `demo-toegang.txt`. Gebruik deze gegevens niet als echte leerlingadministratie.
