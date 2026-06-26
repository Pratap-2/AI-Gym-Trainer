import math
from core.base_exercise import BaseExercise


class PullUpDetector(BaseExercise):
    UP_THRESHOLD = 70       # elbows fully flexed (chin over bar)
    DOWN_THRESHOLD = 150    # arms extended (hanging position)
    MIN_VISIBILITY = 0.6
    SWING_THRESHOLD = 12    # degrees of hip sway before flagging

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
            if elbow_angle < self.UP_THRESHOLD:
                self.stage = "up"

            if elbow_angle > self.DOWN_THRESHOLD and self.stage == "up":
                self.stage = "down"
                self.reps += 1

        # Body alignment: shoulder-hip vertical check
        shoulder_x = (landmarks[self.LEFT_SHOULDER].x + landmarks[self.RIGHT_SHOULDER].x) / 2
        hip_x = (landmarks[self.LEFT_HIP].x + landmarks[self.RIGHT_HIP].x) / 2
        shoulder_y = (landmarks[self.LEFT_SHOULDER].y + landmarks[self.RIGHT_SHOULDER].y) / 2
        hip_y = (landmarks[self.LEFT_HIP].y + landmarks[self.RIGHT_HIP].y) / 2

        dx = shoulder_x - hip_x
        dy = hip_y - shoulder_y  # positive when hips below shoulders

        lean_angle = math.degrees(math.atan2(abs(dx), abs(dy))) if dy != 0 else 0.0
        body_alignment = "STRAIGHT" if lean_angle < 15 else "BODY SWINGING"

        # Swing: horizontal hip deviation from shoulder line
        hip_deviation = abs(hip_x - shoulder_x)
        swing_status = "NO SWING" if hip_deviation < 0.08 else "SWINGING"

        return {
            "reps": self.reps,
            "elbow_angle": int(elbow_angle),
            "body_alignment": body_alignment,
            "swing_status": swing_status,
        }
