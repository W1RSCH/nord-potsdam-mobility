# Methodik: Strategische Straßen- und ÖPNV-Netze

## 1. Datengrundlage

- **Straßennetz:** OpenStreetMap (OSM), zur Laufzeit über Overpass geladen. Für die Netzbewertung werden routbare Kfz-Straßenklassen, Geometrie, Einbahnregelungen und – soweit vorhanden – `maxspeed` verwendet.
- **Siedlungs-/Aktivitätsdaten:** ALKIS-Ist-Nutzung, insbesondere Wohnflächen und Arbeits-/Gewerbe-/Funktionsstandorte.
- **Wohngewicht:** Zensus 2022, 100-m-Bevölkerungsraster; für Bereiche ohne Bevölkerungswert wird ersatzweise ALKIS-Wohnfläche verwendet.
- **Verkehrszählungen:** ausgewertete Stromlinienplan-PDFs (Frühspitze, Nachmittagsspitze, 6h-Summe sowie – soweit extrahierbar – Zufahrtswerte nach Himmelsrichtung und Fahrzeugklasse). Nur tatsächlich vorhandene Berichte/Messwerte gehen quantitativ ein.
- **ÖPNV:** VBB-GTFS: Linien-/Fahrweggeometrien und Fahrplanangebot, einschließlich typischer Fahrtenzahlen und berechneter HVZ-/NVZ-Angebotsintervalle.

## 2. Wohn-Arbeits-Verkehrsmodell

1. Wohn- und Arbeitsflächen sowie Zensus-Einwohner werden auf ein quadratisches 400-m-Analyseraster aggregiert.
2. Jede Wohnzone mit positivem Wohnpotenzial wird einer nächstgelegenen routbaren OSM-Netzknotenposition zugeordnet (maximal 1.000 m Entfernung). Arbeitszonen werden entsprechend mit ihrem ALKIS-Arbeits-/Funktionsflächenpotenzial als Zielzonen angebunden.
3. Die Verkehrswege werden im gerichteten OSM-Straßengraphen mit Dijkstra-Kürzeste-Wege-Bäumen bestimmt. Einbahnstraßen werden berücksichtigt; Fahrzeitkosten beruhen auf OSM-Geschwindigkeitsangaben bzw. typisierten Standardgeschwindigkeiten.
4. Zielgewichte werden rückwärts über die Kürzeste-Wege-Bäume auf die tatsächlich verwendeten Straßensegmente aggregiert. Das Resultat ist ein fahrzeitgewichteter **OD-Potenzialindex** und die Zahl der OD-Zonenpaare je Segment.

**Interpretation:** Das Modell ist eine räumliche Potenzial-/Netzbelastungsanalyse, keine empirische Quelle-Ziel-Matrix. ALKIS-Fläche ist kein Beschäftigtenbestand; das Zensus-Wohngewicht ersetzt keine beobachtete Verkehrsmittelwahl oder Pendlerbefragung. Die Werte sind nicht als Kfz/h oder reale Pendlerzahlen zu lesen.

## 3. Priorisierung von Straßenabschnitten

Aus allen Segmenten mit positivem OD-Potenzial sowie Segmenten in unmittelbarer Nähe ausgewerteter Zählstellen wird ein Kandidatenpool gebildet. Der Prioritätsindex kombiniert:

- logarithmisch normiertes OD-Potenzial je Segment,
- logarithmisch normierte Zahl der durchlaufenden OD-Zonenpaare,
- Straßenhierarchie (`highway`-Klasse),
- Nähe zu einer Zählstelle,
- normierte gemessene Spitzenbelastung am zugeordneten Zählstellenknoten, sofern vorhanden.

Der implementierte relative Index lautet:

`I_Straße = 4,8 · N_OD + 1,8 · N_Paare + 0,42 · K_Straße + 0,35 · Z + 3,0 · N_Mess`

Dabei sind `N_OD` und `N_Paare` logarithmisch auf den jeweils höchsten Segmentwert normierte Werte, `K_Straße` der obige Straßenklassenfaktor, `Z` ein Indikator für einen nahegelegenen Zählstellenknoten (0/1) und `N_Mess` der gemessene Spitzenwert relativ zum höchsten im Modell vorhandenen Spitzenwert (0, falls kein Messwert vorhanden ist). Die höchsten bewerteten Kandidaten werden als strategische Straßenabschnitte visualisiert (Top 3,5 % des Kandidatenpools, maximal 160 Segmente). Der Index dient der vergleichenden Vorauswahl und ist keine standardisierte Leistungsfähigkeits- oder Kapazitätskennzahl.

## 4. Priorisierung von Knotenpunkten

Knoten mit mindestens drei angrenzenden Netzsegmenten werden anhand der aufsummierten angrenzenden OD-Potenziale, der Zahl der OD-Zonenpaare, der höchsten angrenzenden Straßenklasse, des Knotengrads und verfügbarer Zählwerte bewertet. Die wichtigsten Knoten werden als begrenzte Top-Auswahl (maximal 45) dargestellt.

## 5. Stromlinien aus Verkehrszählungen

Die derzeit lokal integrierten Stromlinienplan-PDFs enthalten für drei KPNR richtungsbezogene Kfz-Zählwerte je Zufahrt (NORD/OST/SÜD/WEST) und Zeitabschnitt. Für die Karte wird je KPNR der jüngste Bericht mit auswertbaren Zufahrtswerten verwendet. Die Zufahrtsrichtungen werden anhand der Himmelsrichtung am nächstgelegenen OSM-Netzknoten einem angrenzenden Straßenarm zugeordnet; der Straßenarm wird entlang derselben OSM-Way-Geometrie verlängert. Linienbreite und Deckkraft skalieren mit der 6h-Kfz-Menge je Zufahrt; Popup-Werte zeigen zusätzlich Früh- und Nachmittagsspitze.

**Wichtige Einschränkung:** Das sind gemessene Zufahrtsstromlinien, keine vollständigen Abbiegeströme. Die PDF-Daten, die aktuell verarbeitet sind, enthalten keine vollständige Fahrbeziehungs-/Abbiege-OD-Matrix. Geometrische Zuordnung zum OSM-Straßenarm ist eine kartographische Annäherung. Insbesondere OCR-Auswertungen sind anhand des Original-PDFs zu kontrollieren. Die 2018er OCR-Auswertung für KPNR 1851 enthält bislang keine auswertbaren Zufahrtszeilen; daher wird für dessen Richtungsdarstellung auf den jüngeren Bericht mit vollständigen Richtungswerten zurückgegriffen (2014).

## 6. Strategisch wichtige ÖPNV-Verbindungen

- **Schienengebundene Linien:** S-Bahn, Regionalverkehr und Tram werden vollständig in den strategischen ÖPNV-Layer aufgenommen, da sie eigenständige, liniengebundene Hauptachsen darstellen.
- **Buslinien:** Buslinien werden nicht pauschal aufgenommen. Die Liniengeometrie wird segmentweise mit den priorisierten Straßenabschnitten und wichtigen Knoten verglichen. Berücksichtigt werden nur Linien mit mindestens 2,6 km und mindestens 20 % Streckenanteil auf strategischen Korridoren sowie mindestens 3 strategischen Knoten. Alternativ genügt eine Überlagerung von mindestens 4,2 km und 16 % Streckenanteil bei mindestens 2 Knoten. Aus den Kandidaten werden maximal vier Linien mit dem höchsten Überlagerungs-Score ausgewählt. Schienengebundene Linien (S-Bahn, Regionalverkehr, Tram) werden vollständig dargestellt.
- **Angebotsmetrik:** Für Popups werden die im GTFS-Fahrplan enthaltenen typischen Wochentagsfahrten und berechneten HVZ-/NVZ-Intervalle angezeigt.

**Keine Auslastungsdaten:** Der bereitgestellte GTFS-Datensatz beschreibt Fahrplanangebot und Geometrien. Er enthält keine Fahrgastzählungen, Besetzungsgrade oder Kapazitätsauslastung. Deshalb werden keine Aussagen zur tatsächlichen Nachfrage oder Fahrzeugauslastung getroffen.

## 7. Kordonerhebung 2016: ergänzende Interpretation

Die städtische Kordonerhebung 2016 hat ein- und ausfahrende Kfz an 13 wichtigen Einfallstraßen sowie an einem äußeren Kordon entlang/im Bereich des Autobahnrings A10/A115 und an zwei innerstädtischen Havelbrückenquerschnitten erfasst. Sie eignet sich zur Einordnung regionaler Pendler- und Durchgangsverkehre, bildet aber den gesamten innerstädtischen Binnenverkehr nicht ab. Die Kordonergebnisse sind daher als eigenständige empirische Kontextinformation zu lesen und nicht direkt mit dem ALKIS-basierten Wohn-Arbeits-Potenzialindex gleichzusetzen.

Quelle: Landeshauptstadt Potsdam, *Kordonerhebung 2016 Potsdam und Potsdam-Mittelmark*, Veröffentlichungsseite und Ergebnisdokumentation.


## 8. Fußläufige ÖPNV-Erreichbarkeit

Für die ÖPNV-Abdeckung wird aus den OSM-Wegen mit Fußgängereignung ein ungerichteter Graph aufgebaut. GTFS-Haltestellen werden auf den nächstgelegenen Graphknoten (maximal 650 m Snap-Distanz) abgebildet. Anschließend berechnet ein Mehrquellen-Dijkstra die kürzeste Wegdistanz von allen angebundenen Haltestellen zu den Netzpunkten. Jede 100-m-Zelle wird über ihren Mittelpunkt dem nächstgelegenen Fußwegenetzpunkt zugeordnet; die Snap-Distanz zur Zelle wird addiert.

Es werden drei Zustände unterschieden: (1) Fußwegenetzdistanz, (2) Luftlinien-Fallback, wenn die Zelle nicht auf das Netz snappen kann, (3) keine Verbindung innerhalb des berechneten Netzgraphen, wenn die Zelle zwar an einen Netzpunkt angebunden ist, dieser aber von keiner Haltestelle erreichbar ist. Der Regler 100–1.000 m steuert die Farbklassifizierung, nicht die Netzberechnung selbst. Die Modellierung ist eine vereinfachte Fußwegeanalyse und berücksichtigt derzeit keine individuellen Zugangsbarrieren, Querungszeiten, Steigungen oder gesondert modellierten Eingangspunkte von Haltestellen.

## 9. Räumliche Sektoren

Nord, Ost, Süd und West sind künstliche Richtungssektoren. Ihr Mittelpunkt ist der Landtag Brandenburg. Die Teilung erfolgt über diagonale Winkelbereiche, anschließend werden die Polygone an der ALKIS-Verwaltungsgrenze Potsdams abgeschnitten. Die Flächen sind keine amtlichen Stadtteile. Die Geometrien werden als vier eigenständige Flächenlayer mit eigener transparenter Farbfüllung und sichtbarer Grenzlinie dargestellt; das Untersuchungsgebiet Nord ist eine zusätzliche Hervorhebung des Nordsektors.
