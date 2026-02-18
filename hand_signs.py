"""
hand_signs.py  –  Hand-Sign Detection via Google MediaPipe (Tasks API v0.10+)
Classifies hand poses into named signs used for jutsu input.
"""

import os
import cv2
import mediapipe as mp

BaseOptions        = mp.tasks.BaseOptions
HandLandmarker     = mp.tasks.vision.HandLandmarker
HandLandmarkerOpts = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode  = mp.tasks.vision.RunningMode

# Path to the hand_landmarker model file (must be next to this script)
_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")

# MediaPipe hand landmark indices
_WRIST       = 0
_THUMB_TIP   = 4
_THUMB_IP    = 3
_INDEX_TIP   = 8
_INDEX_PIP   = 6
_MIDDLE_TIP  = 12
_MIDDLE_PIP  = 10
_RING_TIP    = 16
_RING_PIP    = 14
_PINKY_TIP   = 20
_PINKY_PIP   = 18

# Connections for drawing landmarks on the frame (pairs of landmark indices)
_HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),   # middle
    (0,13),(13,14),(14,15),(15,16), # ring
    (0,17),(17,18),(18,19),(19,20), # pinky
    (5,9),(9,13),(13,17),           # palm cross-connections
]


class HandSignDetector:
    """Wraps MediaPipe HandLandmarker to classify hand poses into named signs."""

    def __init__(self):
        options = HandLandmarkerOpts(
            base_options=BaseOptions(model_asset_path=_MODEL_PATH),
            running_mode=VisionRunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.5,
        )
        self.landmarker = HandLandmarker.create_from_options(options)

    # ── public API ────────────────────────────────────────────────

    def detect(self, frame_bgr):
        """
        Analyse a BGR frame.
        Returns (sign_name: str | None, annotated_frame_bgr).
        sign_name is one of:
          "fist", "open_palm", "peace", "point_up", "thumbs_up", "rock"
        or None if no hand / unrecognised pose.
        """
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        result = self.landmarker.detect(mp_image)

        sign = None
        if result.hand_landmarks:
            landmarks = result.hand_landmarks[0]  # first hand
            self._draw_landmarks(frame_bgr, landmarks)
            sign = self._classify(landmarks)
        return sign, frame_bgr

    def release(self):
        """Clean up MediaPipe resources."""
        self.landmarker.close()

    # ── drawing ───────────────────────────────────────────────────

    @staticmethod
    def _draw_landmarks(frame, landmarks):
        """Draw hand landmarks and connections on the BGR frame."""
        h, w, _ = frame.shape
        pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

        # Draw connections
        for a, b in _HAND_CONNECTIONS:
            cv2.line(frame, pts[a], pts[b], (255, 0, 255), 2)

        # Draw landmark points
        for px, py in pts:
            cv2.circle(frame, (px, py), 4, (0, 255, 255), -1)

    # ── internal classification ───────────────────────────────────

    def _classify(self, landmarks) -> str | None:
        """Map MediaPipe hand landmarks to a named sign."""
        lm = landmarks  # list of NormalizedLandmark

        # Finger-tip and PIP indices
        tips    = [_THUMB_TIP, _INDEX_TIP, _MIDDLE_TIP, _RING_TIP, _PINKY_TIP]
        pip_ids = [_THUMB_IP,  _INDEX_PIP, _MIDDLE_PIP, _RING_PIP, _PINKY_PIP]

        # For each finger: is the tip above (extended) its PIP joint?
        # y-axis is inverted in screen coords (lower y = higher on screen)
        extended = []
        for i in range(5):
            if i == 0:
                # Thumb: compare x-distance from wrist instead
                extended.append(self._thumb_extended(lm))
            else:
                extended.append(lm[tips[i]].y < lm[pip_ids[i]].y)

        thumb, index, middle, ring, pinky = extended

        # ── Classification rules ──────────────────────────────────
        total_up = sum(extended)

        # FIST – all fingers curled
        if total_up == 0:
            return "fist"

        # OPEN PALM – all fingers extended
        if total_up >= 4 and index and middle and ring:
            return "open_palm"

        # PEACE / V-SIGN – index + middle up, others down
        if index and middle and not ring and not pinky:
            return "peace"

        # POINT UP – only index extended
        if index and not middle and not ring and not pinky:
            return "point_up"

        # THUMBS UP – only thumb extended
        if thumb and not index and not middle and not ring and not pinky:
            return "thumbs_up"

        # ROCK / HORNS – index + pinky up, middle + ring down
        if index and not middle and not ring and pinky:
            return "rock"

        return None

    @staticmethod
    def _thumb_extended(lm) -> bool:
        """
        Heuristic: thumb is 'extended' if tip (4) is farther from
        the palm base (wrist=0) than the thumb IP joint (3) along x-axis.
        """
        tip_dist = abs(lm[_THUMB_TIP].x - lm[_WRIST].x)
        ip_dist  = abs(lm[_THUMB_IP].x - lm[_WRIST].x)
        return tip_dist > ip_dist
