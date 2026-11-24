import cv2, torch, numpy as np
from depth_anything_v2.dpt import DepthAnythingV2
from detection import rect_detection
from zigbee import toggle_on_enter

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
model = DepthAnythingV2(encoder='vits', features=64, out_channels=[48, 96, 192, 384])
model.load_state_dict(torch.load('checkpoints/depth_anything_v2_vits.pth', map_location=DEVICE))
model = model.to(DEVICE).eval()

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW) # auswahl der kamera
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)   # Automatik aus
cap.set(cv2.CAP_PROP_EXPOSURE, -7)          # 1/128 s
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 10000); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 10000)
print(cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

cv2.namedWindow("window_name", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("window_name", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

S, G = 10, 6   # block size, gap width
block = np.zeros((S, S), np.uint8); block[:S-G, :S-G] = 1   # 1 = value, 0 = gap

# background depth: 10 
for _ in range(30): cap.read() # let camera exposure settle, first frames are off
bg = np.max([model.infer_image(cap.read()[1], 252) for _ in range(20)], axis=0) # max = closest bg ever seen -> bg noise doesn't count as foreground
bg = cv2.dilate(bg.astype(np.float32), np.ones((25, 25), np.uint8)) # nearest bg value within 25px -> edges jittering by a few px don't count as foreground

while True:
    ok, frame = cap.read()
    if not ok: break
    frame = model.infer_image(frame, 252) #infer depth map with input size 252px
    is_bg = frame * np.median(bg / np.maximum(frame, 1e-6)) < bg * 1.15 # first guess: scale only
    for _ in range(2): # model drifts scale AND shift per frame; fit both on bg pixels, 2nd pass without the hand
        a, b = np.polyfit(frame[is_bg][::50], bg[is_bg][::50], 1)
        is_bg = a * frame + b < bg * 1.15
    frame = a * frame + b
    frame[is_bg] = 0   # keep only what is >15% closer than background
    vis = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8) # normalize from 0-1 to 0-255
    small = vis[::S, ::S]          # every S-th value
    # check corner
    toggle_on_enter(rect_detection(vis))
    vis = np.kron(small, block)    # scale up + gaps
    cv2.imshow('window_name', vis) #show depth map
    if cv2.waitKey(1) == 27: break

cap.release(); cv2.destroyAllWindows()
