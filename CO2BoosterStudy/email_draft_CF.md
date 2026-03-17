# Email-Entwurf an Herr Lötzsch

**An:** Lötzsch, Benaja  
**CC:** Winter, Simon; Valentin Koch  
**Betreff:** AW: Ecalia x Christof Fischer — Ergebnisse Expander-Potentialanalyse  

---

Guten Tag Herr Lötzsch,

vielen Dank für die Betriebspunkte und die detaillierten BITZER-Auslegungen — damit konnten wir eine saubere thermodynamische Analyse aufsetzen.

Anbei die Ergebnisse als PDF. Kurz zusammengefasst zu Ihren Punkten:

## 1. COP-Vergleich vs. Parallelverdichter

Wir haben alle Ihre Betriebspunkte (Hochsommer, Übergang, WRG, Winter) durchgerechnet und η_s pro Betriebspunkt an Ihre BITZER-Baseline kalibriert — die Baseline-COPs stimmen daher exakt überein. Alle Expander-Konfigurationen laufen bei p_med = 43 bar (= PV-Mitteldruck) mit IWT vor Expander für einen fairen Vergleich.

Hochsommer-Ergebnisse (transkritisch, Baseline COP = 1.56):

| Konfiguration | COP | Δ COP | ΔE [MWh/a] | Ersparnis [€/a] |
|---|---|---|---|---|
| Baseline (V+V) | 1.56 | — | — | — |
| **MD-Expander** | **1.73** | **+11 %** | 15.6 | 3 400 |
| HD-Expander | 1.79 | +15 % | 19.5 | 4 300 |
| HD + MD Kombi | 1.97 | +26 % | 32.8 | 7 200 |
| PV (BITZER Ref.)† | 1.88 | +20 % | 25.1 | 5 500 |
| PV + HD-Exp† | 2.17 | +39 % | 42.1 | 9 300 |


### Thermodynamisches Limit des Expanders

Wichtig zum Einordnen: Selbst bei einem idealen Expander (η = 1.0, isentrop) erreicht der MD-Expander maximal +15 % COP-Verbesserung — der PV kommt bei η = 0.70 bereits auf +20 %. Der Parallelverdichter ist thermodynamisch also überlegen, weil er den gesamten Flashgas-Massenstrom in einem kälteren Zustand verdichtet. Die Hauptstufe muss einen höheren Druckhub leisten, damit ist die mittlere Temeratur des Gases höher, was zu einem nichtlinearen Arbeitsanstieg führt. 

Erst in der HD+MD-Kombination (η = 1.0: +41 %) überholt der Expander den PV — dann wird allerdings sowohl die HD- als auch die MD-Drossel ersetzt.

## 2. Jahresenergiekosten

Im Report ist eine Jahresbetrachtung über alle 4 Betriebspunkte. Für die Betriebsstunden haben wir mal geschätzt (Hochsommer 800 h, Übergang 3 160 h, WRG 2 000 h, Winter 2 800 h), aber korrigieren Sie uns gerne wenn das abweicht. Wir haben auch die Stromkosten mal abgeschätzt und zwei Szenarien berücksichtigt: reiner Netzbezug (0.22 €/kWh) und Supermarkt mit Dach-PV (0.16–0.22 €/kWh saisonabhängig). Wie beim letzten Mal auch schon von Ihnen erwähnt, das Dach-PV senkt den Sommerstrompreis → PV-Kompressor spart genau dann, wenn Strom ohnehin günstig ist. Der Expander dagegen spart ganzjährig, auch im Winter bei vollem Netzbezugspreis.

## 3. IWT-Position

Wir haben beide IWT-Positionen verglichen: IWT *vor* Expander vs. IWT *nach* Expander. Empfehlung: **IWT vor Expander**. Das Flashgas wird im IWT auf Mitteldruckniveau so weit überhitzt, dass der Expanderaustritt dieselbe Überhitzung wie die Baseline-Saugleitung aufweist. 

Falls die benötigte IWT-Fläche zu groß wird (Überhitzung bis ~29 °C bei 43 bar im Hochsommer), kann alternativ nach der Expansion wärmegetauscht werden — dann bei teils flüssiger Phase (hydraulisch einfacher), aber ca. −0.5 % COP. Der Expander muss dann mit der Tröpfchenbildung klarkommen, aber da sind wir zuversichtlich.

## 4. Ihre angefragten Infos

### Rückgewinnungsgrad
Wir rechnen konservativ mit η_exp = 0.70 (isentrop). Der MD-Expander gewinnt damit ca. 3.1 kW zurück, der HD-Expander ca. 5.9 kW. Zusammen (HD+MD) sind es knapp 8 kW Rückgewinnung.

### Flüssigkeitsanteil nach Expansion
Im Fall, dass der IWT vor dem Expander ist, sollten sich bei der Expansion kein Flüssigkeitsanteil bilden. Für den Dampfgehalt am Austritt HPEV (Eintritt Sammler) bedeutet das:
- Baseline (Ventil): x = 0.45 → 55 % Flüssigkeit
- HD-Exp: x = 0.41 → 59 % Flüssigkeit

Durch den Expander entsteht etwas *mehr* Flüssigkeit (weniger Flashgas), weil die Enthalpie am Eintritt in den Sammler niedriger ist, aber das ist hier ja gewünscht.

im Fall, dass der IWT nach dem Expander geschalten ist, liegt der Flüssigkeitsanteil am Expanderaustritt bei

### Regelbereich
Hier müssen wir ehrlicherweise noch Erfahrungen sammeln. Der Scroll-Expander ist drehzahlgeregelt, genaues Teillastverhalten muss im Prüfstandsbetrieb verifiziert werden. Vermutlich werden wir im unteren Prozentbereich kaum noch Elektrizität generieren können da wir viel Druck aufgrund von Leckage verlieren. Da sich das über die mehreren Spiralwicklungen verteilt sollte die Funktionalität aber nicht beeinträchtigt sein, eventuell wird die Regelung hier aber etwas komplexer.

### Optimale Druckdifferenz
Im Report haben wir den Druckbereich von 30–48 bar durchgespielt. wie beim Parallelverdichter steigt der MD-Expander-Vorteil mit dem Druckverhältnis. 

## 5. Anforderungen an den Expander

### Druckfestigkeit
- MD-Pos. (43 bar): Ihre Anforderung min. 60, besser 80 bar → machbar.

Wenn Sie Feedback zu den Berechnungen haben oder Ihnen was auffällt, gern melden.

Mit besten Grüßen  
Michael Ilewicz & Valentin Koch  
Ecalia GmbH
