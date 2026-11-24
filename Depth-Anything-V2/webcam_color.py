import cv2, torch, numpy as np
from detection import rect_detection
from zigbee import toggle_on_enter

MODE = "both"       # "color" = only color difference to the empty background, "both" = color AND depth must agree
COLOR_THRESH = 30   # how much a pixel's color must differ from the empty background (0-255) to count

if MODE == "both":
    from depth_anything_v2.dpt import DepthAnythingV2
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = DepthAnythingV2(encoder='vits', features=64, out_channels=[48, 96, 192, 384])
    model.load_state_dict(torch.load('checkpoints/depth_anything_v2_vits.pth', map_location=DEVICE))
    model = model.to(DEVICE).eval()

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW) # auswahl der kamera
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)   # Automatik aus (wichtig: sonst ändert sich die Wandfarbe mit der Belichtung)
cap.set(cv2.CAP_PROP_EXPOSURE, -7)          # 1/128 s
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 10000); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 10000)
print(cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

cv2.namedWindow("window_name", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("window_name", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

S, G = 10, 6   # block size, gap width
block = np.zeros((S, S), np.uint8); block[:S-G, :S-G] = 1   # 1 = value, 0 = gap

# background, nothing in front of the camera at start
for _ in range(30): cap.read() # let camera exposure settle, first frames are off
frames = [cap.read()[1] for _ in range(20)]
bg_color = cv2.GaussianBlur(np.median(frames, axis=0).astype(np.uint8), (5, 5), 0) # median = typical wall color, blur = less camera noise
if MODE == "both":
    bg = np.max([model.infer_image(f, 252) for f in frames], axis=0) # same depth bg as webcam.py, from the same frames
    bg = cv2.dilate(bg.astype(np.float32), np.ones((25, 25), np.uint8))

while True:
    ok, frame = cap.read()
    if not ok: break
    diff = cv2.absdiff(cv2.GaussianBlur(frame, (5, 5), 0), bg_color).max(axis=2) # biggest change of B, G or R per pixel
    color_fg = cv2.medianBlur((diff > COLOR_THRESH).astype(np.uint8), 5) > 0      # medianBlur removes single noisy pixels

    if MODE == "color":
        vis = color_fg.astype(np.uint8) * 255  # no distance info: something is there = 255
    else:
        depth = model.infer_image(frame, 252)
        is_bg = depth * np.median(bg / np.maximum(depth, 1e-6)) < bg * 1.15 # same depth logic as webcam.py
        for _ in range(2):
            a, b = np.polyfit(depth[is_bg][::50], bg[is_bg][::50], 1)
            is_bg = a * depth + b < bg * 1.15
        depth = a * depth + b
        depth[is_bg | ~color_fg] = 0  # only where depth says "closer" AND color says "changed"
        vis = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    small = vis[::S, ::S]          # every S-th value
    toggle_on_enter(rect_detection(vis))
    vis = np.kron(small, block)    # scale up + gaps
    cv2.imshow('window_name', vis)
    if cv2.waitKey(1) == 27: break

cap.release(); cv2.destroyAllWindows()
