# Kurzleitfaden für die Seminarpräsentation

## Erzählstruktur

Vom räumlichen Systemverständnis über multimodale Verknüpfung und empirische Belastungsdaten hin zur Ableitung des strategischen Netzes. Die vier Aufgabenstellungen werden integriert und nicht nacheinander abgearbeitet.

## Karte 1 – Siedlungs- und Netzstruktur

- **Nutzungsstruktur / funktionale Dichte:** ALKIS-Ist-Nutzung (Wohn-, Arbeits-/Gewerbe-, Misch- und Sondernutzungen) mit Zensus-2022-Bevölkerungsraster.
- Aus dem Datensatz: ca. 182.673 Einwohner im 100-m-Zensusgitter; ca. 18,5 km² erfasste Wohnnutzungsflächen und ca. 12,1 km² ALKIS-Arbeits-/Gewerbe-/Funktionsflächen (Flächenwerte, keine Beschäftigtenzahlen).
- Räumliche Verteilung des Wohnflächenbestands nach den Arbeitssektoren: Nord 39,5 %, Ost 30,7 %, West 19,8 %, Süd 9,9 %. Der Zensus verteilt sich anders: Nord 27,5 %, Ost 40,0 %, West 19,9 %, Süd 12,6 %.
- **Netzhierarchie:** klassifiziertes Straßennetz (motorway/trunk/primary bis residential/service) und ÖPNV-Angebot aus VBB-GTFS (100 Linienkennungen im Untersuchungs-Ausschnitt: 80 Bus, 7 Tram, 4 S-Bahn, 9 Regionalverkehr).
- Fachbegriffe: *funktionale Nutzungsstruktur, Nutzungsmischung, Bevölkerungsdichte, Zentralität, Erreichbarkeit, Netzhierarchie, Angebotsqualität, multimodales Verkehrssystem*.

## Karte 2 – Verknüpfungspunkte und intermodale Schnittstellen

- Haltestellen-/Bahnhofslagen und Umsteigeknoten als **intermodale Verknüpfungspunkte** betrachten.
- GTFS-Transferbeziehungen, Wege/Zugänge (Pathways), Barrierefreiheitsattribute sowie P+R- und Fahrradabstellanlagen heranziehen.
- Wichtige Begriffe: *Umsteigewiderstand, Wegeketten, Intermodalität, Anschlussqualität, Knotenpunktfunktion, Erschließungsqualität, first/last mile*.
- ÖPNV-Angebot anhand der Fahrtenzahlen und HVZ-/NVZ-Intervalle beschreiben; Fahrplanangebot nicht mit Fahrgastnachfrage oder Auslastung gleichsetzen.

## Karte 3 – Empirische Verkehrsbelastung und modellierte Verkehrsbeziehungen

- **Kordonerhebung 2016:** eintägige Erhebung im Oktober 2016 an 13 wichtigen Ein-/Ausfallstraßen; zusätzlicher äußerer Kordon im Bereich A10/A115 und zwei Havelbrückenquerschnitte.
- An der Stadtgrenze: 191.709 Kfz-Erfassungen; 59 % pendelnde Verkehre (113.718 Erfassungen), 14 % Durchgangsverkehr (26.646 Erfassungen); 36 % bzw. etwa 70.554 Erfassungen an der Nuthestraße. Rund 96 % der Erfassungen waren Pkw. Havelbrücken: etwa 93.000 Kfz, darunter rund 9 % Durchgangsverkehr.
- Einschränkung: Kordonerhebung erfasst vor allem den regionalen Quell-, Ziel-, Pendel- und Durchgangsverkehr; der innerstädtische Binnenverkehr wurde – außer an den Havelbrücken – nicht erfasst.
- Lokale Verkehrszählungen/Stromlinienpläne zeigen an einzelnen Knoten die Zufahrtsbelastung nach Richtung und Zeitperiode. Die bisher integrierten drei Zählstellen sind ein erster Ausschnitt; nicht als flächendeckende Verkehrserhebung darstellen.
- Die Wohn-Arbeits-Verknüpfung ist eine **modellierte straßengebundene OD-Potenzialzuweisung** (kürzeste Wege / Dijkstra, Fahrzeitwiderstand, ALKIS-Flächen- und Zensus-Gewichte), keine beobachtete Pendler-OD-Matrix.
- Fachbegriffe: *Quellverkehr, Zielverkehr, Binnenverkehr, Durchgangsverkehr, Pendlerverflechtung, Kordon, Stromlinienplan, Spitzenstundenbelastung, Quelle-Ziel-Beziehung (OD), Widerstandsfunktion, Netzzuweisung, Streckenbelastung*.

## Karte 4 – Strategisches Netz und verkehrliche Priorisierung

- Straßenabschnitte werden aus modellierter OD-Segmentlast, Anzahl der durchlaufenden OD-Zonenpaare, Straßenhierarchie, Zählstellennähe und verfügbaren gemessenen Spitzenwerten priorisiert.
- Knotenpunkte werden über angrenzende Segmentlast, Knotengrad, Straßenhierarchie und Zählwerte bewertet. Die Rangfolge ist ein relativer Prioritätsindex, keine Kapazitäts- oder Qualitätsstufe.
- **Strategische ÖPNV-Verbindungen:** Schienenlinien (S-Bahn, Regionalverkehr, Tram) vollständig; Buslinien, die priorisierte Straßenabschnitte bzw. wichtige Knoten berühren. GTFS-Takte beschreiben Angebotsdichte, keine Fahrgast-Auslastung.
- Ableitung für das Verkehrsmanagement: kritische Korridore und Knoten als prioritäre Erfassungs- und Steuerungsräume; dort stationäre Sensorik (z. B. Radar/Induktionsschleifen/Signalsteuerungsdaten) mit mobilen Daten (FCD, ÖPNV-Echtzeit, Crowdsourcing) kombinieren.
- Fachbegriffe: *strategisches Netz, Netzwirkung, Engpass, Knotenleistungsfähigkeit, Korridor, räumliche Priorisierung, Verkehrsmanagement, Datenfusion, stationäre und mobile Detektion*.

## Übergangssatz / roter Faden

„Aus der funktionalen Siedlungsstruktur und der Hierarchie von Straße und ÖPNV ergeben sich zentrale Wegeketten und intermodale Knoten. Diese werden anschließend mit empirischen Zählungen und modellierten Quelle-Ziel-Potenzialen überlagert. Aus der kombinierten Betrachtung lassen sich jene Korridore und Knoten identifizieren, deren kontinuierliche Erfassung und gezielte Steuerung für die regionale Pendlerverflechtung und die innerstädtische Erreichbarkeit besonders relevant sind.“

## Sprechhinweise / methodische Vorsicht

- ALKIS-Flächen sind tatsächliche Nutzungsflächen, keine Beschäftigtenzahlen.
- Zensuswerte zählen Einwohner, sie liefern aber keine individuellen Pendlerwege oder Verkehrsmittelwahl.
- GTFS zeigt Fahrplanangebot, nicht Besetzungsgrad oder Nachfrage.
- Die lokale Zählstromlinie bildet Zufahrtsmengen ab, keine vollständig beobachteten Abbiege-OD-Ströme.
- Die Kordonerhebung 2016 bildet die Stadtgrenze und regionale Verkehrsbeziehungen ab, nicht den gesamten Potsdamer Binnenverkehr.
