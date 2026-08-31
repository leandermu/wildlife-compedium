"""Generates seed_species.json. Kept as source so the list stays easy to extend."""
import json, pathlib

ROWS = []

def s(name, sci, group, family, order, size, habitats, regions, difficulty, desc,
      wingspan="", weight="", tags=(), countries=("DE",), rarity=""):
    ROWS.append(dict(
        common_name=name, scientific_name=sci, group=group, family=family,
        order_name=order, size=size, wingspan=wingspan, weight=weight,
        habitats=list(habitats), regions=list(regions), countries=list(countries),
        tags=list(tags), difficulty=difficulty, rarity=rarity, description=desc,
    ))

BAY = ["bavaria", "germany", "europe"]
DE = ["germany", "europe"]
EU = ["europe"]
W = ["world"]

# ------------------------------------------------------------------ VÖGEL ---
s("Rotkehlchen", "Erithacus rubecula", "bird", "Fliegenschnäpper", "Sperlingsvögel",
  "13–14 cm", ["garden", "forest", "park", "city"], BAY, 1,
  "Der zutrauliche Gartenvogel mit der orangeroten Brust. Folgt oft dem Spaten und "
  "kommt Menschen näher als fast jeder andere Wildvogel – der perfekte erste Eintrag.",
  wingspan="20–22 cm", weight="16–22 g", tags=["standvogel", "singvogel", "haeufig"])
s("Amsel", "Turdus merula", "bird", "Drosseln", "Sperlingsvögel",
  "24–27 cm", ["garden", "forest", "park", "city"], BAY, 1,
  "Das Männchen tiefschwarz mit leuchtend gelbem Schnabel, das Weibchen erdbraun. "
  "Singt im Frühjahr von Dachfirsten und Antennen – ideal für Gegenlichtaufnahmen.",
  wingspan="34–38 cm", weight="80–110 g", tags=["standvogel", "singvogel"])
s("Buchfink", "Fringilla coelebs", "bird", "Finken", "Sperlingsvögel",
  "14–16 cm", ["forest", "garden", "park"], BAY, 1,
  "Häufigster Waldvogel Mitteleuropas. Der schmetternde Gesang endet in einem "
  "charakteristischen Schnörkel.", wingspan="24–28 cm", weight="18–25 g",
  tags=["singvogel"])
s("Kohlmeise", "Parus major", "bird", "Meisen", "Sperlingsvögel",
  "13–15 cm", ["garden", "forest", "park", "city"], BAY, 1,
  "Größte heimische Meise, kenntlich am schwarzen Bauchstreif. Am Futterhaus "
  "beinahe garantiert.", wingspan="22–25 cm", weight="16–21 g", tags=["futterhaus"])
s("Blaumeise", "Cyanistes caeruleus", "bird", "Meisen", "Sperlingsvögel",
  "11–12 cm", ["garden", "forest", "park", "city"], BAY, 1,
  "Klein, quirlig, azurblau gekappt. Turnt kopfüber an dünnen Zweigen.",
  wingspan="18–20 cm", weight="9–12 g", tags=["futterhaus"])
s("Haussperling", "Passer domesticus", "bird", "Sperlinge", "Sperlingsvögel",
  "14–16 cm", ["city", "garden", "field"], BAY, 1,
  "Der Spatz. Gesellig, laut und trotz Rückgang noch immer überall dort, wo Menschen "
  "wohnen.", wingspan="21–25 cm", weight="24–35 g", tags=["stadtvogel"])
s("Star", "Sturnus vulgaris", "bird", "Stare", "Sperlingsvögel",
  "19–22 cm", ["field", "garden", "city"], BAY, 1,
  "Im Prachtkleid metallisch grün-violett schillernd. Bildet im Herbst spektakuläre "
  "Schwärme.", wingspan="37–42 cm", weight="75–90 g", tags=["zugvogel", "schwarm"])
s("Elster", "Pica pica", "bird", "Rabenvögel", "Sperlingsvögel",
  "44–46 cm", ["city", "garden", "field"], BAY, 1,
  "Schwarz-weiß mit langem, blaugrün schimmerndem Schwanz. Klug, wachsam und "
  "erstaunlich schwer formatfüllend zu erwischen.", wingspan="52–60 cm", weight="200–250 g")
s("Eichelhäher", "Garrulus glandarius", "bird", "Rabenvögel", "Sperlingsvögel",
  "32–35 cm", ["forest", "park"], BAY, 2,
  "Die „Wachtel des Waldes\" warnt mit rauem Krächzen vor jedem Spaziergänger. "
  "Das blau gebänderte Flügelfeld ist ein Sammlerstück für sich.",
  wingspan="52–58 cm", weight="150–190 g")
s("Rabenkrähe", "Corvus corone", "bird", "Rabenvögel", "Sperlingsvögel",
  "45–49 cm", ["field", "city", "forest"], BAY, 1,
  "Einfarbig schwarz, sehr intelligent. In Bayern flächendeckend verbreitet.",
  wingspan="93–104 cm", weight="440–600 g")
s("Kolkrabe", "Corvus corax", "bird", "Rabenvögel", "Sperlingsvögel",
  "54–67 cm", ["forest", "alps", "field"], BAY, 3,
  "Größter Rabenvogel der Welt, erkennbar am keilförmigen Schwanz und dem tiefen "
  "„krock\". In den Alpen segelt er entlang der Felswände.",
  wingspan="115–130 cm", weight="0,8–1,5 kg")
s("Zaunkönig", "Troglodytes troglodytes", "bird", "Zaunkönige", "Sperlingsvögel",
  "9–11 cm", ["forest", "garden", "water"], BAY, 2,
  "Winziger brauner Kobold mit aufgestelltem Schwanz und unglaublich lautem Gesang. "
  "Hält sich meist im Dickicht – Geduld nötig.", wingspan="13–17 cm", weight="8–13 g")
s("Kleiber", "Sitta europaea", "bird", "Kleiber", "Sperlingsvögel",
  "12–15 cm", ["forest", "park", "garden"], BAY, 2,
  "Der einzige heimische Vogel, der kopfüber Stämme hinabläuft. Blaugrauer Rücken, "
  "schwarzer Augenstreif.", wingspan="23–27 cm", weight="20–25 g")
s("Gartenbaumläufer", "Certhia brachydactyla", "bird", "Baumläufer", "Sperlingsvögel",
  "12–13 cm", ["forest", "park", "garden"], BAY, 3,
  "Rindenfarben getarnt, spiralt in kurzen Rucken am Stamm nach oben. Vom "
  "Waldbaumläufer fast nur am Gesang zu trennen.", wingspan="17–20 cm", weight="8–12 g")
s("Rotmilan", "Milvus milvus", "bird", "Habichtartige", "Greifvögel",
  "60–70 cm", ["field", "forest"], BAY, 3,
  "Der Gabelweih – rostrot, mit tief gegabeltem Schwanz. Über der Hälfte des "
  "Weltbestands brütet in Deutschland.", wingspan="155–180 cm", weight="0,8–1,3 kg",
  tags=["greifvogel", "zugvogel"])
s("Schwarzmilan", "Milvus migrans", "bird", "Habichtartige", "Greifvögel",
  "55–60 cm", ["water", "field"], BAY, 3,
  "Dunkler und mit nur flach gekerbtem Schwanz. Jagt gern über Seen und Flüssen.",
  wingspan="150–170 cm", weight="0,6–1 kg", tags=["greifvogel", "zugvogel"])
s("Mäusebussard", "Buteo buteo", "bird", "Habichtartige", "Greifvögel",
  "46–58 cm", ["field", "forest"], BAY, 2,
  "Häufigster Greifvogel Deutschlands. Sitzt im Winter auf Zaunpfählen und "
  "Feldrainen – ein guter erster Greifvogel fürs Kompendium.",
  wingspan="110–130 cm", weight="0,6–1,2 kg", tags=["greifvogel"])
s("Turmfalke", "Falco tinnunculus", "bird", "Falken", "Greifvögel",
  "32–39 cm", ["field", "city"], BAY, 2,
  "Der Rüttelfalke: steht sekundenlang scheinbar bewegungslos in der Luft. Brütet "
  "auch an Kirchtürmen mitten in der Stadt.", wingspan="65–80 cm", weight="150–250 g",
  tags=["greifvogel"])
s("Wanderfalke", "Falco peregrinus", "bird", "Falken", "Greifvögel",
  "38–50 cm", ["alps", "city"], BAY, 4,
  "Schnellstes Tier der Erde – im Sturzflug über 300 km/h. Brütet an Felswänden und "
  "hohen Bauwerken.", wingspan="90–115 cm", weight="0,6–1,3 kg", tags=["greifvogel"])
s("Habicht", "Accipiter gentilis", "bird", "Habichtartige", "Greifvögel",
  "48–62 cm", ["forest"], BAY, 4,
  "Heimlicher Waldjäger mit breiten Flügeln und langem Schwanz. Wird meist nur für "
  "Sekunden sichtbar.", wingspan="95–125 cm", weight="0,6–1,4 kg", tags=["greifvogel"])
s("Sperber", "Accipiter nisus", "bird", "Habichtartige", "Greifvögel",
  "28–40 cm", ["forest", "garden", "city"], BAY, 3,
  "Kleiner Vogeljäger, der im Winter auch am Futterhaus auftaucht. Fliegt "
  "blitzschnell zwischen Hecken hindurch.", wingspan="55–75 cm", weight="100–320 g",
  tags=["greifvogel"])
s("Seeadler", "Haliaeetus albicilla", "bird", "Habichtartige", "Greifvögel",
  "70–90 cm", ["water", "coast"], DE, 4,
  "Der „fliegende Türflügel\" mit weißem Stoßschwanz. In Bayern seit wenigen Jahren "
  "wieder Brutvogel.", wingspan="200–245 cm", weight="3,5–6 kg", tags=["greifvogel"])
s("Steinadler", "Aquila chrysaetos", "bird", "Habichtartige", "Greifvögel",
  "75–90 cm", ["alps"], BAY, 5,
  "König der Alpen. In Bayern brüten nur etwa 50 Paare – ein echtes Trophäenfoto.",
  wingspan="190–230 cm", weight="3–6,5 kg", tags=["greifvogel", "alpen"])
s("Bartgeier", "Gypaetus barbatus", "bird", "Habichtartige", "Greifvögel",
  "100–115 cm", ["alps"], BAY, 5,
  "Größter Vogel der Alpen, seit 2021 in Berchtesgaden wieder ausgewildert. "
  "Rostrot gefärbtes Gefieder, rautenförmiger Schwanz.",
  wingspan="250–290 cm", weight="4,5–7 kg", tags=["greifvogel", "alpen", "legende"])
s("Fischadler", "Pandion haliaetus", "bird", "Fischadler", "Greifvögel",
  "55–65 cm", ["water"], DE, 4,
  "Stößt aus dem Rüttelflug mit den Fängen voran ins Wasser. In Bayern vor allem "
  "als Durchzügler an großen Seen.", wingspan="145–170 cm", weight="1,2–2 kg",
  tags=["greifvogel", "zugvogel"])
s("Uhu", "Bubo bubo", "bird", "Eigentliche Eulen", "Eulen",
  "59–73 cm", ["forest", "alps", "night"], BAY, 4,
  "Größte Eule der Welt mit orangefarbenen Augen und Federohren. Brütet in "
  "Steinbrüchen und Felswänden.", wingspan="155–180 cm", weight="1,5–4 kg",
  tags=["eule", "nacht"])
s("Waldkauz", "Strix aluco", "bird", "Eigentliche Eulen", "Eulen",
  "37–43 cm", ["forest", "park", "night"], BAY, 3,
  "Der Ruf aus jedem Gruselfilm. Häufigste Eule Bayerns, ruht tagsüber gern an "
  "Stammhöhlen – dort auch fotografierbar.", wingspan="94–104 cm", weight="400–600 g",
  tags=["eule", "nacht"])
s("Schleiereule", "Tyto alba", "bird", "Schleiereulen", "Eulen",
  "33–39 cm", ["field", "night"], BAY, 4,
  "Herzförmiger weißer Gesichtsschleier. Brütet in Scheunen und Kirchtürmen, jagt "
  "lautlos über Wiesen.", wingspan="85–95 cm", weight="290–340 g", tags=["eule", "nacht"])
s("Waldohreule", "Asio otus", "bird", "Eigentliche Eulen", "Eulen",
  "31–37 cm", ["forest", "field", "night"], BAY, 3,
  "Lange Federohren, orangegelbe Augen. Bildet im Winter Schlafgemeinschaften in "
  "Ortschaften.", wingspan="86–98 cm", weight="220–350 g", tags=["eule", "nacht"])
s("Sperlingskauz", "Glaucidium passerinum", "bird", "Eigentliche Eulen", "Eulen",
  "15–19 cm", ["forest", "alps"], BAY, 5,
  "Kleinste Eule Europas, kaum größer als ein Star. Bergwälder des Bayerischen "
  "Waldes und der Alpen.", wingspan="32–39 cm", weight="50–80 g", tags=["eule"])
s("Raufußkauz", "Aegolius funereus", "bird", "Eigentliche Eulen", "Eulen",
  "22–27 cm", ["forest", "alps", "night"], BAY, 5,
  "Erstaunt blickender Bergwaldbewohner mit befiederten Zehen. Nutzt alte "
  "Schwarzspechthöhlen.", wingspan="50–62 cm", weight="90–200 g", tags=["eule", "nacht"])
s("Eisvogel", "Alcedo atthis", "bird", "Eisvögel", "Rackenvögel",
  "17–19 cm", ["water"], BAY, 3,
  "Der fliegende Edelstein. Sitzt reglos über klarem Wasser und stürzt sich "
  "pfeilschnell auf Kleinfische. Ansitz mit Tarnung lohnt sich.",
  wingspan="24–26 cm", weight="35–45 g", tags=["gewaesser", "farbenpracht"])
s("Buntspecht", "Dendrocopos major", "bird", "Spechte", "Spechtvögel",
  "22–23 cm", ["forest", "garden", "park"], BAY, 2,
  "Häufigster Specht Mitteleuropas. Trommelt ab Februar an Resonanzästen.",
  wingspan="34–39 cm", weight="70–98 g", tags=["specht"])
s("Schwarzspecht", "Dryocopus martius", "bird", "Spechte", "Spechtvögel",
  "45–47 cm", ["forest"], BAY, 3,
  "So groß wie eine Krähe, tiefschwarz mit roter Kappe. Seine Höhlen sind "
  "Wohnungen für Raufußkauz und Hohltaube.", wingspan="64–73 cm", weight="250–370 g",
  tags=["specht"])
s("Grünspecht", "Picus viridis", "bird", "Spechte", "Spechtvögel",
  "30–36 cm", ["park", "garden", "field"], BAY, 3,
  "Lacht laut über Streuobstwiesen und sucht am Boden nach Ameisen.",
  wingspan="45–51 cm", weight="150–250 g", tags=["specht"])
s("Graureiher", "Ardea cinerea", "bird", "Reiher", "Ruderfüßer",
  "84–102 cm", ["water", "field"], BAY, 2,
  "Steht stundenlang bewegungslos im Flachwasser. Der geduldigste Fotomodel-"
  "Kandidat unter den großen Wasservögeln.", wingspan="155–195 cm", weight="1–2 kg")
s("Silberreiher", "Ardea alba", "bird", "Reiher", "Ruderfüßer",
  "85–100 cm", ["water"], BAY, 3,
  "Strahlend weiß mit gelbem Schnabel im Winter. In Bayern inzwischen regelmäßiger "
  "Wintergast.", wingspan="145–170 cm", weight="1–1,5 kg")
s("Kormoran", "Phalacrocorax carbo", "bird", "Kormorane", "Ruderfüßer",
  "77–94 cm", ["water", "coast"], BAY, 2,
  "Trocknet sein Gefieder mit ausgebreiteten Flügeln – ein grafisch starkes Motiv.",
  wingspan="121–149 cm", weight="2–3 kg")
s("Haubentaucher", "Podiceps cristatus", "bird", "Lappentaucher", "Lappentaucher",
  "46–51 cm", ["water"], BAY, 2,
  "Im Frühjahr zeigt das Paar den berühmten Pinguintanz mit Wasserpflanzen im "
  "Schnabel. Junge reiten auf dem Rücken.", wingspan="59–73 cm", weight="600–1500 g")
s("Weißstorch", "Ciconia ciconia", "bird", "Störche", "Schreitvögel",
  "100–115 cm", ["field", "water"], BAY, 2,
  "Adebar. Klappert auf dem Horst und schreitet über feuchte Wiesen.",
  wingspan="195–215 cm", weight="2,5–4,5 kg", tags=["zugvogel"])
s("Höckerschwan", "Cygnus olor", "bird", "Entenvögel", "Gänsevögel",
  "125–160 cm", ["water", "park"], BAY, 1,
  "Schwerster flugfähiger Vogel Europas. Im Gegenlicht über Wasserdampf ein "
  "Klassiker.", wingspan="200–240 cm", weight="8–14 kg")
s("Stockente", "Anas platyrhynchos", "bird", "Entenvögel", "Gänsevögel",
  "50–65 cm", ["water", "park", "city"], BAY, 1,
  "Der grün schillernde Erpelkopf ist eine gute Übung für Belichtung auf "
  "irisierenden Federn.", wingspan="81–98 cm", weight="0,8–1,5 kg")
s("Reiherente", "Aythya fuligula", "bird", "Entenvögel", "Gänsevögel",
  "40–47 cm", ["water"], BAY, 2,
  "Tauchente mit langem Nackenschopf und leuchtend gelbem Auge.",
  wingspan="65–72 cm", weight="550–900 g")
s("Gänsesäger", "Mergus merganser", "bird", "Entenvögel", "Gänsevögel",
  "58–68 cm", ["water", "alps"], BAY, 3,
  "Fischjäger mit gezähntem Hakenschnabel. Brütet an bayerischen Voralpenflüssen "
  "in Baumhöhlen.", wingspan="78–94 cm", weight="1–2 kg")
s("Blässhuhn", "Fulica atra", "bird", "Rallen", "Kranichvögel",
  "36–42 cm", ["water", "park"], BAY, 1,
  "Schiefergrau mit weißem Stirnschild, streitlustig. An jedem Weiher zu finden.",
  wingspan="70–80 cm", weight="600–900 g")
s("Teichhuhn", "Gallinula chloropus", "bird", "Rallen", "Kranichvögel",
  "30–38 cm", ["water"], BAY, 2,
  "Rot-gelber Schnabel, nickender Gang. Bleibt gern in Deckung am Schilfrand.",
  wingspan="50–55 cm", weight="250–400 g")
s("Kiebitz", "Vanellus vanellus", "bird", "Regenpfeifer", "Watvögel",
  "28–31 cm", ["field", "moor", "water"], BAY, 3,
  "Metallisch grün schillernd mit Federholle. Der taumelnde Balzflug im Frühjahr "
  "ist unverwechselbar.", wingspan="70–80 cm", weight="150–300 g", tags=["wiesenbrueter"])
s("Flussuferläufer", "Actitis hypoleucos", "bird", "Schnepfenvögel", "Watvögel",
  "18–21 cm", ["water", "alps"], BAY, 4,
  "Wippt unentwegt mit dem Hinterkörper und fliegt mit steifen, flatternden "
  "Flügelschlägen dicht über dem Wasser.", wingspan="32–35 cm", weight="40–60 g")
s("Kranich", "Grus grus", "bird", "Kraniche", "Kranichvögel",
  "110–130 cm", ["moor", "field", "water"], DE, 3,
  "Vogel des Glücks. Zieht im Herbst in Keilformation trompetend über Deutschland.",
  wingspan="200–230 cm", weight="4–7 kg", tags=["zugvogel"])
s("Feldlerche", "Alauda arvensis", "bird", "Lerchen", "Sperlingsvögel",
  "16–18 cm", ["field"], BAY, 2,
  "Singt minutenlang im Rüttelflug hoch über dem Acker. Am Boden hervorragend "
  "getarnt.", wingspan="30–36 cm", weight="30–45 g", tags=["wiesenbrueter"])
s("Rauchschwalbe", "Hirundo rustica", "bird", "Schwalben", "Sperlingsvögel",
  "17–21 cm", ["field", "garden"], BAY, 2,
  "Tief gegabelter Schwanz, rostrote Kehle. Der Flug fordert schnelle "
  "Verschlusszeiten und viel Geduld.", wingspan="32–35 cm", weight="16–22 g",
  tags=["zugvogel"])
s("Mauersegler", "Apus apus", "bird", "Segler", "Seglervögel",
  "16–18 cm", ["city"], BAY, 3,
  "Verbringt fast sein ganzes Leben in der Luft – schläft und paart sich im Flug. "
  "Ein echtes Können-Foto.", wingspan="40–44 cm", weight="36–50 g", tags=["zugvogel"])
s("Wiedehopf", "Upupa epops", "bird", "Wiedehopfe", "Rackenvögel",
  "25–29 cm", ["field", "heath"], DE, 5,
  "Rostorange mit schwarz-weißen Flügeln und aufstellbarer Haube. In Bayern nur "
  "sehr lokal – die Begegnung eines Sommers.", wingspan="44–48 cm", weight="45–80 g")
s("Neuntöter", "Lanius collurio", "bird", "Würger", "Sperlingsvögel",
  "16–18 cm", ["field", "heath"], BAY, 3,
  "Spießt Beute auf Dornen. Männchen mit grauer Kappe und schwarzer Räubermaske.",
  wingspan="24–27 cm", weight="25–35 g", tags=["zugvogel"])
s("Goldammer", "Emberiza citrinella", "bird", "Ammern", "Sperlingsvögel",
  "16–17 cm", ["field", "heath"], BAY, 2,
  "„Wie-wie-wie hab ich dich lieb\" – singt von Heckenspitzen, leuchtend gelber Kopf.",
  wingspan="23–29 cm", weight="25–35 g")
s("Stieglitz", "Carduelis carduelis", "bird", "Finken", "Sperlingsvögel",
  "12–13 cm", ["garden", "field", "park"], BAY, 2,
  "Der Distelfink: rote Gesichtsmaske, goldgelbe Flügelbinde. Turnt an "
  "Distelköpfen.", wingspan="21–25 cm", weight="14–19 g", tags=["farbenpracht"])
s("Gimpel", "Pyrrhula pyrrhula", "bird", "Finken", "Sperlingsvögel",
  "15–17 cm", ["forest", "garden"], BAY, 2,
  "Der Dompfaff mit karminroter Brust – im Schnee eines der schönsten Wintermotive.",
  wingspan="22–29 cm", weight="21–27 g", tags=["winter"])
s("Erlenzeisig", "Spinus spinus", "bird", "Finken", "Sperlingsvögel",
  "11–12,5 cm", ["forest", "garden"], BAY, 2,
  "Kleiner gelbgrüner Finke, hängt akrobatisch an Erlenzapfen.",
  wingspan="20–23 cm", weight="10–18 g")
s("Wacholderdrossel", "Turdus pilaris", "bird", "Drosseln", "Sperlingsvögel",
  "22–27 cm", ["field", "garden"], BAY, 2,
  "Grauer Kopf, kastanienbrauner Rücken. Fällt im Winter in Trupps über "
  "Beerensträucher her.", wingspan="39–42 cm", weight="80–130 g", tags=["winter"])
s("Singdrossel", "Turdus philomelos", "bird", "Drosseln", "Sperlingsvögel",
  "20–22 cm", ["forest", "garden", "park"], BAY, 2,
  "Wiederholt jede Strophe zwei- bis dreimal. Zerschlägt Schnecken an "
  "„Drosselschmieden\".", wingspan="33–36 cm", weight="65–90 g")
s("Alpendohle", "Pyrrhocorax graculus", "bird", "Rabenvögel", "Sperlingsvögel",
  "36–39 cm", ["alps"], BAY, 2,
  "Gelber Schnabel, rote Beine. Bettelt an jeder Gipfelbrotzeit – die einfachste "
  "Alpenart des Kompendiums.", wingspan="65–74 cm", weight="200–250 g", tags=["alpen"])
s("Alpenschneehuhn", "Lagopus muta", "bird", "Fasanenartige", "Hühnervögel",
  "34–36 cm", ["alps"], BAY, 5,
  "Im Winter reinweiß, im Sommer felsgrau gesprenkelt. Lebt oberhalb der "
  "Baumgrenze und lässt sich kaum finden.", wingspan="54–60 cm", weight="400–600 g",
  tags=["alpen", "winter"])
s("Auerhuhn", "Tetrao urogallus", "bird", "Fasanenartige", "Hühnervögel",
  "74–90 cm", ["forest", "alps"], BAY, 5,
  "Größtes Waldhuhn Europas. Sehr störungsempfindlich – Balzplätze bitte "
  "grundsätzlich meiden.", wingspan="87–125 cm", weight="1,5–5 kg", tags=["alpen"])
s("Birkhuhn", "Lyrurus tetrix", "bird", "Fasanenartige", "Hühnervögel",
  "40–55 cm", ["moor", "alps"], BAY, 5,
  "Leierförmiger Schwanz, blau schimmerndes Gefieder. Balzt kollektiv auf "
  "Moorlichtungen.", wingspan="65–80 cm", weight="0,8–1,4 kg", tags=["alpen", "moor"])
s("Mauerläufer", "Tichodroma muraria", "bird", "Mauerläufer", "Sperlingsvögel",
  "15–17 cm", ["alps"], BAY, 5,
  "Der „Schmetterling der Felswand\" mit karminroten Flügelfeldern. Der heilige "
  "Gral der Alpenfotografie.", wingspan="27–32 cm", weight="17–19 g",
  tags=["alpen", "legende"])
s("Wasseramsel", "Cinclus cinclus", "bird", "Wasseramseln", "Sperlingsvögel",
  "17–20 cm", ["water", "alps"], BAY, 3,
  "Taucht und läuft am Grund schnell fließender Bäche. Weißer Latz auf "
  "schokobraunem Gefieder.", wingspan="25–30 cm", weight="50–75 g")
s("Gebirgsstelze", "Motacilla cinerea", "bird", "Stelzen", "Sperlingsvögel",
  "17–20 cm", ["water", "alps"], BAY, 2,
  "Zitronengelbe Unterseite, sehr langer wippender Schwanz. An jedem Wehr und "
  "Mühlbach.", wingspan="25–27 cm", weight="15–23 g")
s("Bachstelze", "Motacilla alba", "bird", "Stelzen", "Sperlingsvögel",
  "16,5–19 cm", ["water", "field", "city"], BAY, 1,
  "Trippelt wippend über Parkplätze und Uferkies.", wingspan="25–30 cm",
  weight="19–27 g")
s("Zilpzalp", "Phylloscopus collybita", "bird", "Laubsängerartige", "Sperlingsvögel",
  "10–12 cm", ["forest", "garden", "park"], BAY, 2,
  "Benennt sich selbst im Gesang. Unauffällig olivbraun – die Herausforderung "
  "liegt in der Bestimmung.", wingspan="15–21 cm", weight="6–9 g", tags=["zugvogel"])
s("Mönchsgrasmücke", "Sylvia atricapilla", "bird", "Grasmücken", "Sperlingsvögel",
  "13–15 cm", ["forest", "garden", "park"], BAY, 2,
  "Männchen mit schwarzer, Weibchen mit rotbrauner Kappe. Flötender Überschlag "
  "am Ende der Strophe.", wingspan="20–23 cm", weight="14–20 g", tags=["zugvogel"])
s("Kuckuck", "Cuculus canorus", "bird", "Kuckucke", "Kuckucksvögel",
  "32–34 cm", ["forest", "moor", "field"], BAY, 4,
  "Jeder hört ihn, kaum jemand sieht ihn. Im Flug sperberähnlich mit spitzen "
  "Flügeln.", wingspan="55–65 cm", weight="105–130 g", tags=["zugvogel"])
s("Ringeltaube", "Columba palumbus", "bird", "Tauben", "Taubenvögel",
  "38–43 cm", ["forest", "park", "city", "garden"], BAY, 1,
  "Weißer Halsfleck, klatschender Abflug. Größte heimische Taube.",
  wingspan="68–80 cm", weight="450–550 g")
s("Graugans", "Anser anser", "bird", "Entenvögel", "Gänsevögel",
  "75–90 cm", ["water", "field"], BAY, 2,
  "Stammform der Hausgans. Familienverbände mit Gösseln sind ein dankbares Motiv.",
  wingspan="147–180 cm", weight="2,5–4 kg")
s("Fasan", "Phasianus colchicus", "bird", "Fasanenartige", "Hühnervögel",
  "70–90 cm", ["field"], BAY, 2,
  "Der Hahn ist ein Feuerwerk aus Kupfer, Grün und Rot. Startet mit lautem "
  "Poltern.", wingspan="70–90 cm", weight="0,9–1,4 kg")
s("Rebhuhn", "Perdix perdix", "bird", "Fasanenartige", "Hühnervögel",
  "28–32 cm", ["field"], DE, 4,
  "Einst überall auf Äckern, heute stark bedroht. Drückt sich bis zum letzten "
  "Moment in die Ackerfurche.", wingspan="45–48 cm", weight="350–450 g")

# ------------------------------------------------------------- SÄUGETIERE ---
s("Reh", "Capreolus capreolus", "mammal", "Hirsche", "Paarhufer",
  "95–140 cm", ["forest", "field"], BAY, 2,
  "Häufigstes Wildtier Bayerns. Am besten in der Dämmerung am Waldrand, mit "
  "ruhigem Ansitz statt Anpirschen.", weight="15–35 kg", tags=["daemmerung"])
s("Rothirsch", "Cervus elaphus", "mammal", "Hirsche", "Paarhufer",
  "160–250 cm", ["forest", "alps"], BAY, 3,
  "Zur Brunft im September röhren die Platzhirsche – akustisch wie fotografisch "
  "der Höhepunkt des Wildtierjahres.", weight="90–250 kg", tags=["brunft"])
s("Wildschwein", "Sus scrofa", "mammal", "Echte Schweine", "Paarhufer",
  "110–160 cm", ["forest", "field"], BAY, 3,
  "Nachtaktiv und wachsam. Rotten mit Frischlingen immer mit großem Abstand "
  "fotografieren.", weight="50–150 kg", tags=["nacht", "vorsicht"])
s("Rotfuchs", "Vulpes vulpes", "mammal", "Hunde", "Raubtiere",
  "60–90 cm", ["forest", "field", "city"], BAY, 3,
  "Anpassungskünstler bis in die Innenstädte. Das Mäusespringen im Schnee ist "
  "das klassische Motiv.", weight="5–10 kg", tags=["raubtier"])
s("Dachs", "Meles meles", "mammal", "Marder", "Raubtiere",
  "60–90 cm", ["forest", "night"], BAY, 4,
  "Dämmerungs- und nachtaktiv. Am Bau mit Tarnzelt und viel Zeit – oder gar nicht.",
  weight="7–14 kg", tags=["raubtier", "nacht"])
s("Feldhase", "Lepus europaeus", "mammal", "Hasen", "Hasenartige",
  "50–70 cm", ["field"], BAY, 2,
  "Lange schwarz gespitzte Löffel, drückt sich in der Sasse. Im März boxen die "
  "Rammler.", weight="3–5 kg")
s("Eichhörnchen", "Sciurus vulgaris", "mammal", "Hörnchen", "Nagetiere",
  "19–25 cm", ["forest", "park", "garden", "city"], BAY, 2,
  "In Bayern von rotbraun bis fast schwarz. In Parks oft erstaunlich zutraulich.",
  weight="200–400 g")
s("Europäischer Biber", "Castor fiber", "mammal", "Biber", "Nagetiere",
  "80–100 cm", ["water"], BAY, 3,
  "Bayern ist Biberland – über 20.000 Tiere. Aktiv in der Abenddämmerung an "
  "Burg und Damm.", weight="20–30 kg", tags=["daemmerung", "gewaesser"])
s("Braunbrustigel", "Erinaceus europaeus", "mammal", "Igel", "Insektenfresser",
  "20–30 cm", ["garden", "park", "city", "night"], BAY, 2,
  "Nachtaktiver Gartenbewohner. Bitte nie zum Wachwerden zwingen – lieber "
  "abends mit Licht aus dem Hintergrund.", weight="600–1200 g", tags=["nacht"])
s("Gämse", "Rupicapra rupicapra", "mammal", "Hornträger", "Paarhufer",
  "110–130 cm", ["alps", "forest"], BAY, 3,
  "Hakenförmige Krucken, im Winter fast schwarz. Klettert über Schrofen, an "
  "denen kein Mensch steht.", weight="25–50 kg", tags=["alpen"])
s("Alpenmurmeltier", "Marmota marmota", "mammal", "Hörnchen", "Nagetiere",
  "40–55 cm", ["alps"], BAY, 2,
  "Der Pfiff über der Almwiese. Am Wanderweg gewöhnte Kolonien lassen sich gut "
  "annähern.", weight="3–7 kg", tags=["alpen"])
s("Alpensteinbock", "Capra ibex", "mammal", "Hornträger", "Paarhufer",
  "130–150 cm", ["alps"], BAY, 4,
  "Mächtige geknotete Hörner. In Bayern nur in wenigen Kolonien, etwa am "
  "Hochvogel und Benediktenwand.", weight="40–120 kg", tags=["alpen"])
s("Steinmarder", "Martes foina", "mammal", "Marder", "Raubtiere",
  "40–55 cm", ["city", "garden", "night"], BAY, 4,
  "Weißer, gegabelter Kehlfleck. Der Untermieter unter Motorhauben – tagsüber "
  "kaum zu sehen.", weight="1,1–2,3 kg", tags=["raubtier", "nacht"])
s("Baummarder", "Martes martes", "mammal", "Marder", "Raubtiere",
  "45–58 cm", ["forest", "night"], BAY, 5,
  "Gelblicher Kehlfleck, scheuer Waldbewohner. Eine Sichtung ist bereits ein "
  "Ereignis.", weight="0,8–1,8 kg", tags=["raubtier", "nacht"])
s("Hermelin", "Mustela erminea", "mammal", "Marder", "Raubtiere",
  "22–32 cm", ["field", "forest"], BAY, 4,
  "Im Winter weiß mit schwarzer Schwanzspitze. Bewegt sich in nervösen Sprüngen – "
  "kurze Verschlusszeit bereithalten.", weight="150–300 g", tags=["raubtier", "winter"])
s("Fischotter", "Lutra lutra", "mammal", "Marder", "Raubtiere",
  "90–120 cm", ["water", "night"], BAY, 5,
  "Kehrt langsam nach Bayern zurück. Dämmerungsaktiv, meist nur als Kopf im "
  "dunklen Wasser.", weight="7–12 kg", tags=["raubtier", "gewaesser"])
s("Eurasischer Luchs", "Lynx lynx", "mammal", "Katzen", "Raubtiere",
  "80–120 cm", ["forest", "alps"], BAY, 5,
  "Pinselohren und Backenbart. Im Bayerischen Wald leben nur wenige Dutzend – "
  "die legendärste heimische Art.", weight="18–30 kg", tags=["raubtier", "legende"])
s("Siebenschläfer", "Glis glis", "mammal", "Bilche", "Nagetiere",
  "13–18 cm", ["forest", "garden", "night"], BAY, 4,
  "Große dunkle Augen, buschiger Schwanz. Nachts auf Dachböden und in Obstgärten.",
  weight="70–180 g", tags=["nacht"])
s("Großes Mausohr", "Myotis myotis", "mammal", "Glattnasen", "Fledermäuse",
  "6,7–8,4 cm", ["forest", "city", "night"], BAY, 5,
  "Größte heimische Fledermaus. Fotografie nur mit Blitz im Flug oder am "
  "Quartierausflug – anspruchsvoll.", wingspan="35–43 cm", weight="20–40 g",
  tags=["nacht", "fledermaus"])
s("Damhirsch", "Dama dama", "mammal", "Hirsche", "Paarhufer",
  "130–160 cm", ["forest", "field"], DE, 2,
  "Schaufelgeweih und weiß geflecktes Sommerkleid. In Bayern vor allem in "
  "Gattern und lokalen Beständen.", weight="40–100 kg")
s("Waschbär", "Procyon lotor", "mammal", "Kleinbären", "Raubtiere",
  "40–70 cm", ["forest", "city", "night"], DE, 3,
  "Eingebürgerter Neubürger mit schwarzer Gesichtsmaske. Nachtaktiv und "
  "neugierig.", weight="4–9 kg", tags=["nacht", "neozoon"])
s("Mauswiesel", "Mustela nivalis", "mammal", "Marder", "Raubtiere",
  "17–23 cm", ["field", "garden"], BAY, 5,
  "Kleinstes Raubtier der Welt. Verschwindet meist schneller, als der Autofokus "
  "sitzt.", weight="35–130 g", tags=["raubtier"])

# ----------------------------------------------------------- SCHMETTERLINGE -
s("Tagpfauenauge", "Aglais io", "butterfly", "Edelfalter", "Schmetterlinge",
  "5–6 cm Spannweite", ["garden", "field", "park"], BAY, 1,
  "Vier leuchtende Augenflecken schrecken Vögel ab. Überwintert als Falter und "
  "fliegt schon an warmen Märztagen.", wingspan="50–60 mm")
s("Kleiner Fuchs", "Aglais urticae", "butterfly", "Edelfalter", "Schmetterlinge",
  "4–5 cm Spannweite", ["garden", "field", "alps"], BAY, 1,
  "Ziegelrot mit blauem Saumfleckenband. Raupen leben gesellig an Brennnesseln.",
  wingspan="40–50 mm")
s("Admiral", "Vanessa atalanta", "butterfly", "Edelfalter", "Schmetterlinge",
  "5,5–6,5 cm Spannweite", ["garden", "forest", "field"], BAY, 2,
  "Wanderfalter aus dem Mittelmeerraum. Saugt im Spätsommer an Fallobst und ist "
  "dann sehr zutraulich.", wingspan="55–65 mm", tags=["wanderfalter"])
s("Distelfalter", "Vanessa cardui", "butterfly", "Edelfalter", "Schmetterlinge",
  "5–6 cm Spannweite", ["field", "garden"], BAY, 2,
  "Fliegt in manchen Jahren zu Millionen aus Nordafrika ein.", wingspan="50–60 mm",
  tags=["wanderfalter"])
s("Zitronenfalter", "Gonepteryx rhamni", "butterfly", "Weißlinge", "Schmetterlinge",
  "5–6 cm Spannweite", ["forest", "garden", "field"], BAY, 1,
  "Der erste Falter des Jahres – oft schon im Februar. Männchen leuchtend "
  "schwefelgelb, Weibchen fast weiß.", wingspan="50–60 mm", tags=["fruehling"])
s("Aurorafalter", "Anthocharis cardamines", "butterfly", "Weißlinge", "Schmetterlinge",
  "3,5–4,5 cm Spannweite", ["field", "forest", "garden"], BAY, 2,
  "Nur das Männchen trägt die orangefarbenen Flügelspitzen. Fliegt in einer "
  "kurzen Generation im Mai.", wingspan="35–45 mm", tags=["fruehling"])
s("Großer Kohlweißling", "Pieris brassicae", "butterfly", "Weißlinge", "Schmetterlinge",
  "5–6,5 cm Spannweite", ["garden", "field"], BAY, 1,
  "Bekanntester Kulturfolger unter den Faltern.", wingspan="50–65 mm")
s("Schwalbenschwanz", "Papilio machaon", "butterfly", "Ritterfalter", "Schmetterlinge",
  "6–8 cm Spannweite", ["field", "garden", "alps"], BAY, 3,
  "Segelt an sonnigen Hängen und sammelt sich zur Balz auf Bergkuppen – "
  "„Gipfelbalz\".", wingspan="60–80 mm", tags=["farbenpracht"])
s("Segelfalter", "Iphiclides podalirius", "butterfly", "Ritterfalter", "Schmetterlinge",
  "6–8 cm Spannweite", ["heath", "field"], DE, 4,
  "Tigerstreifen und lange Schwänzchen. In Bayern nur an warmen Trockenhängen.",
  wingspan="60–80 mm")
s("Kaisermantel", "Argynnis paphia", "butterfly", "Edelfalter", "Schmetterlinge",
  "5,5–6,5 cm Spannweite", ["forest"], BAY, 3,
  "Größter heimischer Perlmuttfalter. Sammelt sich im Hochsommer an "
  "Waldwegdisteln.", wingspan="55–65 mm")
s("Großer Schillerfalter", "Apatura iris", "butterfly", "Edelfalter", "Schmetterlinge",
  "6–7,5 cm Spannweite", ["forest", "water"], BAY, 4,
  "Nur aus bestimmten Winkeln schillern die Flügel elektrisch blau. Männchen "
  "saugen an feuchten Waldwegen.", wingspan="60–75 mm", tags=["farbenpracht"])
s("Trauermantel", "Nymphalis antiopa", "butterfly", "Edelfalter", "Schmetterlinge",
  "6–7,5 cm Spannweite", ["forest", "water"], BAY, 4,
  "Samtbraun mit cremeweißem Saum. Überwintert als Falter und erscheint an "
  "warmen Vorfrühlingstagen.", wingspan="60–75 mm")
s("Hauhechel-Bläuling", "Polyommatus icarus", "butterfly", "Bläulinge", "Schmetterlinge",
  "2,5–3 cm Spannweite", ["field", "heath"], BAY, 2,
  "Häufigster Bläuling. Am frühen Morgen schlafen die Falter an Grashalmen und "
  "lassen sich mit Tau fotografieren.", wingspan="25–30 mm")
s("Apollofalter", "Parnassius apollo", "butterfly", "Ritterfalter", "Schmetterlinge",
  "7–8,5 cm Spannweite", ["alps"], BAY, 5,
  "Rote Augenflecken auf durchscheinend weißen Flügeln. Streng geschützt, nur "
  "an wenigen Felshängen der Alpen und der Fränkischen Schweiz.",
  wingspan="70–85 mm", tags=["alpen", "legende"])
s("Landkärtchen", "Araschnia levana", "butterfly", "Edelfalter", "Schmetterlinge",
  "3–4 cm Spannweite", ["forest", "water"], BAY, 3,
  "Zwei völlig verschiedene Generationen: orange im Frühling, schwarz-weiß im "
  "Sommer.", wingspan="30–40 mm")
s("Taubenschwänzchen", "Macroglossum stellatarum", "butterfly", "Schwärmer", "Schmetterlinge",
  "4–4,5 cm Spannweite", ["garden", "field"], BAY, 4,
  "Schwirrt wie ein Kolibri vor Blüten. Verlangt 1/2000 s und viel Übung.",
  wingspan="40–45 mm", tags=["wanderfalter"])

# --------------------------------------------------------------- INSEKTEN ---
s("Blauflügel-Prachtlibelle", "Calopteryx virgo", "insect", "Prachtlibellen", "Libellen",
  "4,5–5 cm", ["water", "forest"], BAY, 3,
  "Männchen mit vollständig metallblauen Flügeln, gaukelnder Flug über "
  "schattigen Bächen.", wingspan="60–70 mm", tags=["libelle"])
s("Große Königslibelle", "Anax imperator", "insect", "Edellibellen", "Libellen",
  "6,5–8,5 cm", ["water", "garden"], BAY, 3,
  "Patrouilliert unermüdlich über dem Weiher und landet fast nie – Mitzieher "
  "üben!", wingspan="95–110 mm", tags=["libelle"])
s("Plattbauch", "Libellula depressa", "insect", "Segellibellen", "Libellen",
  "4–4,5 cm", ["water", "garden"], BAY, 2,
  "Breiter, hellblau bereifter Hinterleib. Kehrt gern zum selben Ansitzstock "
  "zurück – dankbares Motiv.", wingspan="70–80 mm", tags=["libelle"])
s("Hirschkäfer", "Lucanus cervus", "insect", "Schröter", "Käfer",
  "3,5–9 cm", ["forest"], BAY, 5,
  "Größter Käfer Europas. Fliegt an schwülen Juniabenden um alte Eichen.",
  weight="2–8 g", tags=["kaefer", "legende"])
s("Maikäfer", "Melolontha melolontha", "insect", "Blatthornkäfer", "Käfer",
  "2,5–3 cm", ["forest", "garden"], BAY, 3,
  "Gefächerte Fühler, klassischer Frühlingsbote. Erscheint massenhaft nur alle "
  "paar Jahre.", tags=["kaefer", "fruehling"])
s("Siebenpunkt-Marienkäfer", "Coccinella septempunctata", "insect", "Marienkäfer", "Käfer",
  "5–8 mm", ["garden", "field"], BAY, 1,
  "Der Glückskäfer. Gute Übung für Makro und Schärfentiefe.", tags=["kaefer"])
s("Hornisse", "Vespa crabro", "insect", "Faltenwespen", "Hautflügler",
  "2–3,5 cm", ["forest", "garden"], BAY, 3,
  "Größte heimische Wespe, friedlicher als ihr Ruf. Streng geschützt – Abstand "
  "zum Nest halten.", tags=["hautfluegler"])
s("Dunkle Erdhummel", "Bombus terrestris", "insect", "Echte Bienen", "Hautflügler",
  "1,5–2,5 cm", ["garden", "field", "alps"], BAY, 1,
  "Fliegt schon bei 5 °C. Die Königinnen im März sind erstaunlich groß.",
  tags=["hautfluegler", "bestaeuber"])
s("Honigbiene", "Apis mellifera", "insect", "Echte Bienen", "Hautflügler",
  "1,1–1,5 cm", ["garden", "field"], BAY, 1,
  "Mit Pollenhöschen an der Blüte – ein Klassiker der Nahfotografie.",
  tags=["hautfluegler", "bestaeuber"])
s("Grünes Heupferd", "Tettigonia viridissima", "insect", "Laubheuschrecken", "Heuschrecken",
  "2,8–4,2 cm", ["field", "garden"], BAY, 2,
  "Große grüne Langfühlerschrecke, zirpt bis in die Nacht hinein.",
  tags=["heuschrecke"])
s("Gottesanbeterin", "Mantis religiosa", "insect", "Fangschrecken", "Fangschrecken",
  "4–7,5 cm", ["field", "heath"], DE, 4,
  "Breitet sich mit dem Klimawandel nach Norden aus und erreicht inzwischen "
  "auch Bayern.", tags=["waermeliebend"])
s("Feuerlibelle", "Crocothemis erythraea", "insect", "Segellibellen", "Libellen",
  "3,3–4,4 cm", ["water"], BAY, 3,
  "Männchen leuchtend scharlachrot. Ein Gewinner der wärmeren Sommer.",
  wingspan="60–70 mm", tags=["libelle", "waermeliebend"])

# ----------------------------------------------- AMPHIBIEN UND REPTILIEN ----
s("Erdkröte", "Bufo bufo", "amphibian", "Kröten", "Froschlurche",
  "8–13 cm", ["forest", "water", "garden", "night"], BAY, 2,
  "Die große Wanderung zu den Laichgewässern im März ist die beste "
  "Fotogelegenheit – bitte auf der Straße nur mit Warnweste.", tags=["fruehling"])
s("Grasfrosch", "Rana temporaria", "amphibian", "Echte Frösche", "Froschlurche",
  "6–9 cm", ["water", "forest", "field"], BAY, 2,
  "Laicht als Erster, oft noch unter Eisresten. Kehlansicht mit Spiegelung im "
  "Laichgewässer.")
s("Laubfrosch", "Hyla arborea", "amphibian", "Laubfrösche", "Froschlurche",
  "3–5 cm", ["water", "moor"], BAY, 4,
  "Leuchtend grün mit Haftscheiben. Der Chor der Männchen ist kilometerweit "
  "hörbar.", tags=["gewaesser"])
s("Feuersalamander", "Salamandra salamandra", "amphibian", "Echte Salamander", "Schwanzlurche",
  "14–20 cm", ["forest", "water", "night"], BAY, 3,
  "Schwarz-gelb gemustert wie ein Wappentier. Erscheint nach warmem Regen in "
  "Laubwäldern mit Quellbächen.", tags=["nacht", "regen"])
s("Bergmolch", "Ichthyosaura alpestris", "amphibian", "Echte Salamander", "Schwanzlurche",
  "8–12 cm", ["water", "forest", "alps"], BAY, 3,
  "Im Wassertracht orangefarbener Bauch und blau schimmernde Flanken.")
s("Zauneidechse", "Lacerta agilis", "reptile", "Echte Eidechsen", "Schuppenkriechtiere",
  "18–24 cm", ["heath", "garden", "field"], BAY, 3,
  "Männchen im Mai leuchtend grün geflankt. Sonnt sich morgens auf Totholz und "
  "Steinen.", tags=["fruehling"])
s("Ringelnatter", "Natrix natrix", "reptile", "Nattern", "Schuppenkriechtiere",
  "70–120 cm", ["water", "moor"], BAY, 3,
  "Gelbe Halbmondflecken am Hinterkopf. Ungiftig, schwimmt oft mit erhobenem "
  "Kopf.", tags=["gewaesser"])
s("Kreuzotter", "Vipera berus", "reptile", "Vipern", "Schuppenkriechtiere",
  "50–80 cm", ["moor", "alps", "heath"], BAY, 5,
  "Dunkles Zickzackband, senkrechte Pupille. Einzige Giftschlange Bayerns – "
  "nur mit Teleobjektiv und Abstand.", tags=["moor", "vorsicht"])
s("Blindschleiche", "Anguis fragilis", "reptile", "Schleichen", "Schuppenkriechtiere",
  "30–50 cm", ["forest", "garden"], BAY, 2,
  "Keine Schlange, sondern eine beinlose Echse – erkennbar an den beweglichen "
  "Augenlidern.")

# ------------------------------------------------------------------ FISCHE --
s("Bachforelle", "Salmo trutta fario", "fish", "Lachsfische", "Lachsartige",
  "25–50 cm", ["water", "alps"], BAY, 4,
  "Rot umrandete Tupfen. Aus dem Uferschatten mit Polfilter über klaren "
  "Voralpenbächen.", weight="0,3–2 kg", tags=["gewaesser"])
s("Hecht", "Esox lucius", "fish", "Hechte", "Hechtartige",
  "50–120 cm", ["water"], BAY, 4,
  "Der Standjäger im Schilfgürtel. Im Frühjahr im flachen Laichkraut "
  "sichtbar.", weight="1–15 kg", tags=["gewaesser"])
s("Äsche", "Thymallus thymallus", "fish", "Lachsfische", "Lachsartige",
  "30–50 cm", ["water"], BAY, 5,
  "Die „Fahne\" – die riesige Rückenflosse – macht sie unverwechselbar. "
  "Charakterfisch bayerischer Flüsse.", weight="0,3–1,5 kg", tags=["gewaesser"])

# -------------------------------------------------- WELT / EXPEDITION -------
s("Löwe", "Panthera leo", "mammal", "Katzen", "Raubtiere",
  "170–250 cm", ["savanna"], W, 4,
  "Ruht bis zu 20 Stunden am Tag. Das beste Licht gibt es in der ersten halben "
  "Stunde nach Sonnenaufgang.", weight="120–250 kg",
  countries=("KE", "TZ", "ZA", "BW"), tags=["expedition", "raubtier", "afrika"])
s("Leopard", "Panthera pardus", "mammal", "Katzen", "Raubtiere",
  "125–190 cm", ["savanna", "forest"], W, 5,
  "Heimlichste der großen Katzen. Legt die Beute in Bäumen ab – dort gelingen "
  "die stärksten Bilder.", weight="30–90 kg",
  countries=("KE", "TZ", "ZA", "IN"), tags=["expedition", "raubtier", "afrika"])
s("Afrikanischer Elefant", "Loxodonta africana", "mammal", "Elefanten", "Rüsseltiere",
  "600–750 cm", ["savanna"], W, 3,
  "Größtes Landtier der Erde. Ganze Herden am Wasserloch – Weitwinkel und Tele "
  "wechseln sich ab.", weight="4–6,5 t",
  countries=("KE", "TZ", "ZA", "BW"), tags=["expedition", "afrika"])
s("Breitmaulnashorn", "Ceratotherium simum", "mammal", "Nashörner", "Unpaarhufer",
  "340–420 cm", ["savanna"], W, 4,
  "Grasender Riese mit breiter Maulscheibe. Am eindrucksvollsten im "
  "Gegenlichtstaub.", weight="1,8–2,5 t", countries=("ZA", "KE", "NA"),
  tags=["expedition", "afrika"])
s("Afrikanischer Büffel", "Syncerus caffer", "mammal", "Hornträger", "Paarhufer",
  "220–340 cm", ["savanna"], W, 3,
  "Gilt als eines der gefährlichsten Tiere Afrikas. Der Blick über die "
  "Hornbasis ist das ikonische Motiv.", weight="500–900 kg",
  countries=("KE", "TZ", "ZA"), tags=["expedition", "afrika"])
s("Giraffe", "Giraffa camelopardalis", "mammal", "Giraffen", "Paarhufer",
  "450–580 cm", ["savanna"], W, 3,
  "Beim Trinken spreizt sie die Vorderbeine – die klassische Safariszene.",
  weight="800–1900 kg", countries=("KE", "TZ", "NA"), tags=["expedition", "afrika"])
s("Eisbär", "Ursus maritimus", "mammal", "Bären", "Raubtiere",
  "200–300 cm", ["coast", "ocean"], W, 5,
  "Größtes Landraubtier. Svalbard oder Churchill – eine Reise nur für dieses "
  "eine Bild.", weight="150–700 kg", countries=("NO", "CA", "GL"),
  tags=["expedition", "arktis", "raubtier", "legende"])
s("Braunbär", "Ursus arctos", "mammal", "Bären", "Raubtiere",
  "150–280 cm", ["forest", "alps"], ["europe", "world"], 5,
  "In Europa noch in den Karpaten, Skandinavien und Slowenien. In Bayern nur "
  "als seltener Durchwanderer.", weight="100–350 kg",
  countries=("RO", "SI", "FI", "SK"), tags=["expedition", "raubtier", "legende"])
s("Wolf", "Canis lupus", "mammal", "Hunde", "Raubtiere",
  "100–150 cm", ["forest", "field"], ["germany", "europe", "world"], 5,
  "Kehrt nach Deutschland zurück, auch nach Bayern. Ein freilebender Wolf vor "
  "der Linse ist reines Glück.", weight="30–50 kg",
  countries=("DE", "PL", "RO"), tags=["raubtier", "legende"])
s("Orca", "Orcinus orca", "mammal", "Delfine", "Wale",
  "600–900 cm", ["ocean", "coast"], W, 5,
  "Die hohe Rückenfinne der Bullen ragt bis 1,8 m aus dem Wasser. Norwegen im "
  "Winter, Island oder British Columbia.", weight="3–6 t",
  countries=("NO", "IS", "CA"), tags=["expedition", "meer", "legende"])
s("Buckelwal", "Megaptera novaeangliae", "mammal", "Furchenwale", "Wale",
  "1200–1600 cm", ["ocean"], W, 4,
  "Berühmt für spektakuläre Sprünge und die lange, weiße Brustflosse.",
  weight="25–30 t", countries=("IS", "NO", "US"), tags=["expedition", "meer"])
s("Riesentukan", "Ramphastos toco", "bird", "Tukane", "Spechtvögel",
  "55–65 cm", ["rainforest"], W, 3,
  "Der größte Tukan – der leuchtend orange Schnabel ist fast ein Fünftel der "
  "Körperlänge.", wingspan="55–60 cm", weight="500–860 g",
  countries=("BR", "AR", "BO"), tags=["expedition", "farbenpracht"])
s("Rubinkehlkolibri", "Archilochus colubris", "bird", "Kolibris", "Seglervögel",
  "7–9 cm", ["garden", "rainforest"], W, 4,
  "Über 50 Flügelschläge pro Sekunde. Nur mit sehr kurzer Belichtung oder "
  "mehreren Blitzen einzufrieren.", wingspan="8–11 cm", weight="2–6 g",
  countries=("US", "CA", "MX"), tags=["expedition", "farbenpracht"])
s("Blauer Morphofalter", "Morpho menelaus", "butterfly", "Edelfalter", "Schmetterlinge",
  "12–15 cm Spannweite", ["rainforest"], W, 4,
  "Das Blau entsteht nicht durch Farbe, sondern durch Lichtbrechung an "
  "Flügelschuppen. Nur im Flug sichtbar.", wingspan="120–150 mm",
  countries=("BR", "CR", "PE"), tags=["expedition", "farbenpracht"])
s("Kleiner Paradiesvogel", "Paradisaea minor", "bird", "Paradiesvögel", "Sperlingsvögel",
  "32 cm", ["rainforest"], W, 5,
  "Balzt in traditionellen Bäumen Neuguineas mit kaskadierenden Schmuckfedern.",
  wingspan="—", weight="180–300 g", countries=("PG", "ID"),
  tags=["expedition", "legende", "farbenpracht"])

out = pathlib.Path(__file__).with_name("seed_species.json")
out.write_text(json.dumps(ROWS, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(ROWS)} Arten -> {out.name}")
from collections import Counter
print(Counter(r["group"] for r in ROWS))
