from core.base_exercise import BaseExercise

class SquatDetect(BaseExercise):
    def __init__(self):
        super().__init__()


    def reset(self):
        self.reps=0
        self.stage=None
    

    def process(self,landmarks):
        