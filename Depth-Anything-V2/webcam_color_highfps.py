import cv2, torch, numpy as np
from detection import center_detection
from zigbee import toggle_on_enter

MODE = "both"       # "color" = nur Farbunterschied zum leeren Hintergrund, "both" = Farbe UND Tiefe müssen zustimmen
COLOR_THRESH = 30   # wie stark die Farbe eines Pixels vom leeren Hintergrund abweichen muss (0-255), damit er zählt
WORK = (640, 360)   # mit halber Auflösung von 1280x720 rechnen: 4x weniger Pixel, das Raster nimmt eh nur jeden 10. Pixel

if MODE == "both":
    from depth_anything_v2.dpt import DepthAnythingV2
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = DepthAnythingV2(encoder='vits', features=64, out_channels=[48, 96, 192, 384])
    model.load_state_dict(torch.load('checkpoints/depth_anything_v2_vits.pth', map_location=DEVICE))
    model = model.to(DEVICE).eval()

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW) # Auswahl der Kamera
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)   # Automatik aus (wichtig: sonst ändert sich die Wandfarbe mit der Belichtung)
cap.set(cv2.CAP_PROP_EXPOSURE, -7)          # 1/128 s
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 10000); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 10000)
print(cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

cv2.namedWindow("window_name", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("window_name", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

S, G = 10, 6   # Blockgröße, Breite der Lücke
block = np.zeros((S, S), np.uint8); block[:S-G, :S-G] = 1   # 1 = Wert, 0 = Lücke

# Hintergrund: beim Start darf nichts vor der Kamera sein
for _ in range(30): cap.read() # Kamera einpendeln lassen, die ersten Bilder sind falsch belichtet
frames = [cv2.resize(cap.read()[1], WORK, interpolation=cv2.INTER_AREA) for _ in range(20)]
bg_color = cv2.GaussianBlur(np.median(frames, axis=0).astype(np.uint8), (3, 3), 0) # Median = typische Wandfarbe, Blur = weniger Kamerarauschen
if MODE == "both":
    with torch.autocast('cuda', dtype=torch.float16, enabled=DEVICE == 'cuda'):
        bg = np.max([model.infer_image(f, 252).astype(np.float32) for f in frames], axis=0) # gleicher Tiefen-Hintergrund wie webcam.py, aus denselben Bildern
    bg = cv2.dilate(bg, np.ones((13, 13), np.uint8)) # 13 bei halber Auflösung = 25 bei voller Auflösung

while True:
    ok, frame = cap.read()
    if not ok: break
    frame = cv2.resize(frame, WORK, interpolation=cv2.INTER_AREA)
    diff = cv2.absdiff(cv2.GaussianBlur(frame, (3, 3), 0), bg_color).max(axis=2) # größte Änderung von B, G oder R pro Pixel
    color_fg = cv2.medianBlur((diff > COLOR_THRESH).astype(np.uint8), 3) > 0      # medianBlur entfernt einzelne verrauschte Pixel

    if MODE == "color":
        vis = color_fg.astype(np.uint8) * 255  # keine Entfernung: etwas ist da = 255
    else:
        with torch.autocast('cuda', dtype=torch.float16, enabled=DEVICE == 'cuda'): # halbe Genauigkeit (FP16): ca. 2x schneller auf Nvidia, gleiches Ergebnis
            depth = model.infer_image(frame, 252).astype(np.float32)
        a, b = np.median(bg / np.maximum(depth, 1e-6)), 0.0 # gleiche Tiefen-Logik wie webcam.py
        is_bg = a * depth + b < bg * 1.15
        for _ in range(2):
            x, y = depth[is_bg][::50], bg[is_bg][::50]
            if x.size < 2: break  # fast kein Hintergrund sichtbar -> letzte Schätzung behalten
            # Ausgleichsgerade (kleinste Quadrate) per Formel statt np.polyfit: polyfit scheitert manchmal ("did not converge")
            xm, ym = x.mean(), y.mean()
            a = ((x - xm) * (y - ym)).sum() / max(((x - xm) ** 2).sum(), 1e-12)
            b = ym - a * xm
            is_bg = a * depth + b < bg * 1.15
        depth = a * depth + b
        depth[is_bg | ~color_fg] = 0  # nur wo die Tiefe "näher" UND die Farbe "verändert" sagt
        vis = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    small = vis[::S//2, ::S//2]    # jeder S-te Wert bei voller Auflösung = jeder S/2-te bei halber Auflösung
    toggle_on_enter(center_detection(vis)) # Mitte vom Bild
    vis = np.kron(small, block)    # hochskalieren + Lücken
    cv2.imshow('window_name', vis)
    if cv2.waitKey(1) == 27: break

cap.release(); cv2.destroyAllWindows()
