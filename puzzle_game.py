"""
Gesture-Controlled Virtual Puzzle Game
---------------------------------------
4x4 jigsaw puzzle controlled entirely with hand gestures via webcam.

The puzzle image fills the box you select and is cut into a 4x4 grid.
All 16 pieces stay INSIDE that box at all times, each occupying exactly one
grid cell - they start shuffled (out of order) and you drag them around to
put them back in the right order. Dragging a piece onto another piece's
cell SWAPS the two, so the box is always completely full, pieces never
overlap, and nothing ever leaves the box.

Controls
--------
SETUP PHASE (before the puzzle exists):
    - Pinch (thumb + index finger) with your LEFT hand  -> sets the TOP-LEFT corner
    - Pinch (thumb + index finger) with your RIGHT hand -> sets the BOTTOM-RIGHT corner
    - While BOTH hands are pinching at the same time, a live preview box is drawn.
    - Release both pinches to LOCK IN the box -> the puzzle is generated,
      cut into a 4x4 grid, and shuffled inside that same box.

PLAY PHASE:
    - Pinch on top of a piece to grab it.
    - Drag it (still pinching) - it follows your finger but is always kept
      clamped inside the box, so it can't overlap the edge or leave.
    - Release near a grid cell to drop the piece there:
        - If that cell already has a different piece, the two SWAP places.
        - Pieces in their correct spot get a green border.
    - Get every piece into its correct cell to win.

GLOBAL KEYS:
    - ENTER : quit the program
    - SPACE : reset back to a blank frame (clears the puzzle / box, back to SETUP)

Requirements: opencv-python, cvzone, mediapipe, numpy, Pillow
    pip install opencv-python cvzone mediapipe numpy Pillow

Optional: put an image named "puzzle.jpg" in this same folder to use your own
picture. If it's missing, a colorful auto-generated placeholder image is used.
"""

import os
import time
import random
import numpy as np
import cv2
from cvzone.HandTrackingModule import HandDetector

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------
GRID = 4                      # 4x4 puzzle
CAM_W, CAM_H = 1280, 720
PINCH_THRESHOLD = 40           # pixel distance between thumb tip & index tip to count as a pinch
MIN_BOX_SIZE = 160             # minimum width/height for a valid puzzle box
IMG_PATH = os.path.join(os.path.dirname(__file__), "puzzle.jpg")

STATE_SETUP = "setup"
STATE_PLAY = "play"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def make_placeholder_image(size=500):
    """Generate a colorful numbered placeholder image if the user hasn't supplied one."""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    step = size // GRID
    for r in range(GRID):
        for c in range(GRID):
            color = (
                int(40 + 200 * (r / (GRID - 1))),
                int(40 + 200 * (c / (GRID - 1))),
                int(80 + 150 * ((r + c) % 2)),
            )
            y1, y2 = r * step, (r + 1) * step
            x1, x2 = c * step, (c + 1) * step
            cv2.rectangle(img, (x1, y1), (x2, y2), color, -1)
            cv2.putText(
                img, str(r * GRID + c + 1),
                (x1 + step // 3, y1 + step // 2 + 10),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3
            )
    return img


def load_puzzle_source():
    if os.path.exists(IMG_PATH):
        img = cv2.imread(IMG_PATH)
        if img is not None:
            return img
    print("[info] No puzzle.jpg found (or failed to load) - using generated placeholder image.")
    return make_placeholder_image()


def cell_center(box_x1, box_y1, cell_w, cell_h, row, col):
    cx = box_x1 + col * cell_w + cell_w // 2
    cy = box_y1 + row * cell_h + cell_h // 2
    return [cx, cy]


def build_pieces(box_x1, box_y1, box_w, box_h):
    """Slice the source image into a GRID x GRID set of pieces sized to exactly
    fill the chosen box, then shuffle which cell each piece currently sits in."""
    src = load_puzzle_source()
    cell_w = box_w // GRID
    cell_h = box_h // GRID
    fit_w, fit_h = cell_w * GRID, cell_h * GRID  # exact multiple, avoids rounding gaps
    resized = cv2.resize(src, (fit_w, fit_h))

    pieces = []
    piece_id = 0
    for r in range(GRID):
        for c in range(GRID):
            y1, y2 = r * cell_h, (r + 1) * cell_h
            x1, x2 = c * cell_w, (c + 1) * cell_w
            piece_img = resized[y1:y2, x1:x2].copy()
            cv2.rectangle(piece_img, (0, 0), (piece_img.shape[1] - 1, piece_img.shape[0] - 1), (255, 255, 255), 2)

            pieces.append({
                "id": piece_id,
                "img": piece_img,
                "w": cell_w,
                "h": cell_h,
                "correct_cell": (r, c),
                "cell": (r, c),          # current cell - gets shuffled below
                "held_by": None,
            })
            piece_id += 1

    # Shuffle current cells among all pieces (guarantee it isn't already solved)
    cells = [p["cell"] for p in pieces]
    solved = True
    while solved:
        random.shuffle(cells)
        solved = all(cells[i] == pieces[i]["correct_cell"] for i in range(len(pieces)))
    for p, cell in zip(pieces, cells):
        p["cell"] = cell

    box = {"x1": box_x1, "y1": box_y1, "w": fit_w, "h": fit_h, "cell_w": cell_w, "cell_h": cell_h}
    return pieces, box


def piece_pos(piece, box):
    """Current on-screen center position of a piece (its cell center),
    unless it's actively being dragged (handled separately)."""
    r, c = piece["cell"]
    return cell_center(box["x1"], box["y1"], box["cell_w"], box["cell_h"], r, c)


def nearest_cell(pt, box):
    r = (pt[1] - box["y1"]) // box["cell_h"]
    c = (pt[0] - box["x1"]) // box["cell_w"]
    r = max(0, min(GRID - 1, int(r)))
    c = max(0, min(GRID - 1, int(c)))
    return (r, c)


def clamp_to_box(pt, box, half_w, half_h):
    x = max(box["x1"] + half_w, min(box["x1"] + box["w"] - half_w, pt[0]))
    y = max(box["y1"] + half_h, min(box["y1"] + box["h"] - half_h, pt[1]))
    return [x, y]


def overlay_piece(frame, img, cx, cy, w, h):
    """Draw an image (opaque) centered at (cx, cy), clipped to frame bounds."""
    x1, y1 = int(cx - w / 2), int(cy - h / 2)
    x2, y2 = x1 + w, y1 + h
    fh, fw = frame.shape[:2]

    sx1, sy1 = 0, 0
    if x1 < 0:
        sx1 = -x1
        x1 = 0
    if y1 < 0:
        sy1 = -y1
        y1 = 0
    sx2 = w - max(0, x2 - fw)
    sy2 = h - max(0, y2 - fh)
    x2 = min(x2, fw)
    y2 = min(y2, fh)

    if x2 <= x1 or y2 <= y1:
        return
    frame[y1:y2, x1:x2] = img[sy1:sy2, sx1:sx2]


def dist(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    cap = cv2.VideoCapture(0)
    cap.set(3, CAM_W)
    cap.set(4, CAM_H)

    detector = HandDetector(maxHands=2, detectionCon=0.8)

    state = STATE_SETUP
    corner_tl = None
    corner_br = None
    both_pinching_prev = False

    pieces = []
    box = None
    drag_pos = {}  # hand_key -> [x, y] live drag position while held
    win_time = None

    print("Controls: ENTER = quit | SPACE = reset")
    print("Setup: pinch LEFT hand = top-left corner, pinch RIGHT hand = bottom-right corner.")
    print("Hold both pinches to preview the box, release both to lock it in.")

    while True:
        success, frame = cap.read()
        if not success:
            break
        frame = cv2.flip(frame, 1)
        frame_h, frame_w = frame.shape[:2]

        hands, frame = detector.findHands(frame, flipType=False)  # already flipped above

        # ------------------------------------------------------------
        # SETUP PHASE
        # ------------------------------------------------------------
        if state == STATE_SETUP:
            left_hand = next((h for h in hands if h["type"] == "Left"), None)
            right_hand = next((h for h in hands if h["type"] == "Right"), None)

            left_pinching = False
            right_pinching = False

            if left_hand:
                lm = left_hand["lmList"]
                p1, p2 = lm[4][:2], lm[8][:2]
                if dist(p1, p2) < PINCH_THRESHOLD:
                    left_pinching = True
                    corner_tl = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)

            if right_hand:
                lm = right_hand["lmList"]
                p1, p2 = lm[4][:2], lm[8][:2]
                if dist(p1, p2) < PINCH_THRESHOLD:
                    right_pinching = True
                    corner_br = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)

            both_pinching = left_pinching and right_pinching

            if corner_tl:
                cv2.circle(frame, corner_tl, 12, (0, 255, 0), cv2.FILLED)
            if corner_br:
                cv2.circle(frame, corner_br, 12, (0, 0, 255), cv2.FILLED)

            if both_pinching and corner_tl and corner_br:
                x1, y1 = corner_tl
                x2, y2 = corner_br
                x1, x2 = sorted((x1, x2))
                y1, y2 = sorted((y1, y2))
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 200, 0), 3)
                cv2.putText(frame, "Release both pinches to confirm", (30, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 0), 2)

            # Detect release transition -> lock in the box
            if both_pinching_prev and not both_pinching and corner_tl and corner_br:
                x1, y1 = corner_tl
                x2, y2 = corner_br
                x1, x2 = sorted((x1, x2))
                y1, y2 = sorted((y1, y2))
                box_w, box_h = x2 - x1, y2 - y1

                if box_w >= MIN_BOX_SIZE and box_h >= MIN_BOX_SIZE:
                    pieces, box = build_pieces(x1, y1, box_w, box_h)
                    state = STATE_PLAY
                    drag_pos = {}
                    win_time = None
                else:
                    cv2.putText(frame, "Box too small - try again", (30, 80),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    corner_tl, corner_br = None, None

            both_pinching_prev = both_pinching

            cv2.putText(frame, "SETUP: pinch LEFT=top-left, RIGHT=bottom-right",
                        (30, frame_h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # ------------------------------------------------------------
        # PLAY PHASE
        # ------------------------------------------------------------
        elif state == STATE_PLAY:
            cv2.rectangle(frame, (box["x1"], box["y1"]),
                          (box["x1"] + box["w"], box["y1"] + box["h"]), (0, 255, 255), 2)
            # grid lines
            for i in range(1, GRID):
                gx = box["x1"] + i * box["cell_w"]
                gy = box["y1"] + i * box["cell_h"]
                cv2.line(frame, (gx, box["y1"]), (gx, box["y1"] + box["h"]), (0, 255, 255), 1)
                cv2.line(frame, (box["x1"], gy), (box["x1"] + box["w"], gy), (0, 255, 255), 1)

            half_w, half_h = box["cell_w"] // 2, box["cell_h"] // 2

            for hand in hands:
                lm = hand["lmList"]
                p1, p2 = lm[4][:2], lm[8][:2]
                pinching = dist(p1, p2) < PINCH_THRESHOLD
                finger_pt = [(p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2]
                hand_key = hand["type"]

                cv2.circle(frame, tuple(finger_pt), 8, (0, 255, 0) if pinching else (200, 200, 200), cv2.FILLED)

                if pinching:
                    held_piece = next((p for p in pieces if p["held_by"] == hand_key), None)
                    if held_piece:
                        # keep the dragged piece fully inside the box at all times
                        drag_pos[hand_key] = clamp_to_box(finger_pt, box, half_w, half_h)
                    else:
                        # grab whichever piece's current cell the finger is over
                        target_cell = nearest_cell(finger_pt, box)
                        for p in pieces:
                            if p["held_by"] is None and p["cell"] == target_cell:
                                p["held_by"] = hand_key
                                drag_pos[hand_key] = clamp_to_box(finger_pt, box, half_w, half_h)
                                break
                else:
                    held_piece = next((p for p in pieces if p["held_by"] == hand_key), None)
                    if held_piece:
                        drop_pt = drag_pos.get(hand_key, piece_pos(held_piece, box))
                        target_cell = nearest_cell(drop_pt, box)
                        occupant = next((p for p in pieces if p is not held_piece and p["cell"] == target_cell), None)
                        if occupant:
                            occupant["cell"], held_piece["cell"] = held_piece["cell"], occupant["cell"]
                        else:
                            held_piece["cell"] = target_cell
                        held_piece["held_by"] = None
                    drag_pos.pop(hand_key, None)

            # draw pieces: settled ones first, dragged one(s) last (on top)
            dragged = [p for p in pieces if p["held_by"] is not None]
            settled = [p for p in pieces if p["held_by"] is None]

            for p in settled:
                cx, cy = piece_pos(p, box)
                overlay_piece(frame, p["img"], cx, cy, p["w"], p["h"])
                if p["cell"] == p["correct_cell"]:
                    x1, y1 = int(cx - p["w"] / 2), int(cy - p["h"] / 2)
                    cv2.rectangle(frame, (x1, y1), (x1 + p["w"], y1 + p["h"]), (0, 255, 0), 3)

            for p in dragged:
                cx, cy = drag_pos.get(p["held_by"], piece_pos(p, box))
                overlay_piece(frame, p["img"], cx, cy, p["w"], p["h"])
                x1, y1 = int(cx - p["w"] / 2), int(cy - p["h"] / 2)
                cv2.rectangle(frame, (x1, y1), (x1 + p["w"], y1 + p["h"]), (255, 200, 0), 3)

            placed_count = sum(1 for p in pieces if p["cell"] == p["correct_cell"])
            cv2.putText(frame, f"Placed: {placed_count}/{len(pieces)}", (30, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

            if placed_count == len(pieces) and pieces:
                if win_time is None:
                    win_time = time.time()
                cv2.putText(frame, "PUZZLE COMPLETE!", (frame_w // 2 - 220, frame_h // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 255, 0), 4)

            cv2.putText(frame, "SPACE = reset | ENTER = quit", (30, frame_h - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Gesture Puzzle Game", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 13:  # ENTER
            break
        elif key == 32:  # SPACE -> reset to blank frame, back to setup
            state = STATE_SETUP
            corner_tl, corner_br = None, None
            both_pinching_prev = False
            pieces = []
            box = None
            drag_pos = {}
            win_time = None

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
