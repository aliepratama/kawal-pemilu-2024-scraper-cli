import cv2
import numpy as np
import matplotlib.pyplot as plt
from ultralytics import YOLO

# ==========================================
# 1. HELPER WARP (STANDARD)
# ==========================================
def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]; rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]; rect[3] = pts[np.argmax(diff)]
    return rect

def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    dst = np.array([[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (maxWidth, maxHeight))

def warp_from_mask_initial(image, mask_points):
    contour = np.array(mask_points, dtype=np.int32)
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect)
    box = np.int32(box)
    return four_point_transform(image, box)

def clean_border_fallback(img):
    if img is None: return img
    h, w = img.shape[:2]
    py, px = int(h*0.15), int(w*0.15)
    return cv2.resize(img[py:h-py, px:w-px], (w, h))

# ==========================================
# 2. STRATEGI FINAL: OUTER SHELL PEELING
# ==========================================
def process_digit_peel_outer(img, peel_pixels=7):
    """
    Strategi: 'Kupas Kulit'
    1. Padding PUTIH (Isolasi border hitam).
    2. Deteksi 'Monster' (Border + Angka).
    3. Ambil kotak terluarnya saja.
    4. Kecilkan kotak itu (Peel) seukuran ketebalan border.
    """
    if img is None or img.size == 0: return img

    # 1. PADDING PUTIH (255)
    # Ini kuncinya! Biar Border Hitam dikelilingi Putih, jadi objek terpisah.
    pad = 10
    img_padded = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(255,255,255))
    
    # 2. Invers Threshold
    # Asli: Border=Hitam.
    # Invers: Border=Putih (Objek), Background=Hitam.
    gray = cv2.cvtColor(img_padded, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 3. Find External Contour
    # Kita ambil kulit terluar. Sekalipun angka nempel di dalam, 
    # kontur terluar tetaplah bentuk kotak border.
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours: 
        return clean_border_fallback(img)

    # Ambil yang terbesar (Si Monster Border)
    target_cnt = max(contours, key=cv2.contourArea)
    
    # 4. Fit Rotated Rect (Kotak Merah di Debug tadi)
    rect = cv2.minAreaRect(target_cnt)
    (center, (w, h), angle) = rect

    # 5. PEELING ACTION (Kupas Kulitnya)
    # Kita kurangi lebar dan tinggi kotak sebesar 2x tebal border
    new_w = w - (2 * peel_pixels)
    new_h = h - (2 * peel_pixels)
    
    # Safety: Jangan sampai minus
    if new_w < 10 or new_h < 10: 
        return clean_border_fallback(img)
    
    # Update Rect dengan ukuran baru yang lebih kecil (Inset)
    new_rect = (center, (new_w, new_h), angle)
    box = cv2.boxPoints(new_rect)
    box = np.int32(box)

    # 6. Warp (Dari gambar Padded)
    warped = four_point_transform(img_padded, box)

    return warped

# ==========================================
# 3. MAIN EXECUTION
# ==========================================
MODEL_PATH = "/content/C1_Plano_Project/run_segmentation/weights/best.pt"
TEST_IMAGE_PATH = "/content/raw_6104252010_001_a4daa.jpg" 

model = YOLO(MODEL_PATH)
results = model.predict(TEST_IMAGE_PATH, conf=0.25, iou=0.5, imgsz=1280)
result = results[0]
img_bgr = cv2.imread(TEST_IMAGE_PATH)

if result.masks is not None:
    masks = result.masks.xy 
    boxes = result.boxes.xyxy.cpu().numpy()
    
    detected_objects = []
    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = map(int, box)
        detected_objects.append({'mask': masks[i], 'center_y': (y1+y2)/2, 'center_x': (x1+x2)/2})

    detected_objects.sort(key=lambda k: k['center_y'])
    rows = []
    for i in range(0, 9, 3):
        chunk = detected_objects[i : i+3]
        if chunk: chunk.sort(key=lambda k: k['center_x']); rows.append(chunk)

    paslon_names = ["Paslon 01", "Paslon 02", "Paslon 03"]
    fig, axes = plt.subplots(3, 3, figsize=(10, 11))
    plt.subplots_adjust(wspace=0.2, hspace=0.4)
    
    print("\n✅ FINAL RESULT (Outer Shell Peeling):")
    print("Metode ini 'buta' terhadap isi (angka nempel/tidak). Dia hanya mengupas kulit frame.")

    for i in range(3):
        p_name = paslon_names[i] if i < len(paslon_names) else f"Row {i+1}"
        row_objs = rows[i] if i < len(rows) else []

        for j in range(3):
            ax = axes[i, j]
            if j < len(row_objs):
                obj = row_objs[j]
                try:
                    initial_warp = warp_from_mask_initial(img_bgr, obj['mask'])
                    
                    # KITA PAKAI STRATEGI PEELING UNTUK SEMUA
                    # Karena ini paling robust, bahkan untuk X sekalipun.
                    # peel_pixels=7 cukup untuk membuang border tebal.
                    final_img = process_digit_peel_outer(initial_warp, peel_pixels=7)
                    
                    final_gray = cv2.cvtColor(final_img, cv2.COLOR_BGR2GRAY)
                    final_view = cv2.copyMakeBorder(final_gray, 3, 3, 3, 3, cv2.BORDER_CONSTANT, value=255)
                    final_view = cv2.cvtColor(final_view, cv2.COLOR_GRAY2RGB)
                    
                    ax.imshow(final_view)
                    ax.set_title(f"Digit {j+1}", fontsize=10)
                    
                except Exception as e:
                    print(e); ax.imshow(np.zeros((64,64,3)))
            else:
                ax.imshow(np.zeros((64,64,3)))

            if j == 1:
                ax.text(0.5, 1.25, p_name, transform=ax.transAxes, 
                        ha='center', fontsize=12, fontweight='bold', color='blue')
            ax.set_xticks([]); ax.set_yticks([])

    plt.show()