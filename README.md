# Nord-Potsdam · Mobility Intelligence (Version 12)

Lokale, browserbasierte GIS-/Verkehrsmanagement-Anwendung für die Bestandsaufnahme und eine erste verkehrliche Potenzialanalyse in Potsdam. Das bestehende Layout (Fullscreen-Karte, schwebendes Layer-Menü, dynamische Legende) bleibt erhalten. Grunddaten liegen lokal unter `./data/`; es gibt bewusst **keine Datei-Upload-Funktion in der Webseite**.

## Starten

Im Projektordner:

```bash
python3 -m http.server 8001 --bind 127.0.0.1
```

Anschließend in Firefox öffnen: `http://127.0.0.1:8001/`. Alternativ funktioniert VS Code Live Server. Nicht per `file://` öffnen, da die Anwendung lokale GeoJSON- und JSON-Dateien mit `fetch()` lädt.

## Kartenansicht und räumliche Gliederung

- **Startmittelpunkt:** Landtag Brandenburg, Alter Markt 1, Potsdam (52.394623 N, 13.060371 E). Die vier Arbeitssektoren werden von dort durch diagonale 45°-Teilung gebildet. Es handelt sich um eine analytische Arbeitsgliederung, nicht um amtliche Stadtteile.
- **Räumliche Gliederung:** vier unabhängige, transparente Flächensektoren Nord/Ost/Süd/West, vom Landtag als Mittelpunkt in vier 45°-Richtungsbereiche geteilt und an der ALKIS-Stadtgrenze abgeschnitten. Das sind ausdrücklich keine amtlichen Stadtteilgrenzen. Die Sektorflächen sind keine Kachel- oder Wabenlayer.
- **Analysezonen:** Für die rechenintensive Wohn-Arbeits-Modellierung werden die ALKIS- und Zensuswerte in regelmäßigen quadratischen 400-m-Zonen aggregiert. Dies ist ein internes Berechnungsraster und muss nicht aktiviert werden.
- **ÖPNV-Abdeckung:** Für jede 100-m-Zelle wird die kürzeste Distanz zu einer GTFS-Haltestelle über ein OSM-Fußwegenetz mit Mehrquellen-Dijkstra berechnet. Zellen, die nicht auf das Netz snappen können, werden als Luftlinien-Fallback gekennzeichnet; verbundene Netzkomponenten ohne erreichbare Haltestelle werden separat als nicht verbunden markiert. Der Regler wirkt von 100 bis 1.000 m in 100-m-Schritten auf die Farbklassifizierung.

## Kartenmodi und Export

- **Minimal Dark:** schwarzer Hintergrund, filigrane helle Straßen, keine Hintergrundkacheln.
- **Klassisch:** OpenStreetMap-Kartenkacheln.
- **Satellit:** Esri World Imagery mit Quellenangabe.
- **PNG-Export:** Exportiert den sichtbaren Kartenausschnitt mit aktuell aktivierten Kartenlayern und dynamischer Legende in dreifacher Bildschirmauflösung. Externe Kacheldienste müssen CORS zulassen; bei einem CORS-Fehler kann Minimal Dark ohne fremde Kacheln verwendet werden.
- **Sensoren:** Das Plus unter dem Export öffnet ein Formular. Nach Eingabe der Eigenschaften wird der Standort per Kartenklick gesetzt. Marker können verschoben, bearbeitet und gelöscht werden. Die Sensoren werden lokal in `localStorage` des jeweiligen Browsers gespeichert, nicht auf einen Server hochgeladen und nicht automatisch in einem anderen Browser übernommen.

## Mitgelieferte Grunddaten

### ALKIS · tatsächliche Nutzung

Die Daten stammen aus den bereitgestellten vollständigen Shapefiles `Nutzung.*` und `VerwaltungsEinheit.*` und wurden nach GeoJSON/WGS84 umprojiziert und thematisch aufgeteilt. Der Flächennutzungsplan wird nicht verwendet.

Wesentliche Layer: Wohnflächen, Arbeits-/Gewerbestandorte, gemischte Nutzung, besondere funktionale Prägung, Versorgung/soziale Infrastruktur, Bildung, Grün- und Erholungsflächen, Parkflächen und Bahnanlagen. ALKIS-Flächennutzung ist ein IST-Zustandsindikator. Flächengröße ist weder Einwohnerzahl noch Beschäftigtenzahl. POI-Punkte aus ALKIS sind repräsentative Flächenschwerpunkte und keine zwingend exakten Gebäudeadressen.

### Zensus 2022 · 100-m-Gitter

Aus den beiden bereitgestellten Zensus-ZIPs wurden Zellen übernommen, deren Gittermittelpunkt innerhalb der Potsdamer Verwaltungsgrenze liegt. Die Gitterdaten wurden aus EPSG:3035 nach WGS84 umgerechnet.

- `zensus2022_bevoelkerung_100m.geojson`: 3.411 Bevölkerungszellen; Einwohnerzahl und abgeleitete Einwohner/km².
- `zensus2022_wohngebaeude_100m.geojson`: 2.869 Zellen; Zahl der Wohngebäude sowie verfügbare Verteilung nach Zahl der Wohnungen je Gebäude.

Die Einwohner/km²-Angabe bezieht sich auf die ursprüngliche 100 × 100 m-Zensus-Gitterzelle (0,01 km²), nicht auf eine gegebenenfalls an der Stadtgrenze beschnittene Kartenfläche. Zensus-Referenzjahr: 2022.

### VBB GTFS

Regional zugeschnittener lokaler Ausschnitt aus der bereitgestellten GTFS-Datei. Enthält Liniengeometrien, Halte-/Bahnsteigobjekte, Umsteigeverbindungen und Zugangs-/Wegedaten. Die Taktwerte sind aus dem GTFS-Fahrplan für einen Referenzwerktag abgeleitete Medianabstände erster Abfahrten. HVZ morgens: 06–09 Uhr; HVZ nachmittags: 15–19 Uhr; NVZ: 09–15 Uhr. Es handelt sich nicht um Echtzeitdaten. Tramlinien und Haltestellensymbole sind rot.

### Verkehrszählstellen und ausgewertete Zählplan-PDFs

Das Register enthält 426 Zählstellen und 215 direkte Links auf ZIP-Archive. Die Registerdatei selbst enthält keine Verkehrsmengen. Die ZIP-Archive enthalten Stromlinienplan-PDFs mit Zählergebnissen. Der lokale Downloader `tools/download_traffic_counts.py` lädt die verlinkten ZIPs, extrahiert PDFs und erstellt CSV-/GeoJSON-Auswertungen. Die erste PDF-Seite enthält häufig Frühspitze (FSp), Nachmittagsspitze (NSp), Summe der sechs Erhebungsstunden (6h) sowie Fahrzeug-/Zufahrtsangaben.

Aufgrund der Datenqualität sind extrahierte Tabellenwerte stichprobenartig mit Original-PDFs zu kontrollieren. OCR-Ergebnisse sind als solche markiert. Die im Projekt enthaltenen Messwerte stammen von bereits verarbeiteten Archiven; der aktuelle Umfang kann durch erneuten Skriptlauf erweitert werden.

#### Alle Zählplan-Archive automatisiert herunterladen und auswerten

Auf Fedora benötigte Programme:

```bash
sudo dnf install poppler-utils tesseract tesseract-langpack-deu
```

Im Projektordner:

```bash
python3 tools/download_traffic_counts.py
```

Nur bereits vorhandene Archive neu auswerten:

```bash
python3 tools/download_traffic_counts.py --no-download
```

Die Ergebnisse liegen in `data/traffic_archives/`, `data/traffic_pdfs/`, `data/traffic_text/`, `data/traffic_measurements.csv` und `data/verkehrszahlungen_messwerte.geojson`. Fehlgeschlagene Links werden protokolliert und können bei einem späteren Lauf erneut versucht werden. Die Anwendung liest die lokale GeoJSON-Datei beim Neuladen ein.

## Analyse und Priorisierung · Wohn-Arbeits-Modell

Die drei Ebenen **Wohn-Arbeits-Verknüpfung**, **Strategisch wichtige Straßenabschnitte** und **Wichtige Knotenpunkte** werden beim Start nach dem Laden des OSM-Straßennetzes dynamisch berechnet. Die Berechnung läuft in `tools/transport_model_worker.js` als Web Worker, damit die Kartenoberfläche währenddessen bedienbar bleibt. Über **Analyse neu berechnen** kann sie erneut gestartet werden.

### Räumliche Eingangsdaten

1. Die ALKIS-Wohnflächen werden mit dem Zensus-100-m-Gitter auf ein quadratisches 400-m-Analyse-Raster aggregiert. Zensus-Einwohnerzahlen dienen als Wohngewicht; bei Rasterzonen ohne Einwohnerzahl wird die ALKIS-Wohnfläche als Ersatzproxy verwendet.
2. Alle 400-m-Zonen mit Wohnpotenzial werden als Startzonen berücksichtigt.
3. Alle 400-m-Zonen mit mehr als 300 m² ALKIS-Arbeits-/Gewerbe-Potenzialfläche werden als Zielzonen berücksichtigt. Das ALKIS-Arbeitsflächen-Subset enthält Industrie/Gewerbe, Handel/Dienstleistung sowie verschiedene besondere funktionale Nutzungen, z. B. Bildung, Gesundheit, Verwaltung, Kultur und Soziales.
4. Start- und Zielzonen werden jeweils dem nächstgelegenen routbaren OSM-Straßenknoten zugeordnet, sofern der Abstand höchstens 1.000 m beträgt. Zonen am gleichen Netzknoten werden gruppiert und ihre Gewichte summiert.

### Straßengebundene Verkehrsströme

- Der gerichtete Straßengraph besteht aus den geladenen OSM-Kfz-Straßenabschnitten. Einbahnstraßen und `oneway=-1` werden berücksichtigt. Fahrzeitkosten werden aus OSM-Geschwindigkeitsangaben oder typisierten Standardgeschwindigkeiten angenähert.
- Für jeden eindeutigen Wohnzugang wird ein Dijkstra-Kürzeste-Wege-Baum im Straßengraph berechnet. Jede erreichbare Wohn-Ziel-Kombination innerhalb von maximal 10.800 Sekunden (3 h modellierte Fahrzeit) trägt zum OD-Potenzial bei.
- Das Zielgewicht basiert auf der ALKIS-Arbeitsfläche; das Startgewicht auf Zensus-Einwohnern bzw. ALKIS-Wohnfläche. Eine glatte Fahrzeitabnahme reduziert das Gewicht längerer Verbindungen.
- Statt für jede OD-Verbindung den vollständigen Weg separat zu speichern, werden die Zielgewichte im Kürzeste-Wege-Baum rückwärts von den Zielknoten zum jeweiligen Startknoten propagiert. Dadurch wird für jedes einzelne OSM-Straßensegment sowohl die Summe der gewichteten OD-Potenziale als auch die Zahl der durchlaufenden 400-m-OD-Zonenpaare berechnet.
- Der Layer **Wohn-Arbeits-Verknüpfung** zeichnet alle Straßensegmente mit positivem aggregiertem Potenzial. Strichbreite und Deckkraft kombinieren gewichtetes Potenzial und Zahl der OD-Zonenpaare. Popups zeigen beide Kennwerte. Es sind straßengebundene aggregierte Stromlinien, nicht einzelne Luftlinien zwischen Flächenmittelpunkten.

### Strategische Straßenabschnitte und Knoten

- Die Priorisierung wird nach Abschluss der OD-Berechnung neu aus den Segmentlasten berechnet.
- Die Straßenbewertung kombiniert gewichtetes OD-Potenzial, Zahl der OD-Zonenpaare, OSM-Straßenhierarchie, Nähe zu Zählstellen und – sofern vorhanden – die zuletzt verfügbare Spitzenzählung je KPNR aus den ausgewerteten Stromlinienplan-PDFs.
- Als Kandidaten gelten alle positiv belasteten Straßensegmente sowie Segmente direkt an Zählstellenknoten. Sichtbar sind die höchstbewerteten 5 % der Kandidaten, maximal 180 Abschnitte.
- Knoten werden anhand der angrenzenden Segmentlast, Knotengrad, Straßenhierarchie und verfügbarer Zählwerte bewertet; dargestellt werden maximal 45 Knoten.
- Kfz-Spitzenwerte werden auf die nahegelegenen Netzknoten übertragen und beeinflussen die Priorisierung dort angrenzender Segmente. Zählstellen ohne Messbericht liefern nur einen qualitativen Standort-Hinweis.

### Methodische Grenzen

Das ist ein **Potenzialmodell**, keine kalibrierte Verkehrsprognose und keine gemessene Quelle-Ziel-Matrix. ALKIS-Arbeitsfläche ist kein Beschäftigtenbestand; es liegen keine Beschäftigtenzahlen je Zielzone, keine individuelle Verkehrsmittelwahl und keine beobachteten Pendlerwege vor. Die modellierten Linien zeigen relative, fahrzeitgewichtete Potenziale. Sie dürfen nicht als tatsächliche Fahrzeugmengen, Pendlerzahlen oder Kapazitätsauslastung interpretiert werden. Für eine belastbare Verkehrszuweisung wären Beschäftigten-/Pendlerdaten, SrV-/MiD-Ergebnisse, ein empirisches Quelle-Ziel-Modell oder eine Kalibrierung anhand ausreichender richtungsbezogener Zählwerte erforderlich.

## OSM, Kartenkacheln und technische Hinweise

- Straßen, Schienen, Lichtsignalanlagen, Querungsstellen und ergänzende POI werden zur Laufzeit über Overpass abgefragt. Internetverbindung erforderlich.
- Die Hintergrundkarten benötigen Zugriff auf OSM- bzw. Esri-Kacheldienste.
- PNG-Export nutzt `html2canvas` über CDN. Externe Kacheldienste müssen CORS zulassen; andernfalls Minimal Dark verwenden.
- Sensorstandorte werden ausschließlich in der lokalen Browser-`localStorage` gespeichert.
- OSM-Daten stehen unter ODbL; die OpenStreetMap-Attribution wird angezeigt. Esri World Imagery wird mit Quellenangabe dargestellt.
- Die Anwendung ist ein Analyseprototyp. OSM-Vollständigkeit, Zensus-Aggregation, ALKIS-Kategorien, Fahrzeitannahmen und Modellgewichte sollten für eine Abgabe dokumentiert und stichprobenartig in QGIS/anhand der Originalquellen validiert werden.

## Versionshistorie und aktuelle Funktionen

- Straßengebundene all-to-all-Potenzialverknüpfung: alle angebundenen Wohnzonen werden mit allen Arbeitszielzonen gepaart, soweit die Verbindung im gerichteten OSM-Straßennetz innerhalb des 3-h-Suchhorizonts erreichbar ist.
- Dijkstra-Kürzeste-Wege-Bäume werden im Web Worker berechnet; Zielpotenziale werden rückwärts über Baumkanten aggregiert. Der Flow-Layer zeichnet jeden positiv belasteten OSM-Straßenabschnitt.
- Strategisches Netz: dynamische Top-5-%-Auswahl (maximal 180 Abschnitte) und bis zu 45 bewertete Knoten. Modellfluss, Straßentyp und verfügbare Zählmessungen gehen in die Bewertung ein.
- Berechnung kann über „Analyse neu berechnen“ erneut gestartet werden. Fortschritt erscheint direkt im Layer-Menü/Statusfeld.
- 100-m-Kacheln und 400-m-Analysezonen sind quadratisch; die vorherige Hexagon-/Wabenstruktur ist entfernt.
- Startmittelpunkt und Sektorbezug: Landtag Brandenburg.
- Tramlinien und Tram-Haltestellen sind rot.
- Sensorplanung: frei platzierbare, verschiebbare, editierbare Sensoren mit lokalem Browser-Speicher.


## Version 9 – räumliche Gliederung, Statusanzeigen und Kartenwerkzeuge

- Das 100-m-Quadratraster ist kein dauerhaft sichtbarer Layer mehr. Es wird intern für Zensus-/Abdeckungsdaten geführt und nur beim aktivierten Layer „ÖPNV-Abdeckung“ gezeichnet.
- Die vier Sektoren werden als zusammenhängende, transparent eingefärbte Flächen mit den 45°-Trennlinien vom Landtag dargestellt; es gibt keine sichtbaren Kachelgrenzen in der räumlichen Gliederung.
- Statusanzeigen sind auf kompakte Einzeilenansichten begrenzt. OD-Zonenzahlen werden auf die maximal mögliche Zahl erreichbarer Paare begrenzt, um fehlerhafte Überläufe aus der Aggregation nicht in die UI zu geben.
- Neuer Werkzeugkasten: Distanzmessung per zwei Kartenklicks sowie Freihandzeichnung. Zeichnungen lassen sich rückgängig machen, einzeln über den Radierer entfernen oder vollständig löschen. Zeichnungen werden lokal im Browser gespeichert.
- Die Distanzmessung zeigt die Karten-/Luftliniendistanz zwischen den gewählten Punkten; sie ist keine Straßennetz-Reiseweite.


## Version 10 – Darstellung und Performance strategischer Abschnitte

- Sektorflächen Nord/Ost/Süd/West erhalten wieder gut erkennbare, transparente Farbfüllungen mit klaren Grenzlinien; es werden keine Kacheln/Waben gezeichnet. Das separate Untersuchungsgebiet Nord ist stärker blau transparent hervorgehoben.
- Wohn-Arbeits-Stromlinien sind schmaler und transparenter dargestellt, damit sie das Straßennetz weniger überdecken.
- Strategische Segmente werden nicht mehr als Hunderte einzelner Leaflet-Canvas-Renderer erzeugt. Stattdessen werden die ausgewählten Segmente als eine GeoJSON-FeatureCollection mit einem gemeinsamen Canvas-Renderer gezeichnet. Dies behebt die wesentliche Rendering-Last beim Aktivieren des Layers.
- Kandidaten werden effizient aus bereits belasteten OD-Segmenten und unmittelbar an Zählstellenknoten angrenzenden Kanten gebildet. Die sichtbare Auswahl ist auf die Top 3,5 % (maximal 160 Segmente) begrenzt.
- JavaScript-Syntax von Anwendung und Worker sowie die ZIP-Integrität wurden geprüft. Ein vollständiger Live-Rendering-Test mit dem gesamten OSM-Netz ist in der Erstellungsumgebung nicht möglich.


## Version 11 – räumliche Sektoren, Zählstromlinien und strategischer ÖPNV

- Die vier Arbeitssektoren sind als vorgefertigte, an der ALKIS-Stadtgrenze Potsdam geclippte GeoJSON-Flächen enthalten (`data/sektoren_potsdam_landtag.geojson`). Mittelpunkt ist der Landtag; die Sektoren sind reine Himmelsrichtungszonen, keine amtlichen Stadtteile.
- Neuer Layer „Stromlinien aus Verkehrszählungen“: Zufahrtswerte je Himmelsrichtung aus den lokal ausgewerteten Zählplan-PDFs werden an den nächsten OSM-Netzknoten gebunden und auf den zugehörigen Straßenarm projiziert. Linienbreite basiert auf Kfz/6h. Es handelt sich nicht um Abbiege- oder Quelle-Ziel-Matrizen.
- Neuer Layer „Strategisch wichtige ÖPNV-Verbindungen“: Alle GTFS-Schienenlinien (S-Bahn, Regionalverkehr, Tram) werden dargestellt. Buslinien werden nur bei substantieller räumlicher Überlagerung berücksichtigt: mindestens 2,6 km und 20 % Streckenanteil sowie mindestens 3 strategische Knoten; alternativ mindestens 4,2 km, 16 % und 2 Knoten. Es werden maximal vier Buslinien mit dem höchsten Überlagerungswert aufgenommen. Schienenlinien bleiben vollständig enthalten. GTFS-Fahrten-/Taktinformationen werden als Angebotsmetriken genutzt; Fahrgast-Auslastung liegt nicht vor.
- Die Berechnungsdokumentation steht unter `docs/methodik_strategisches_netz.md`; ein kompakter Sprechleitfaden unter `docs/praesentationsleitfaden.md`.


## Version 12 · Stabilisierung der Sektoren, Abdeckung und Linieninteraktion

- Die vier Sektorpolygone werden explizit als Leaflet-Polygone mit eigenem SVG-Renderer und separater Kartenebene gezeichnet. Jedes der vier Layer ist unabhängig schaltbar; das Untersuchungsgebiet Nord ist eine zusätzliche Hervorhebung des Nordsektors.
- Die Sektorgeometrien sind valide und wurden gegen die ALKIS-Stadtgrenze geprüft: Die Vereinigungsfläche der vier Sektoren deckt die Stadtfläche praktisch vollständig ab. Die Sektoren sind geometrische 45°-Arbeitsbereiche ab Landtag, keine realen Verwaltungs- oder Stadtteilgrenzen.
- ÖPNV-Linien sind in allen aktiven ÖV-Layern anklickbar. Die Auswahl hebt alle Geometrieabschnitte einer Linien-ID hervor; Schließen des Popups, Kartenklick auf freie Fläche oder Deaktivierung aller ÖV-Linienfilter hebt die Auswahl auf. Beim Zurücksetzen werden die ursprünglichen Styles des jeweiligen Layers wiederhergestellt.
- Strategische Buslinien: Schwellenwerte gegenüber Version 11 verschärft; maximal vier Buslinien, ausgewählt nach tatsächlicher geometrischer Überlagerung mit strategischen Straßenabschnitten und Knoten. S-Bahn, Regionalverkehr und Tram bleiben vollständig enthalten.
- Fußläufige Haltestellenabdeckung: Mehrquellen-Dijkstra im OSM-Fußwegenetz; Statusanzeige dokumentiert angebundene Haltestellen, Anzahl Netzpunkte sowie Netz-/Fallback-/Nichtverbindungszellen.
- Das Lineal bietet „Zurück“ (letzten Messpunkt entfernen) und „Reset“ (alle Messpunkte entfernen).
