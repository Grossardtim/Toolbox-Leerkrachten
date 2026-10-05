# Voortgang leerkrachtenportaal

Dit bestand wordt tijdens de bouw bijgewerkt. De toepassing wordt eerst lokaal getest met fictieve gegevens.

| Onderdeel | Status |
|---|---|
| Eisen en schoollogo | Verwerkt |
| Django-project en duurzame opslag | Lokaal werkend; PostgreSQL-configuratie voor latere hosting |
| Persoonlijke accounts en adminbeheer | Gebouwd en getest |
| Schooljaren, klassen, leerlingen, vakken en doelen | Gebouwd en getest |
| Lessen, doelen selecteren/slepen, scores en feedback | Gebouwd; preview geopend |
| Berekeningen en bescherming tegen overschrijven | Getest |
| 0 en afzonderlijke status Afwezig | Toegevoegd en getest |
| Leerjaar naast schooljaar, met doelenselectie per vak | Toegevoegd en getest |
| Tests en visuele controle | 26 automatische tests geslaagd; login, beheer en evaluatieformulier bekeken |
| Lokale preview en startinstructies | Beschikbaar; zie LEESMIJ.md en start-windows.cmd |
| Excel-export per klas en leerling | Gebouwd; echte .xlsx-bestanden en privacy gecontroleerd |
| Gebruikerskeuzelijst bij aanmelden | Toegevoegd; alleen actieve accounts |
| Leerkrachtenbeheer in hoofdportaal | Toegevoegd voor de overkoepelende admin |

Hosting en ingebruikname met echte leerlinggegevens volgen na de lokale beoordeling.

## Gecontroleerd

- Scores, feedback en instellingen opslaan en heropenen.
- Scheiding tussen leerkrachten, ingetrokken rechten en inactieve accounts.
- 0 telt als score; Afwezig en leeg tellen niet mee in gemiddelden.
- Doelen van het verkeerde leerjaar worden niet aangeboden en servermatig geweigerd.
- Gelijke weging per evaluatiepunt en geen dubbele doeltoekenning.
- Revisieconflicten, onvolledige formulieren, CSRF en ongeldige scores.
- Back-upcommando en herstel in een afzonderlijke tijdelijke testdatabase.
- De migratie naar leerjaren en afwezigheden behield beide bestaande lessen,
  alle 7 toen aanwezige scores, 8 lesinschrijvingen, 2 lesdoelen en 4 lespunten.
- Django-systeemcontrole en controle op ontbrekende migraties geslaagd.
- In een aparte browserproefles gecontroleerd: doel toevoegen, doel slepen,
  0 en Afwezig opslaan, herladen en correcte resultaten terugzien.
  Score 0 bleef gemiddelde 0; Afwezig werd afzonderlijk geteld.
- 44 automatische tests geslaagd na toevoegen van exports en accountbeheer.
- Individuele Excel-export gecontroleerd in alle XML-onderdelen: geen namen,
  scores of feedback van medeleerlingen, geen klasfeedback of verborgen gegevens.
- Excel-formules bewaren hun berekende waarden; 0 en Afwezig blijven onderscheiden.
- Beide exportvarianten visueel gecontroleerd met overzicht, lesbladen en feedback.
- Aanmelding met de aangepaste adminreferenties bevestigd; gebruikerskeuzelijst
  bevat alleen actieve accounts. Leerkrachtenbeheer is alleen toegankelijk voor admin.

## Nog buiten de lokale oplevering

- Productiehosting, automatische productieback-ups en operationeel beheer.
- Testen met PostgreSQL en op een echte Mac.
- Afdrukken, PDF, Google-koppelingen en toekomstige planningmodules.

De demo bevat een aparte les 'Demo · controle opslaan' voor browsercontroles.
De oorspronkelijke Excel-bronbestanden blijven ongewijzigd.

## Aanpassingen overzichten en bediening (4 oktober 2026)

- Overzichten hebben sorteren en combineerbare filters op inhoudelijke velden.
- Zonder filters zijn alle eigen schooljaren/records zichtbaar, inclusief
  gearchiveerde klassen en inactieve leerlingen. Andere accounts blijven afgeschermd.
- Klassen en leerlingen delen één scherm met gekoppelde selectie en toevoegen.
- Importingang en voorbereidingsscherm toegevoegd. Upload/parser wachten op het
  officiële voorbeeldbestand; er wordt nog geen document geïmporteerd.
- Exportleerlingkeuze staat onder individueel rapport en is alleen dan zichtbaar.
- Doelgroepen in de puntenmatrix zijn versleepbaar en hebben ook pijlen.
  Volgorde en scores worden samen opgeslagen met revisiecontrole.
- Extra witruimte, afzonderlijk algemeen totaal en klasgemiddelde, compacte
  doorzoekbare doelenlijst, kleurrijkere secties en duidelijkere navigatie.
- Start-tool.bat en bestaande startbestanden gebruiken tools/start_local.py:
  server starten, gereedheid afwachten, browser openen, bestaande server herkennen.

Validatie: 49 Django-tests en 3 tests voor het startscript geslaagd.
Browser: filteren, sorteren, leeg resultaat, alle filters wissen, conditionele
leerlingkeuze, importvoorbereiding, werkelijk slepen en bewaren/heropenen bevestigd.
Demo-doelvolgorde na controle teruggezet; scores/feedback ongewijzigd behouden.
Startscript met echte lokale server getest, .bat hergebruikt de bestaande server.
Browser-open-aanroep en bezette-poortafhandeling ook automatisch getest.
Preview op http://127.0.0.1:8000/ herstart met de actuele code.

## Aanvullende UI-controle

De navigatie is verbreed tot 284 px met modulekaarten en accountacties onderaan.
De evaluatie heeft een sticky rechterkolom met apart scrollbare inhoud en een
vast zichtbare opslagknop die het volledige evaluatieformulier verstuurt.
Leerlingnamen staan verticaal in sticky kolomkoppen. In de browser gecontroleerd:
headerpositie bleef gelijk bij matrixscroll van 250 px naar 0; rechterkolom bleef
op 22 px van de schermbovenkant terwijl het middenveld naar beneden scrolde.
Na deze templatewijzigingen slagen ook de 8 relevante pagina-, opslag- en accounttests.

## Klasselectie en wissen (4 oktober 2026)

- Iedere klasrij heeft een selectierondje en aanklikbare naam; klikken op de rij
  toont meteen de leerlingen van die klas. De gekozen klas krijgt een markering.
- Wisacties toegevoegd aan beheer-, les-, export- en accountlijsten, en aan de
  lijst met beschikbare doelen. Bestaande verwijderactie voor lesdoelen blijft.
- Bevestigingspagina met impact, ondertekende actuele gegevens, CSRF, rechten-
  controle, transacties en auditregistratie. GET verwijdert nooit gegevens.
- Afhankelijke gegevens blokkeren wissen van ouders en gebruikte leerlingen.
  Les verwijderen wist haar beoordelingen; beheerdoel verwijderen bewaart snapshots.
- 58 automatische applicatietests geslaagd, waaronder 9 nieuwe tests voor
  selectie, verwijderen, eigenaarschap, adminbescherming, stale forms en CSRF.
- Browsercontrole bevestigt klasselectie, automatische leerlingenweergave en
  bescherming van een leerling met bestaande lesinschrijvingen.
- Werkelijk verwijderen uitsluitend in tijdelijke testdatabases uitgevoerd;
  bestaande gebruikersgegevens en demo-ingaven niet gewist.


## Feedback demogebruiker en overdracht (4 oktober 2026)

- Unieke studierichtingen, klasrelatie en vak-richtingkoppelingen toegevoegd.
  Bestaande richtingsteksten blijven bewaard; twee migraties vullen de relaties.
- Databaseback-up vooraf. Read-only vergelijking: alle oorspronkelijke velden
  en records in 13 onderwijstabellen identiek gebleven.
- Beoordeelde punten per leerling, totalen X/Y met noemer 80 per cijfer,
  filter lege rijen per doel zonder invoer te wissen, klastotaalkaart verwijderd.
- Sterkere kleuren, felblauw voor 80, fuchsia voor doelen; algemene zoekvelden weg.
- Exportselectie in drie tegels; leerlingkeuze conditioneel; les-wisactie weg.
- Puntenlijsten met nieuwe bestandsnamen, numeriek beoordeelde rijen en privacy-
  filtering. Excel-formules berekenen totalen X/Y en gewogen gemiddelden.
- 64 Django-tests geslaagd. Aanvullend systeemcheck en migratiecheck geslaagd.
- Browser bevestigt lege-rijfilter met behoud van alle scorevelden en ongewijzigde
  opslagstatus, persoonlijke totalen, kolomfilters, exportkeuzes en nieuwe structuur.
- Demo-klasexport en individuele export gegenereerd, formuleresultaten onafhankelijk
  gecontroleerd en gewijzigde werkbladen visueel nagekeken. Geen echte scores gewijzigd.
- INSTALLATIE-ANDERE-COMPUTER.md toegevoegd. Python-omgeving opnieuw opbouwen;
  bestaande data optioneel meenemen. Excel-engine nog geen zelfstandig installatiepakket.
- Smartschool en hosting geparkeerd voor overleg met de beheerder.

## Graad, richting en Windows-executable (4 oktober 2026)

- Leerplandoelen horen nu bij studierichting en graad, onafhankelijk van vak en schooljaar.
  Leerjaar 1–2: graad 1; 3–4: graad 2; 5–7: graad 3.
- Migratie 0006 bewaart de oorspronkelijke context en behoudt doel-ID's en leskopieën.
  Back-up vooraf in data/backups/voor-doelen-graad. Migratie op een geïsoleerde
  kopie gecontroleerd: historische lessen, scores, feedback en leerlingen identiek.
  De live database bevat ook gebruikerswijzigingen sinds de back-up (nieuwe lessen,
  één scorewijziging en leerlingstatus); daarom is deze niet bytegelijk aan de back-up.
- Wissen van brondoelen verwijderd uit de beschikbare doelenlijst in Evaluaties.
  Beheer houdt de wisactie; verwijderen van een doel uit de les blijft beschikbaar.
- 72 Django-tests geslaagd; migratiecheck zonder ontbrekende migraties.
- Excel-engine vervangen door zelfstandig mee te leveren XlsxWriter. Klassexport
  en individuele puntenlijst gegenereerd en visueel gecontroleerd. Tests controleren
  privacyfiltering, formules, opgeslagen uitkomsten en scorevalidatie.
- Build-exe.bat, PyInstaller-specificatie, desktop.py en COMPILEREN.md toegevoegd.
  Gebouwde Windows-executable in dist. Geen leerlinggegevens meegebundeld.
  Aparte gegevensmap, lokale eerste beheerder en automatische back-up vóór migraties.
- Executable getest met afzonderlijke demodatabase: opstart, migraties, aanmelding,
  pagina's en volledige Excel-download geslaagd. Geen Python/Node/Codex-aanroep nodig.
  Een schone andere computer en Mac-build zijn nog niet getest.
- Browsercontrole bevestigt richting/graad en ontbreken van de bron-wisactie.
  Screenshot: preview-evaluaties-graad.png. Ontwikkelpreview herstart op poort 8000.
- prompt.txt en installatiehandleidingen bijgewerkt.

## Kleuren en gegroepeerde lesdoelen (4 oktober 2026)

- Blauw menu, neutraal werkvlak en fuchsia rechterkolom; compactere Lesgegevens.
- Grotere doelcodes en titels naast elkaar in matrix en geselecteerde doeltegels.
- Gelijke titels vormen één weergavegroep, met vetgedrukte BK-code per subdoel.
  Groepen behouden alle doel- en score-ID's. Verplaatsen werkt voor de volledige
  groep; verwijderen uit de les blijft per onderliggend doel mogelijk.
- Twee regressietests voor groepering, nulscore, totalen en bewaren van de volgorde;
  samen met vijf tests voor doelbeschikbaarheid geslaagd.
  Ook de 30 bestaande evaluatietests zijn geslaagd: 37 tests gecontroleerd.
- Browsercontrole met afzonderlijke fictieve database: groep verplaatst en opgeslagen,
  alle 28 scorevelden behouden. Screenshot preview-gegroepeerde-doelen.png.
- Niet gecompileerd. De bestaande executable op poort 8000 is ongewijzigd.
  Broncode-preview met de projectgegevens gestart op poort 8003.


## Afgerond op 5 oktober 2026
- Laatste gebruiksfeedback geïntegreerd: compacte beheerknoppen/kolomfilters, doelinvoer, inklapbare navigatie en kolommen, persoonlijke UI-kleuren, live totalen, standaard verborgen lege rijen, branding Leerkrachten Tool.
- Doelenoverzicht per subdoel/leerling met filters, scorecategorie en Excel-export.
- Gedeelde inzage instelbaar door admin; server blokkeert wijzigen van andermans evaluaties. Admin ziet alles. Back-up/herstel en wijzigingslogboek toegevoegd.
- Beide migraties toegepast na veiligheidskopie. Geen echte inhoud vervangen of samengevoegd.
- Eindcontrole: 78 Django-tests OK; migratiecontrole geen wijzigingen; JavaScript-syntaxcontrole OK. Herstelworkflow afzonderlijk geslaagd op tijdelijke database.
- Browsercontrole op geïsoleerde demo: score 60 naar 80 verandert onmiddellijk totaal 300/400 naar 320/400 en gemiddelde 60 naar 64. Zonder opslaan teruggezet. Lege rijen standaard ingeklapt; doelinvoer eindigt op 756px binnen 1080px viewport.
- Screenshot: outputs/evaluaties-eindcontrole.png. Bronpreview opnieuw gestart op 8003. Bestaande executable op 8000 ongemoeid gelaten.
- prompt.txt en handleidingen bijgewerkt. NIET gecompileerd. Volledig scherm via browserknop; automatische native vensterstart blijft niet geïmplementeerd. Back-upherstel beperkt tot compatibele SQLite-databases.


## Versie 1.1.000 — desktopherwerking, 5 oktober 2026
- Algemene desktopcontrole uitgebreid naar alle gedeelde schermcomponenten, aanmelden, start, beheerformulieren, export en instellingen. Vaste titelzone met afzonderlijk scrollend werkgebied; rijacties horizontaal en exportkeuzes compact.
- Eerdere drie-kolomslay-out vervangen: volledige matrixbreedte, vaste actiebalk, brede doelkiezer en tabbladen Punten/Feedback/Klasresultaten. Alleen het centrale werkgebied scrolt. Compactere desktopstijl over de hele tool.
- Herbruikbare SVG-lijnicoontjes, grotere gecentreerde inlogtitel, Tool-beheerder, compactere bediening, thematische acties en leerlingkoppen.
- Catalogus gedeeld en bewerkbaar door iedere ingelogde leerkracht; maker behouden en daadwerkelijke editor gelogd. Maker/admin mogen lessen wijzigen; derden alleen lezen binnen ingestelde lesinzage. Export van lessen van andere makers in gedeelde klas gecorrigeerd.
- Klas- en lesexport: A4 liggend, één pagina breed, herhaalde tabelkoppen, echte kop-/voetteksten, logo op fysieke headergrootte, borders, banding, verticale naamstijlen, kleurcategorieën op gemiddelde/totalen. Feedbackhoogte berekend met complete vervolgrijen. Werkbladrenderer gecontroleerd; echte Excel-afdrukvoorbeeldweergave is hier niet beschikbaar.
- Pywebview 6.2.1 geïnstalleerd in projectomgeving. Verborgen WebView2-venster geladen en afgesloten (PASS). Afsluitworkflow HTTP getest met tijdelijke kopie van fictieve QA-database: proces sluit met code 0.
- Softwarelogboek voor admin op /beheerder/versies/, afzonderlijk van gegevenslogboek. Centrale releasebron schoolportal/releases.py en zichtbare versie 1.1.000. AGENTS.md schrijft verdere registratie/versionering voor.
- Volledige testreeks: 83 tests geslaagd. JavaScript-syntax OK; geen migraties nodig. Extra gerichte controles na de exportopmaak geslaagd.
- Browsercontrole op 1280x720: matrix gebruikt volledige beschikbare 1020px, hoofdvenster blijft scrollY=0 terwijl matrix scrollTop=265 bereikt. Tabwissel behoudt niet-opgeslagen score. Brede doelkiezer toont lange subdoelen leesbaar.
- prompt.txt en handleidingen aangevuld. Start-app.bat gebruikt projectdata en poort 8003. Geen echte gegevens overschreven of records samengevoegd. Geen executable gecompileerd.


## Versie 1.2.000 — leerplanselectie en BK-opvolging
- Leerplan = BK-catalogus per studierichting/graad. Volledige selectie, meerdere BK's of losse subdoelen in breed lesvenster; aanvullen behoudt bestaande snapshots/scores.
- BK zonder subdoelen gebruikt eigen omschrijving als beoordelingsrij. BK-overzicht en Excel tonen volledigheid over zichtbare lessen/vakken; alle subdoelen vereist, 0 geldig, leeg/Afwezig uitgesloten.
- Migratie 0008 voegt stabiele bronkoppeling en directe-BK-vlag toe. Ongewijzigde subdoelen behouden identiteit bij herordenen. Gewijzigde/verwijderde subdoelen blijven in historische lessen bewaard; geen onzekere automatische koppeling.
- Verwijderen in BK-hoofding met bevestiging, duidelijke lege-rijenknop, gelijke compacte volgordeknoppen, witte tabelkop, acties bij titel en tabbladen onder lesgegevens. Scoreregels-tab verwijderd.
- Totalen UI en Excel numeriek op 100; gemiddelden blijven op 80. Excelformules en gecachte resultaten gecontroleerd (0 en 80 = 50/100; afwezig uitgesloten).
- 89 tests in volledige reeks geslaagd; aanvullende Excel-normalisatietest geslaagd (90 in totaal). JavaScript-syntax, Django check en migratieconsistentie OK.
- Browser: demoles met 19 leerlingen en 58 rijen; twee losse subdoelen toegevoegd, bestaande scores behouden. Full-HD: buitenvenster scrollt niet. Kleine schermen gebruiken horizontale scroll met vaste doelomschrijvingen.
- Afzonderlijke outputs/demo-1.2 met 6 extra klassen van 19, 36 extra BK's, 24 extra lessen en 6 extra vakken. Geen voorbeelddata in echte AppData ingevoerd.
- AppData-migratie getest op tijdelijke kopie: alle bestaande account/evaluatievelden exact gelijk, 74 lespunten gekoppeld, 0 onzekere koppelingen, integrity_check OK. Kopieën opgeruimd. Origineel niet gemigreerd.
- Bronpreview data-map na automatische voor-updateback-up gemigreerd; oude executable op 8000 blijft ongewijzigd. Nieuwe bronpreview 8003; fictieve demo 8002. Niet gecompileerd.
- Open: leerlingidentiteit over nieuwe inschrijvingen/schooljaren. Geen samenvoeging op alleen naam; gebruikersvraag naar uniek leerlingnummer of handmatig koppelen staat open.


## Versie 1.2.001 — compileerblokkering
- WinError 5 veroorzaakt door nog actieve dist/LeerkrachtenTool.exe (processen 10484 en 4476).
- Build-exe.bat controleert vooraf exact procespad en vervangingsrechten. Geen automatische processtop of verwijdering.
- Gecontroleerd: actieve executable wordt geblokkeerd; vrij tijdelijk bestand passeert zonder inhoudswijziging. Niet gecompileerd.
