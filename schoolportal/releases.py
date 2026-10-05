"""Software release history. Newest release first; never overwrite older entries."""
RELEASES = [
    {
        'version': '1.2.001', 'date': '2026-10-05', 'kind': 'Bugfix',
        'title': 'Duidelijke melding bij geblokkeerde executable',
        'changes': [
            'Compileerscript controleert vooraf of de bestaande executable vervangen kan worden.',
            'Bij een draaiende toepassing of toegangsblokkering stopt de build met uitleg; geen processen worden geforceerd afgesloten.',
        ],
    },
    {
        'version': '1.2.000', 'date': '2026-10-05', 'kind': 'Functie-update',
        'title': 'Leerplanselectie, deel-BK’s en totalen op 100',
        'changes': [
            'Selecteer een volledig leerplan per studierichting/graad, volledige BK’s of losse subdoelen voor een les.',
            'BK zonder subdoelen is rechtstreeks beoordeelbaar; bestaande lespunten en scores blijven behouden.',
            'BK-opvolging over lessen en vakken: pas volledig aangereikt als elk subdoel minstens één cijfer heeft; nul telt mee.',
            'Blijvende subdoelkoppelingen met migratie van bestaande leshistoriek; geen automatische samenvoeging van leerlinginschrijvingen.',
            'Verwijderen vanuit de BK-hoofding, duidelijke lege-rijenknoppen, compacte volgordebediening en witte tabelkop.',
            'Opslaan en export bij de lestitel; tabbladen onder de lesgegevens; het aparte scoreregelsvenster vervalt.',
            'Totalen in evaluatie en Excel op 100; invoerscores en gemiddelden blijven op de schaal 0–80.',
            'Afzonderlijke uitgebreide demo: zes klassen met 19 leerlingen, 36 extra BK’s en 24 extra lessen.',
        ],
    },
    {
        'version': '1.1.000', 'date': '2026-10-05', 'kind': 'Functie-update',
        'title': 'Desktopwerkplek en gedeelde tool-administratie',
        'changes': [
            'Evaluatiematrix over de volledige werkbreedte; vaste actiebalk en breed doelenvenster met tabbladen.',
            'Vaste vensterindeling: alleen het centrale werkgebied scrolt; Punten, Feedback en Klasresultaten hebben eigen tabbladen.',
            'Compacte desktopstijl op aanmelden, start, tool-administratie, export, instellingen en admin; vaste titels/filters met één scrollend werkgebied.',
            'Compacte rijacties naast elkaar en exportkeuzes op één regel; uniforme kleinere formulieren en werkbalken.',
            'Tool-administratie onder Instellingen: gedeelde schooljaren, richtingen, vakken, klassen, leerlingen en doelen.',
            'Maker en admin kunnen lesresultaten aanpassen; andere leerkrachten kunnen ze bekijken volgens hun inzage.',
            'Excel: A4 liggend, kop- en voetteksten, herhaalde tabelkoppen, verticale namen en scorekleuren.',
            'Eigen Windows-appvenster via WebView2 en veilig afsluiten van de lokale server.',
            'Versienummer zichtbaar in de tool en apart softwarelogboek voor de beheerder.',
        ],
    },
    {
        'version': '1.0.000', 'date': '2026-10-04', 'kind': 'Basisversie',
        'title': 'Evaluaties, beheer en puntenlijsten',
        'changes': [
            'Accounts, moduletoegang, schoolstructuur, lesmomenten, evaluatiepunten en feedback.',
            'Excel-puntenlijsten voor klas en leerling; doelenoverzicht per subdoel.',
            'Persoonlijke kleuren, gegevenslogboek en lokale back-up met herstel.',
        ],
    },
]
VERSION = RELEASES[0]['version']
