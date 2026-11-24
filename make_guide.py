# Builds the student guide PDF for the Handportal-Lampe.
import sys, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, KeepTogether, Flowable)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon

OUT = sys.argv[1]
F = r"C:\Windows\Fonts"
pdfmetrics.registerFont(TTFont("Arial", os.path.join(F, "arial.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Bold", os.path.join(F, "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Italic", os.path.join(F, "ariali.ttf")))
pdfmetrics.registerFont(TTFont("Mono", os.path.join(F, "consola.ttf")))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-Bold")

INK = colors.HexColor("#1f2933")
MUTED = colors.HexColor("#52606d")
ACCENT = colors.HexColor("#0b6e69")
ACCENT_BG = colors.HexColor("#e6f4f3")
WARN = colors.HexColor("#9a5b00")
WARN_BG = colors.HexColor("#fff4e0")
LINE = colors.HexColor("#d3dae0")
CODE_BG = colors.HexColor("#f2f4f6")

base = dict(fontName="Arial", textColor=INK, leading=15, fontSize=10.5)
S = {
    "title": ParagraphStyle("title", **{**base, "fontName": "Arial-Bold", "fontSize": 26, "leading": 31, "textColor": ACCENT}),
    "subtitle": ParagraphStyle("subtitle", **{**base, "fontSize": 13, "leading": 18, "textColor": MUTED}),
    "h1": ParagraphStyle("h1", **{**base, "fontName": "Arial-Bold", "fontSize": 17, "leading": 22, "textColor": ACCENT, "spaceBefore": 4, "spaceAfter": 8}),
    "h2": ParagraphStyle("h2", **{**base, "fontName": "Arial-Bold", "fontSize": 12.5, "leading": 17, "spaceBefore": 10, "spaceAfter": 4}),
    "body": ParagraphStyle("body", **{**base, "spaceAfter": 6}),
    "small": ParagraphStyle("small", **{**base, "fontSize": 9, "leading": 12, "textColor": MUTED}),
    "cell": ParagraphStyle("cell", **{**base, "fontSize": 9.5, "leading": 12.5}),
    "cellb": ParagraphStyle("cellb", **{**base, "fontName": "Arial-Bold", "fontSize": 9.5, "leading": 12.5}),
    "head": ParagraphStyle("head", **{**base, "fontName": "Arial-Bold", "fontSize": 9.5, "leading": 12.5, "textColor": colors.white}),
    "code": ParagraphStyle("code", **{**base, "fontName": "Mono", "fontSize": 9.5, "leading": 13}),
    "step_no": ParagraphStyle("step_no", **{**base, "fontName": "Arial-Bold", "fontSize": 14, "leading": 16, "textColor": colors.white, "alignment": TA_CENTER}),
}


def p(text, style="body"):
    return Paragraph(text, S[style])


def code(text):
    return f'<font name="Mono" size="9">{text}</font>'


def box(flowables, bg=ACCENT_BG, border=ACCENT, title=None):
    content = ([p(f"<b>{title}</b>")] if title else []) + flowables
    t = Table([[content]], colWidths=[170 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, border),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return t


def codebox(lines, width=150):
    t = Table([[p("<br/>".join(lines), "code")]], colWidths=[width * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CODE_BG), ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t


def table(header, rows, widths):
    data = [[p(h, "head") for h in header]] + [[p(c, "cellb" if i == 0 else "cell") for i, c in enumerate(r)] for r in rows]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), ACCENT), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fa")]),
                           ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
                           ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                           ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)]))
    return t


def badge(n):
    b = Table([[p(str(n), "step_no")]], colWidths=[8 * mm], rowHeights=[8 * mm])
    b.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACCENT), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                           ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return b


def steps(items):
    rows = [[badge(i), [p(f"<b>{title}</b>")] + body] for i, (title, body) in enumerate(items, 1)]
    t = Table(rows, colWidths=[10 * mm, 160 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (0, -1), 0),
                           ("LEFTPADDING", (1, 0), (1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 3),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return t


def flow_diagram():
    """Camera -> PC -> Mosquitto -> zigbee2mqtt -> USB stick -> lamp, as boxes with arrows."""
    w, h = 170 * mm, 62 * mm
    d = Drawing(w, h)
    boxes = [("Kamera", "filmt den Rahmen"), ("PC + Programm", "erkennt die Hand"),
             ("Mosquitto", "Postbote für\nNachrichten"), ("zigbee2mqtt", "übersetzt in\nZigbee-Funk"),
             ("USB-Funkstick", "sendet per Funk"), ("IKEA-Lampe", "geht an / aus")]
    bw, bh, gap = 25 * mm, 24 * mm, (w - 6 * 25 * mm) / 5
    y = 26 * mm
    for i, (name, sub) in enumerate(boxes):
        x = i * (bw + gap)
        fill = ACCENT if i in (1, 5) else ACCENT_BG
        txt = colors.white if i in (1, 5) else INK
        d.add(Rect(x, y, bw, bh, rx=3, ry=3, fillColor=fill, strokeColor=ACCENT, strokeWidth=1))
        d.add(String(x + bw / 2, y + bh - 9 * mm + 2, name, fontName="Arial-Bold", fontSize=8.5, fillColor=txt, textAnchor="middle"))
        for j, line in enumerate(sub.split("\n")):
            d.add(String(x + bw / 2, y + bh - 14 * mm - j * 3.6 * mm + 2, line, fontName="Arial", fontSize=7, fillColor=txt, textAnchor="middle"))
        if i < 5:
            ax = x + bw + 1.5
            d.add(Line(ax, y + bh / 2, ax + gap - 4, y + bh / 2, strokeColor=ACCENT, strokeWidth=1.4))
            d.add(Polygon([ax + gap - 4, y + bh / 2 + 3, ax + gap - 1, y + bh / 2, ax + gap - 4, y + bh / 2 - 3], fillColor=ACCENT, strokeColor=ACCENT))
    # what travels over each link
    labels = ["Video (USB)", "", "MQTT-Nachricht", "", "Zigbee-Funk"]
    for i, lab in enumerate(labels):
        if lab:
            x = i * (bw + gap) + bw + gap / 2
            d.add(String(x, y - 6 * mm, lab, fontName="Arial", fontSize=7, fillColor=MUTED, textAnchor="middle"))
    d.add(String(0, 6 * mm, "Alles außer der Lampe läuft am PC. Die Lampe bekommt den Befehl per Funk, ganz ohne Kabel.",
                 fontName="Arial-Italic", fontSize=8.5, fillColor=MUTED))
    return d


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Arial", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 12 * mm, "Handportal-Lampe · Anleitung für Betreuer:innen")
    canvas.drawRightString(190 * mm, 12 * mm, f"Seite {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.line(20 * mm, 16 * mm, 190 * mm, 16 * mm)
    canvas.restoreState()


story = []

# ---------- Page 1: what is it ----------
story += [Spacer(1, 6 * mm), p("Handportal-Lampe", "title"),
          p("Anleitung zum Erklären, Starten und Fehlerbeheben", "subtitle"), Spacer(1, 6 * mm)]
story.append(box([p("<b>Kamera, Lampe, Beamer und Tisch NICHT bewegen!</b> Das Programm hat sich beim Start gemerkt, "
                    "wo alles steht. Wird etwas verschoben, stimmt die Erkennung nicht mehr."),
                  p("Der <b>Rahmen</b> darf nur im Notfall bewegt werden.")],
                 bg=WARN_BG, border=WARN, title="Wenn das System läuft:"))
story.append(Spacer(1, 4 * mm))
story.append(box([p("Man steckt die Hand durch einen Bilderrahmen. Eine Kamera sieht die Hand, "
                    "der Computer erkennt sie, und eine Lampe schaltet sich ein oder aus. "
                    "Ohne Schalter, ohne Berührung.")], title="In einem Satz"))
story += [Spacer(1, 6 * mm), p("So erklärst du es Besuchern", "h1"),
          p("Du musst nichts Technisches sagen. Diese drei Sätze reichen:")]
story.append(steps([
    ("„Die Kamera hat sich gemerkt, wie der leere Rahmen aussieht.“",
     [p("Am Anfang macht der Computer ein „Foto“ vom leeren Rahmen und der Wand dahinter.")]),
    ("„Wenn deine Hand reinkommt, sieht der Computer, dass sich etwas verändert hat.“",
     [p("Er schaut auf zwei Dinge: Hat sich die <b>Farbe</b> verändert? Und ist da etwas <b>näher</b> als die Wand? "
        "Das Zweite schätzt eine künstliche Intelligenz (KI) aus dem Kamerabild.")]),
    ("„Ist deine Hand über der Lampe, schickt der Computer per Funk einen Befehl an die Lampe.“",
     [p("Die Lampe ist eine normale IKEA-Smart-Lampe. Sie bekommt den Befehl „umschalten“ über Zigbee, "
        "eine Funktechnik ähnlich wie WLAN, nur für Smart-Home-Geräte.")]),
]))
story += [Spacer(1, 4 * mm), p("Das ganze System auf einen Blick", "h2"), flow_diagram()]
story.append(PageBreak())

# ---------- Technical explanation ----------
story.append(p("So erklärst du es Technik-Interessierten", "h1"))
story.append(p("Für Besucher, die genauer wissen wollen, was passiert. Das läuft für jedes Kamerabild ab, "
               "ungefähr <b>20-mal pro Sekunde</b>:"))
story.append(table(["Schritt", "Was passiert", "Technik dahinter"], [
    ["1. Bild aufnehmen", "Die Kamera liefert 1280×720 Pixel. Das Bild wird auf 640×360 verkleinert, damit die Rechnung schneller ist.",
     "USB-Webcam, MJPG, feste Belichtung 1/128 s (weniger Bewegungsunschärfe, Farben bleiben gleich)"],
    ["2. Farbe vergleichen", "Jeder Pixel wird mit einem Referenzbild vom leeren Rahmen verglichen. Ist die Farbe deutlich anders, ist dort etwas Neues.",
     "Hintergrund-Subtraktion: Differenz zum Median aus 20 Startbildern, Schwelle 30 von 255, Medianfilter gegen Rauschen"],
    ["3. Entfernung schätzen", "Eine KI schätzt aus einem einzigen Bild, wie weit jeder Pixel weg ist, ganz ohne 3D-Kamera.",
     "<i>Depth Anything V2 Small</i>: Vision Transformer (DINOv2-Encoder, DPT-Decoder), zerlegt das Bild in 14×14-Pixel-Kacheln. Läuft auf der Grafikkarte (CUDA, FP16)"],
    ["4. Schwankungen ausgleichen", "Die KI liefert nur <i>relative</i> Werte, die von Bild zu Bild etwas anders skaliert sind. Das wird korrigiert.",
     "Lineare Regression (kleinste Quadrate) von Skala und Versatz auf Hintergrund-Pixeln, die Hand wird dabei ausgeschlossen"],
    ["5. Kombinieren", "Ein Pixel zählt nur, wenn er mindestens 15&nbsp;% näher als die Wand ist <b>und</b> seine Farbe verändert hat.",
     "Logisches UND aus Tiefen- und Farbmaske: Schatten (nur Farbe) und KI-Fehler auf glatten Flächen (nur Tiefe) fallen weg"],
    ["6. Anzeigen", "Das Tiefenbild der KI wird auf ein kleines Raster verkleinert und wieder vergrößert. "
     "Die Lücken dazwischen bleiben schwarz. So entsteht der Retro-Pixel-Look am Beamer.",
     "Nur jeder 5. Wert wird behalten (kleines Array). Beim Hochskalieren wird jeder Wert zu einem 10×10-Block, "
     "die restlichen Einträge werden mit 0 befüllt (NumPy <i>kron</i>)"],
    ["7. Auslösen", "Ist im Feld über der Lampe 0,3 s lang etwas, wird einmal geschaltet. Erst nach 0,5 s ohne Hand geht es wieder.",
     "Entprellung mit Flanken-Erkennung, wie bei einem Taster in der Elektronik"],
    ["8. Lampe schalten", "Der Befehl „umschalten“ geht über den Postboten an den Übersetzer und von dort per Funk zur Lampe.",
     "MQTT an <i>zigbee2mqtt/lampe/set</i> mit {\"state\": \"TOGGLE\"} → Mosquitto → zigbee2mqtt → USB-Koordinator → IKEA TRÅDFRI (Zigbee 3.0, 2,4 GHz Mesh)"],
], [32, 70, 68]))
story.append(Spacer(1, 4 * mm))
story.append(p("<b>Warum nicht einfach eine 3D-Kamera?</b> Das Projekt zeigt, dass eine normale Webcam und KI reichen. "
               "Eine einzelne Kamera kann Entfernung eigentlich nicht messen. Die KI hat aber aus Millionen Bildern gelernt, "
               "woran man sie erkennt: Größe, Verdeckung, Schatten, Perspektive."))
story.append(Spacer(1, 4 * mm))
story.append(box([p("Schick die Person runter zur <b>Diplomarbeit SteadyTouch</b> in der <b>Aula</b>. "
                    "Dort gibt es Antworten auf weitere Fragen.")], title="Tiefgründigere Fragen?"))
story.append(PageBreak())

# ---------- Page 2: parts + how detection works ----------
story.append(p("Die Teile und was sie machen", "h1"))
story.append(table(["Teil", "Was es macht", "So siehst du, dass es funktioniert"], [
    ["Kamera<br/>(Microsoft LifeCam)", "Filmt den Rahmen von vorne. Hängt per USB am PC.", "Das kleine Licht an der Kamera leuchtet, wenn das Programm läuft."],
    ["Bilderrahmen", "Hier steckt man die Hand durch.", "Nur im Notfall bewegen."],
    ["Beamer", "Zeigt das Punkte-Bild an, damit man sieht, was der Computer erkennt.", "Das Punkte-Bild ist an der Wand zu sehen. Nicht verschieben!"],
    ["PC mit Grafikkarte", "Rechnet die Erkennung. Die Grafikkarte macht die KI schnell.", "Das Programm zeigt ein Punkte-Bild im Vollbild."],
    ["Programm<br/>" + code("webcam_color_highfps.py"), "Erkennt die Hand und entscheidet, wann die Lampe schaltet.", "Läuft in einem Terminal-Fenster, zeigt das Punkte-Bild."],
    ["Mosquitto", "Ein „Postbote“: nimmt Nachrichten vom Programm an und gibt sie weiter. Startet automatisch mit Windows.", "Läuft unsichtbar im Hintergrund."],
    ["zigbee2mqtt", "Übersetzt die Nachricht in Zigbee-Funk für die Lampe.", "Im Terminal steht „Zigbee2MQTT started!“. Webseite: localhost:8080"],
    ["USB-Funkstick", "Der Funk-Sender für Zigbee. Steckt am PC.", "Im Geräte-Manager: „Silicon Labs CP210x (COM3)“."],
    ["IKEA-Lampe", "Heißt im System <b>lampe</b>. Schaltet um, wenn der Befehl kommt.", "Braucht Strom: Wandschalter muss AN sein."],
], [38, 66, 66]))

story += [Spacer(1, 4 * mm), p("Wie erkennt der Computer die Hand?", "h1")]
story.append(steps([
    ("Merken, wie es leer aussieht", [p("Beim Start nimmt das Programm ca. 3 Sekunden lang Bilder vom <b>leeren</b> Rahmen auf. "
                                        "Das ist der „Hintergrund“. Deshalb darf beim Start niemand die Hand reinhalten.")]),
    ("Farbe vergleichen", [p("Jedes neue Bild wird mit dem Hintergrund verglichen. Wo die Farbe deutlich anders ist "
                             "(z. B. Haut statt weiße Wand), ist vielleicht etwas Neues.")]),
    ("Entfernung schätzen (KI)", [p("Eine KI namens <i>Depth Anything</i> schätzt aus dem Bild, wie weit alles weg ist. "
                                    "Sie wurde mit Millionen Bildern trainiert. Ist etwas deutlich <b>näher</b> als die Wand, zählt es.")]),
    ("Beide müssen „ja“ sagen", [p("Nur wenn Farbe <b>und</b> Entfernung sagen „da ist was“, wird der Punkt hell. "
                                   "So werden Fehler einer Methode von der anderen herausgefiltert.")]),
    ("Feld in der Mitte prüfen", [p("Ist im Erkennungsfeld (Bildmitte, etwas unterhalb) ein heller Punkt und bleibt er "
                                    "<b>0,3 Sekunden</b>, wird die Lampe umgeschaltet. Danach passiert nichts mehr, bis die Hand "
                                    "<b>0,5 Sekunden</b> ganz draußen war. So schaltet die Lampe nicht dauernd hin und her.")]),
]))
story.append(PageBreak())

# ---------- Page 3: start ----------
story.append(p("System starten", "h1"))
story.append(p("Die Reihenfolge ist wichtig. Mosquitto (der Postbote) startet automatisch mit Windows, darum musst du dich nicht kümmern."))
story.append(steps([
    ("Strom und Kabel", [p("Lampe am Wandschalter <b>einschalten</b>. Kamera und USB-Funkstick am PC anstecken.")]),
    ("zigbee2mqtt starten (Terminal 1)", [p("Ein Terminal (PowerShell) öffnen und eingeben:"),
        codebox(["cd Handportal-Lampe-v2\\zigbee2mqtt", "npm start"]),
        p("Warten, bis <b>„Zigbee2MQTT started!“</b> erscheint. Dieses Fenster offen lassen!", "small")]),
    ("Erkennung starten (Terminal 2)", [p("Ein <b>zweites</b> Terminal öffnen:"),
        codebox(["cd Handportal-Lampe-v2", "py webcam_color_highfps.py"])]),
    ("3 Sekunden: Rahmen leer lassen!", [p("Jetzt merkt sich das Programm den Hintergrund. Niemand darf die Hand reinhalten, "
                                          "nichts bewegen, Licht nicht verändern. Danach erscheint das Punkte-Bild im Vollbild.")]),
    ("Fertig", [p("Hand durch den Rahmen in die Mitte halten: Die Lampe schaltet um. "
                  "Zum Beenden im Punkte-Fenster die Taste <b>ESC</b> drücken.")]),
]))
story.append(Spacer(1, 5 * mm))
story.append(box([p("Meldungen wie <i>„Triton not found“</i> oder <i>„A matching Triton is not available“</i> beim Start "
                    "sind <b>keine Fehler</b>. Einfach ignorieren.")], bg=ACCENT_BG, title="Gut zu wissen"))
story.append(Spacer(1, 3 * mm))
story.append(box([p("Wenn sich das Licht im Raum stark ändert (Sonne, Deckenlicht an/aus) oder Kamera, Lampe, Beamer oder Tisch verschoben wurden: "
                    "Programm mit <b>ESC</b> beenden und neu starten. Dann merkt es sich den neuen Hintergrund.")],
                 bg=WARN_BG, border=WARN, title="Wichtig"))
story.append(PageBreak())

# ---------- Page 4-5: troubleshooting ----------
story.append(p("Fehler beheben", "h1"))
story.append(p("Such dein Problem in der linken Spalte. Probier die Lösungen von oben nach unten."))
story.append(table(["Problem", "Warum passiert das?", "Lösung"], [
    ["Das Bild zeigt die Laptop-Kamera statt die Rahmen-Kamera",
     "Der PC hat zwei Kameras. Das Programm nimmt die falsche Nummer.",
     "In " + code("webcam_color_highfps.py") + " die Zeile " + code("cv2.VideoCapture(1, ...)") + " suchen und die "
     "<b>1</b> gegen <b>0</b> tauschen (oder umgekehrt). Speichern (Strg+S), neu starten."],
    ["Bild ist schwarz oder ruckelt extrem (ca. 1 Bild pro Sekunde)",
     "Ein anderes Programm benutzt die Kamera gerade (z. B. ein zweites Python-Fenster, Teams, die Kamera-App).",
     "Alle anderen Programme und Terminal-Fenster mit Python schließen. Dann neu starten."],
    ["Punkte leuchten, obwohl keine Hand im Rahmen ist",
     "Beim Start war etwas im Bild, oder das Licht hat sich seitdem verändert.",
     "Mit ESC beenden, Rahmen leer machen, neu starten. Hilft das nicht: " + code("COLOR_THRESH") + " von 30 auf 40 bis 50 erhöhen."],
    ["Hand wird nur teilweise oder gar nicht erkannt",
     "Die Hand unterscheidet sich zu wenig von der Wand (z. B. weißer Ärmel) oder es ist zu dunkel.",
     "Mehr Licht. Ärmel hochkrempeln. " + code("COLOR_THRESH") + " auf 20 senken."],
    ["Hand ist im Bild sichtbar, aber die Lampe schaltet nicht",
     "Die Hand ist nicht im Erkennungsfeld, oder der Befehl kommt nicht bei der Lampe an.",
     "1. Hand <b>in die Mitte, etwas unterhalb</b> halten, kurz still halten.<br/>"
     "2. Läuft Terminal 1 (zigbee2mqtt) noch?<br/>"
     "3. Lampe am Wandschalter an?<br/>"
     "4. Steht in Terminal 2 „[MQTT] Fehler“? Dann siehe nächste Zeile."],
    ["In Terminal 2 steht „[MQTT] Fehler beim Senden“",
     "Der Postbote (Mosquitto) läuft nicht.",
     "Windows-Suche: „Dienste“ öffnen, <b>mosquitto</b> suchen, Rechtsklick, <b>Starten</b>."],
    ["Lampe schaltet nicht noch einmal",
     "Absicht: Die Lampe schaltet nur einmal pro Hineinhalten.",
     "Hand ganz aus dem Rahmen nehmen, kurz warten (0,5 s), dann wieder reinhalten."],
    ["Die Lampe schaltet zweimal hintereinander",
     "Die Erkennung flackert am Rand des Felds.",
     "In " + code("zigbee.py") + " " + code("RELEASE_SECONDS") + " von 0.5 auf 1.0 erhöhen."],
], [42, 52, 76]))
story.append(PageBreak())
story.append(p("Fehler beheben: zigbee2mqtt und Lampe", "h1"))
story.append(table(["Problem", "Warum passiert das?", "Lösung"], [
    ["npm start: „'rimraf' is not recognized“",
     "Es fehlen Hilfsprogramme, die zigbee2mqtt zum Starten braucht.",
     "Im Ordner " + code("zigbee2mqtt") + " einmal eingeben:<br/>" + code("pnpm install --frozen-lockfile") + "<br/>Danach wieder " + code("npm start") + "."],
    ["zigbee2mqtt meldet einen Fehler mit COM3 oder findet den Stick nicht",
     "Der USB-Funkstick ist nicht angesteckt oder hat eine andere Nummer bekommen.",
     "Stick ab- und wieder anstecken. Im Geräte-Manager unter „Anschlüsse (COM &amp; LPT)“ nachsehen. "
     "Steht dort nicht COM3: in " + code("zigbee2mqtt\\data\\configuration.yaml") + " bei " + code("port:") + " die richtige Nummer eintragen."],
    ["Die Lampe ist in zigbee2mqtt verschwunden / muss neu verbunden werden",
     "Die Lampe wurde zurückgesetzt oder mit einem anderen System verbunden.",
     "1. Im Browser <b>localhost:8080</b> öffnen, oben <b>„Permit join“</b> klicken.<br/>"
     "2. Lampe <b>6-mal</b> hintereinander aus- und einschalten (ca. 1 Sekunde Abstand). Sie blinkt, wenn es geklappt hat.<br/>"
     "3. Wenn sie in der Liste auftaucht: in <b>lampe</b> umbenennen (genau so, klein geschrieben)."],
    ["Fehler „FileNotFoundError“ mit „.pth“ am Ende",
     "Die Datei mit dem „Wissen“ der KI fehlt.",
     "Im Browser <b>huggingface.co/depth-anything/Depth-Anything-V2-Small</b> öffnen, unter „Files“ die Datei "
     + code("depth_anything_v2_vits.pth") + " (ca. 100 MB) herunterladen und in den Ordner "
     + code("Handportal-Lampe-v2\\checkpoints") + " legen."],
    ["Programm reagiert nicht mehr, Fenster hängt",
     "Das Vollbild-Fenster hat die Tastatur nicht mehr.",
     "Ins Punkte-Fenster klicken, dann ESC. Hilft das nicht: im Terminal <b>Strg+C</b> drücken."],
], [42, 52, 76]))
story.append(Spacer(1, 6 * mm))
story.append(box([p("Kommst du nicht weiter? Schreib auf, <b>was du gemacht hast</b> und <b>welche Meldung</b> im Terminal steht "
                    "(Foto mit dem Handy reicht). Damit kann dir jemand viel schneller helfen.")], bg=WARN_BG, border=WARN,
                 title="Wenn nichts hilft"))
story.append(PageBreak())

# ---------- Page 6: settings + FAQ ----------
story.append(p("Einstellungen anpassen", "h1"))
story.append(p("Nach jeder Änderung: Datei speichern (<b>Strg+S</b>) und das Programm neu starten. "
               "Ändere immer nur <b>eine</b> Sache auf einmal, dann weißt du, was geholfen hat."))
story.append(table(["Was", "Wo", "Standard", "Was passiert, wenn ..."], [
    ["Welche Kamera", code("webcam_color_highfps.py") + "<br/>" + code("VideoCapture(1, ...)"), "1", "0 = Laptop-Kamera, 1 = Rahmen-Kamera (kann sich beim Umstecken ändern)"],
    ["Farb-<br/>Empfindlichkeit",code("webcam_color_highfps.py") + "<br/>" + code("COLOR_THRESH"), "30", "höher = weniger Fehl-Punkte, aber Hand schwerer erkannt; niedriger = umgekehrt"],
    ["Größe des Erkennungsfelds", code("detection.py") + "<br/>die Zahl " + code("11"), "11", "größer = Feld größer, Lampe schaltet leichter"],
    ["Position des Felds", code("detection.py") + "<br/>" + code("h//10"), "10 % unter Mitte", code("h//5") + " = 20 % unter der Mitte, " + code("0") + " = genau Mitte"],
    ["Wie lange halten", code("zigbee.py") + "<br/>" + code("HOLD_SECONDS"), "0.3", "höher = Hand muss länger im Feld sein"],
    ["Pause bis nächstes Schalten", code("zigbee.py") + "<br/>" + code("RELEASE_SECONDS"), "0.5", "höher = weniger doppeltes Schalten"],
    ["Name der Lampe", code("zigbee.py") + "<br/>" + code("LAMPE_NAME"), "lampe", "muss genau gleich heißen wie in zigbee2mqtt"],
], [37, 49, 21, 63]))

story += [Spacer(1, 4 * mm), p("Fragen, die Besucher oft stellen", "h1")]
faq = [
    ("Werde ich gefilmt? Wird das gespeichert?", "Nein. Das Kamerabild wird nur live ausgewertet und sofort wieder vergessen. Es wird nichts gespeichert oder verschickt."),
    ("Woher weiß der Computer, wie weit meine Hand weg ist?", "Eine KI hat aus Millionen Fotos gelernt, wie nahe und ferne Dinge aussehen, z. B. dass nahe Dinge größer sind und andere verdecken. Mit nur einer Kamera ist das eine Schätzung, aber eine ziemlich gute."),
    ("Warum braucht man Farbe UND die KI?", "Jede Methode macht andere Fehler. Die Farbe wird von Schatten verwirrt, die KI von glatten weißen Wänden. Zusammen sind sie zuverlässig."),
    ("Was sind die vielen Punkte auf dem Bildschirm?", "Das ist das, was der Computer „sieht“: Helle Punkte sind Dinge, die näher als die Wand sind, also deine Hand. Alles andere bleibt schwarz."),
    ("Wie kommt der Befehl zur Lampe?", "Per Funk mit Zigbee. Das ist wie WLAN, aber für Smart-Home-Geräte gemacht und sehr stromsparend."),
]
for q, a in faq:
    story.append(KeepTogether([p(f"<b>{q}</b>", "body"), p(a, "body"), Spacer(1, 1 * mm)]))

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=22 * mm,
                        title="Handportal-Lampe – Anleitung", author="Handportal-Lampe Team",
                        subject="Erklären, Starten und Fehlerbeheben")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("written", OUT)
