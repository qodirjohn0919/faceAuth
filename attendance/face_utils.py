import cv2
import numpy as np
import base64
import os
import json

from django.conf import settings

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# LBPH confidence: 0 = identical, higher = more different.
# Values below this threshold are considered a match.
# Tune by running faces and printing distances; typically 80–100 is a good range.
FACE_MATCH_THRESHOLD = getattr(settings, 'FACE_MATCH_THRESHOLD', 80.0)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _enhance_image_for_recognition(image):
    """Apply CLAHE to the L channel to normalize brightness/contrast."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.merge((l, a, b))
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)


def _crop_and_encode(image, face_location):
    """
    Given a BGR image and a (top, right, bottom, left) face_location tuple,
    return a 100×100 uint8 grayscale face as a flat Python list (10 000 ints).
    Returns None if the crop is empty.
    """
    top, right, bottom, left = face_location
    face_crop = image[top:bottom, left:right]
    if face_crop.size == 0:
        return None
    resized = cv2.resize(face_crop, (100, 100))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY) \
        if len(resized.shape) == 3 else resized
    return gray.flatten().tolist()  # list of 10 000 ints (0-255)


# ---------------------------------------------------------------------------
# Public API — signatures identical to the original face_utils.py
# ---------------------------------------------------------------------------

def detect_faces_in_images(image):
    """
    Detect faces in a BGR image using Haar cascade.

    Returns a list of (top, right, bottom, left) tuples — same convention as
    face_recognition.face_locations() so validate_face_image() is unchanged.
    Only the largest detected face is returned to reduce false positives.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = FACE_CASCADE.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80),
    )
    if len(faces) == 0:
        return []

    # Sort by area descending → pick the largest face only
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    x, y, w, h = faces[0]
    return [(y, x + w, y + h, x)]  # (top, right, bottom, left)


def get_face_encoding(image, face_location=None):
    """
    Return a 10 000-element list (100×100 grayscale pixel values) that
    represents the face in *image*.  LBPH comparison happens at match time
    inside compare_faces(), so the raw pixel array is sufficient storage.

    Returns None if no face is found or the crop fails.
    """
    enhanced = _enhance_image_for_recognition(image)

    if face_location is None:
        locs = detect_faces_in_images(enhanced)
        if not locs:
            print('get_face_encoding: no face detected in image')
            return None
        face_location = locs[0]

    encoding = _crop_and_encode(enhanced, face_location)
    if encoding is None:
        print('get_face_encoding: face crop was empty')
    return encoding


def compare_faces(known_encoding, unknown_encoding, tolerance=None):
    """
    Use an LBPH recognizer to compare two encodings.

    Both encodings are 10 000-element lists of uint8 pixel values (100×100 gray).
    The recognizer is trained on *known_encoding* (1 sample, label 0) and then
    used to predict *unknown_encoding*.  LBPH confidence 0 = identical,
    higher values mean more dissimilar.

    Returns (is_match: bool, confidence: float).
    """
    if tolerance is None:
        tolerance = FACE_MATCH_THRESHOLD

    if known_encoding is None or unknown_encoding is None:
        return False, float('inf')

    try:
        known_face = np.array(known_encoding, dtype=np.uint8).reshape(100, 100)
        unknown_face = np.array(unknown_encoding, dtype=np.uint8).reshape(100, 100)

        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train([known_face], np.array([0]))
        _, confidence = recognizer.predict(unknown_face)

        is_match = confidence <= tolerance
        return is_match, float(confidence)

    except Exception as e:
        print(f'compare_faces error: {e}')
        return False, float('inf')


def find_matching_employee(unknown_encoding, employees):
    """
    Loop through *employees*, compare each stored face encoding against
    *unknown_encoding*, and return the best match under the threshold.

    Returns (Employee, confidence) or (None, None) if no match.
    """
    best_match = None
    best_confidence = float('inf')

    for employee in employees:
        known_encoding = employee.get_face_encoding_list()
        if known_encoding is None:
            continue

        is_match, confidence = compare_faces(known_encoding, unknown_encoding)
        print(f'  [{employee.employee_id}] {employee.full_name()} → confidence {confidence:.2f}')

        if is_match and confidence < best_confidence:
            best_match = employee
            best_confidence = confidence

    if best_match is not None:
        return best_match, best_confidence

    return None, None


def process_base64_image(base64_string):
    """Decode a base64-encoded image (with or without data-URL prefix) to a BGR ndarray."""
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        image_bytes = base64.b64decode(base64_string)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return image
    except Exception as e:
        print(f'process_base64_image error: {e}')
        return None


def validate_face_image(image):
    """
    Validate that *image* contains exactly one face.

    Returns a dict with keys: valid, message, face_count, face_location.
    """
    if image is None:
        return {
            'valid': False,
            'message': 'Rasm yuklanmadi (Image not loaded)',
            'face_count': 0,
            'face_location': None,
        }

    face_locations = detect_faces_in_images(image)
    face_count = len(face_locations)

    if face_count == 0:
        return {
            'valid': False,
            'message': 'Rasmda yuz topilmadi (No face found in image)',
            'face_count': 0,
            'face_location': None,
        }
    elif face_count > 1:
        return {
            'valid': False,
            'message': (
                f'Rasmda {face_count} ta yuz topildi. '
                f"Faqat bitta yuz bo'lishi kerak."
            ),
            'face_count': face_count,
            'face_location': None,
        }
    else:
        return {
            'valid': True,
            'message': 'Yuz muvaffaqiyatli aniqlandi (Face detected successfully)',
            'face_count': 1,
            'face_location': face_locations[0],
        }


def save_face_image(image, employee_id, filename=None):
    """Save *image* to media/faces/ and return the relative path, or None on error."""
    try:
        face_dir = os.path.join(settings.MEDIA_ROOT, 'faces')
        os.makedirs(face_dir, exist_ok=True)

        if filename is None:
            filename = f'{employee_id}_face.jpg'

        full_path = os.path.join(face_dir, filename)
        cv2.imwrite(full_path, image)
        return f'faces/{filename}'
    except Exception as e:
        print(f'save_face_image error: {e}')
        return None


def draw_face_rectangle(image, face_location, name=None, color=(0, 255, 0)):
    """Draw a bounding box (and optional name label) on *image* in-place."""
    top, right, bottom, left = face_location
    cv2.rectangle(image, (left, top), (right, bottom), color, 2)
    if name:
        cv2.rectangle(image, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        cv2.putText(
            image,
            name,
            (left + 6, bottom - 6),
            cv2.FONT_HERSHEY_DUPLEX,
            0.6,
            (255, 255, 255),
            1,
        )
