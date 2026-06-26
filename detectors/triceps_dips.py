import math
from core.base_exercise import BaseExercise


class TricepsDipsDetector(BaseExercise):
    DOWN_THRESHOLD = 90     # elbows bent (bottom of dip)
    UP_THRESHOLD = 155      # arms extended (top of dip)
    MIN_VISIBILITY = 0.6
    SHRUG_TOLERANCE = 0.04  # shoulder rises above elbow by this fraction

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24

    def __init__(self):
        super().__init__()

    def reset(self):
        self.reps = 0
        self.stage = None

    def process(self, landmarks):
        left_vis = landmarks[self.LEFT_ELBOW].visibility
        right_vis = landmarks[self.RIGHT_ELBOW].visibility

        if left_vis >= right_vis:
            shoulder_idx = self.LEFT_SHOULDER
            elbow_idx = self.LEFT_ELBOW
            wrist_idx = self.LEFT_WRIST
        else:
            shoulder_idx = self.RIGHT_SHOULDER
            elbow_idx = self.RIGHT_ELBOW
            wrist_idx = self.RIGHT_WRIST

        elbow_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, elbow_idx),
            self.get_point(landmarks, wrist_idx),
        )

        key_visible = (
            landmarks[shoulder_idx].visibility > self.MIN_VISIBILITY
            and landmarks[elbow_idx].visibility > self.MIN_VISIBILITY
            and landmarks[wrist_idx].visibility > self.MIN_VISIBILITY
        )

        if key_visible:
            if elbow_angle < self.DOWN_THRESHOLD:
                self.stage = "down"

            if elbow_angle > self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        # Shoulder shrug: shoulder y should be above (smaller y value) elbow y
        # Shrugging = shoulder y rises toward elbow y (values converge/cross)
        shoulder_y = landmarks[shoulder_idx].y
        elbow_y = landmarks[elbow_idx].y
        shrug_delta = elbow_y - shoulder_y  # normally positive (elbow below shoulder)

        if shrug_delta < self.SHRUG_TOLERANCE:
            shoulder_status = "SHRUGGING"
        else:
            shoulder_status = "STABLE"

        # Forward lean: torso angle from vertical using shoulder-hip vector
        shoulder_mid_x = (landmarks[self.LEFT_SHOULDER].x + landmarks[self.RIGHT_SHOULDER].x) / 2
        shoulder_mid_y = (landmarks[self.LEFT_SHOULDER].y + landmarks[self.RIGHT_SHOULDER].y) / 2
        hip_mid_x = (landmarks[self.LEFT_HIP].x + landmarks[self.RIGHT_HIP].x) / 2
        hip_mid_y = (landmarks[self.LEFT_HIP].y + landmarks[self.RIGHT_HIP].y) / 2

        dx = shoulder_mid_x - hip_mid_x
        dy = hip_mid_y - shoulder_mid_y

        torso_lean = math.degrees(math.atan2(abs(dx), abs(dy))) if dy != 0 else 0.0
        swing_status = "UPRIGHT" if torso_lean < 20 else "LEANING FORWARD"

        return {
            "reps": self.reps,
            "elbow_angle": int(elbow_angle),
            "shoulder_status": shoulder_status,
            "swing_status": swing_status,
        }
