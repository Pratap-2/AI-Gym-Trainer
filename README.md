# AI Gym Trainer

A Streamlit-based realtime AI gym coaching app. The project is structured to support workout planning, session state, custom UI styling, and future extensions for pose detection and workout analytics.

## Features

- Streamlit user login form and session handling
- Workout planning UI with exercise, sets, and reps
- Real-time workout progress display using Streamlit metrics
- Custom CSS and local font injection
- Config-driven exercise options
- Session defaults initialized on startup

## Requirements

- Python 3.12+
- Streamlit
- Optional future dependencies for AI/pose detection:
  - `mediapipe`
  - `opencv-python-headless`
  - `numpy`
  - `pandas`
  - `streamlit-webrtc`

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/<your-org>/AI-Gym-Trainer.git
   cd AI-Gym-Trainer
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Running the app

```bash
streamlit run main.py
```

Then open the local Streamlit URL shown in the terminal.

## Project structure

- `main.py` – Main Streamlit app and UI flow
- `services/auth/login_wall.py` – Login screen and session-based authentication
- `services/state/session_defaults.py` – Workout and session state initialization
- `services/config/workout_config.py` – Exercise option definitions
- `services/ui/style_loader.py` – CSS and local font injection helpers
- `static/` – Static assets such as `style.css` and font files
- Empty package placeholders:
  - `core/`
  - `detectors/`
  - `ml_models/`
  - `pages/`
  - `services/persistence/`

## Notes

- The current app uses static state metrics and UI only.
- The repository is ready for extension with AI pose detection and exercise analytics.

## Extension ideas

- Add webcam-based exercise detection in `detectors/`
- Build model wrappers and evaluation in `ml_models/`
- Add persistent workout history in `services/persistence/`
- Split app UI into reusable page modules under `pages/`
- Add user profiles and saved workout plans
- Improve login/authentication with secure user storage


Made with love by Aditya Pratap Singh 🤷‍♂️