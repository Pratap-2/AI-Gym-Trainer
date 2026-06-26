import streamlit as st
import os
import time
import pandas as pd
import altair as alt
from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.exercise_repository import init_db
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.exercise_video_processor import VideoProcessorClass
from services.tracking.metrics import sync_metrics_update
from services.persistence.exercise_repository import get_users_exercises
from groq import Groq
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio

  
def main():
    st.set_page_config(
        page_icon="🏋️‍♀️",
        page_title="AI Real-time GYM Coach",
        initial_sidebar_state="expanded",
        layout="centered"
    )

    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")

    init_db()

    if not render_login_wall():
        return 

    initial_session_defaults()

    if "voice_pipeline" not in st.session_state:
        try:
            api_key = os.environ.get("GROQ_API_KEY", "")

            if not api_key and hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                api_key = st.secrets["GROQ_API_KEY"]
            
            groq_client = Groq(api_key=api_key)
            llm_coach = LLMCoach(groq_client)
            tts = TextToSpeech()
            st.session_state.voice_pipeline = VoicePipeline(llm_coach, tts)
        except Exception as e:
            st.session_state.voice_pipeline = None

    workout_started = st.session_state.get("workout_started", False)
    
    with st.sidebar:
        st.title("🏋️‍♂️ GymPulse Coach")

        if st.session_state.username:
            st.caption(f"👤 Login as {st.session_state.username}")

        st.divider()

        st.subheader("Workout Plan")

        if not workout_started:
            plan_exercise = st.selectbox("Exercise", options=EXERCISE_OPTIONS, key="plan_exercise")

            plan_sets = st.number_input("Sets", min_value=0, max_value=50, key="plan_sets", step=1)

            plan_reps = st.number_input("Reps per Set", min_value=0, max_value=50, key="plan_reps", step=1)

            st.markdown("")

            start_session_button = st.button("START WORKOUT", width="stretch", key="start_session_button")

            if start_session_button:
                st.session_state.exercise_type = plan_exercise
                st.session_state.target_sets = int(plan_sets)
                st.session_state.reps_per_set = int(plan_reps)
                st.session_state.reps = 0
                st.session_state.workout_started = True
                st.session_state.set_cycle_started_at = time.time()
                st.session_state.last_saved_sets_completed = 0

                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_started",
                        exercise=plan_exercise,
                        metrics={}
                    )
                    
                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.session_state.last_notified_sets_completed = 0
                st.session_state.last_notified_workout_complete = False
                st.rerun()
        else:
            exercise = st.session_state.get("exercise_type")
            sets = st.session_state.get("target_sets")
            reps = st.session_state.get("reps_per_set")

            st.info(f"**{exercise}** -- {sets} Sets / {reps} Reps")

            end_session_button = st.button("END WORKOUT", key="end_session_button", width="stretch")

            if end_session_button:
                st.session_state.workout_started = False
                
                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_completed",
                        exercise=exercise,
                        metrics={}
                    )
                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.rerun()

        if workout_started:
            st.divider()

            exercise = st.session_state.get("exercise_type")
            total_reps = st.session_state.get("reps")
            current_set_reps = st.session_state.get("current_set_reps")
            reps_per_set = st.session_state.get("reps_per_set")
            sets_completed = st.session_state.get("sets_completed")
            target_sets = st.session_state.get("target_sets")

            st.subheader("Progress")

            st.metric("Total Reps", f"{total_reps}")
            st.metric("Current Set Reps", f"{current_set_reps} / {reps_per_set}")
            st.metric("Sets Completed", f"{sets_completed} / {target_sets}")

            st.divider()

            if exercise == "Squats":
                st.subheader("Squat Metrics")
                st.metric("Knee Angle", f"{st.session_state.knee_angle}°")
                st.metric("Back Angle", f"{st.session_state.back_angle}°")
                st.metric("Depth Status", st.session_state.depth_status)

            elif exercise == "Push-ups":
                st.subheader("Push-up Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Body Alignment", st.session_state.body_alignment)
                st.metric("Hip Position", st.session_state.hip_status)

            elif exercise == "Biceps Curls (Dumbbell)":
                st.subheader("Curl Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Shoulder Stability", st.session_state.shoulder_status)
                st.metric("Swing Detection", st.session_state.swing_status)

            elif exercise == "Shoulder Press":
                st.subheader("Shoulder Press Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Arm Extension", st.session_state.extension_status)
                st.metric("Back Arch", st.session_state.back_arch_status)

            elif exercise == "Lunges":
                st.subheader("Lunge Metrics")
                st.metric("Front Knee Angle", f"{st.session_state.front_knee_angle}°")
                st.metric("Torso Angle", f"{st.session_state.torso_angle}°")
                st.metric("Balance Status", st.session_state.balance_status)

            elif exercise == "Pull-ups":
                st.subheader("Pull-up Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Body Alignment", st.session_state.body_alignment)
                st.metric("Swing Detection", st.session_state.swing_status)

            elif exercise == "Triceps Dips":
                st.subheader("Triceps Dips Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Shoulder Stability", st.session_state.shoulder_status)
                st.metric("Torso Lean", st.session_state.swing_status)

    st.markdown(
        """
        <div style="margin-bottom:28px;">
          <h1 style="font-size:1.65rem; font-weight:300; color:#DCE0EA;
                     letter-spacing:-0.01em; margin:0 0 6px;">
            AI Real-time Gym Coach
          </h1>
          <p style="font-size:0.8rem; color:#585E6E; margin:0;
                    letter-spacing:0.02em;">
            Pose detection &nbsp;&middot;&nbsp; Rep counting &nbsp;&middot;&nbsp; Voice feedback
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div style="background: #11161f; padding: 24px; border-radius: 24px;
                    border: 1px solid rgba(255,255,255,0.06);">
          <p style="font-size:0.95rem; color:#cfd6e8; margin:0 0 16px; line-height:1.7;">
            Meet your AI coach — a friendly gym trainer who spots your form,
            counts your reps, and gives crisp cues so every set feels on point.
          </p>
          <div style="display:flex; align-items:center; gap:16px;">
            <div style="width:100px; height:100px; border-radius:24px; background:#171e2f;
                        display:flex; align-items:center; justify-content:center;">
              <svg width="72" height="72" viewBox="0 0 72 72" fill="none"
                   xmlns="http://www.w3.org/2000/svg">
                <rect x="8" y="34" width="56" height="28" rx="14" fill="#222b3d"/>
                <rect x="18" y="10" width="36" height="40" rx="18" fill="#3d5d7c"/>
                <circle cx="36" cy="18" r="12" fill="#dce0ea"/>
                <rect x="6" y="42" width="12" height="8" rx="4" fill="#d9920a"/>
                <rect x="54" y="42" width="12" height="8" rx="4" fill="#d9920a"/>
                <path d="M14 30L26 30" stroke="#dce0ea" stroke-width="2" stroke-linecap="round"/>
                <path d="M46 30L58 30" stroke="#dce0ea" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div style="flex:1;">
              <p style="font-size:0.78rem; color:#838fba; margin:0 0 8px; text-transform:uppercase; letter-spacing:0.16em;">
                Coach says
              </p>
              <p style="font-size:0.88rem; color:#e7ecff; margin:0; line-height:1.6;">
                &ldquo;Stay tight, keep your core engaged,
                and push through the last rep with confidence.&rdquo;
              </p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)

    if st.session_state.get("coach_feedback"):
        st.markdown("")
        st.success(f"🤖 **Coach:** {st.session_state.coach_feedback}")

    if not workout_started:
        st.markdown(
            """
            <div style="
                background: #141820;
                padding: 56px 32px 52px;
                text-align: center;
                margin: 24px 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 20px;
            ">
              <!-- figure doing squat -->
              <svg width="100" height="96" viewBox="0 0 100 96" fill="none" xmlns="http://www.w3.org/2000/svg">
                <!-- skeleton lines -->
                <line x1="50" y1="28" x2="50" y2="55" stroke="#2A2F3E" stroke-width="2"/>
                <line x1="50" y1="40" x2="32" y2="52" stroke="#2A2F3E" stroke-width="2"/>
                <line x1="50" y1="40" x2="68" y2="52" stroke="#2A2F3E" stroke-width="2"/>
                <line x1="50" y1="55" x2="36" y2="72" stroke="#2A2F3E" stroke-width="2"/>
                <line x1="50" y1="55" x2="64" y2="72" stroke="#2A2F3E" stroke-width="2"/>
                <line x1="36" y1="72" x2="28" y2="86" stroke="#2A2F3E" stroke-width="2"/>
                <line x1="64" y1="72" x2="72" y2="86" stroke="#2A2F3E" stroke-width="2"/>
                <!-- skeleton joints amber -->
                <circle cx="50" cy="17" r="7" fill="#1C2030" stroke="#D9920A" stroke-width="1.5"/>
                <circle cx="50" cy="28" r="3.5" fill="#D9920A" opacity="0.7"/>
                <circle cx="50" cy="55" r="3.5" fill="#D9920A" opacity="0.7"/>
                <circle cx="32" cy="52" r="3"   fill="#5A6070"/>
                <circle cx="68" cy="52" r="3"   fill="#5A6070"/>
                <circle cx="36" cy="72" r="3.5" fill="#D9920A" opacity="0.5"/>
                <circle cx="64" cy="72" r="3.5" fill="#D9920A" opacity="0.5"/>
                <circle cx="28" cy="86" r="3"   fill="#5A6070"/>
                <circle cx="72" cy="86" r="3"   fill="#5A6070"/>
                <!-- camera icon -->
                <rect x="2" y="4" width="22" height="16" rx="2" fill="none" stroke="#2A2F3E" stroke-width="1.5"/>
                <circle cx="13" cy="12" r="4" fill="none" stroke="#2A2F3E" stroke-width="1.5"/>
                <path d="M24 9 L30 6 L30 18 L24 15 Z" fill="#2A2F3E"/>
                <!-- scan line -->
                <line x1="2" y1="12" x2="30" y2="12" stroke="#D9920A" stroke-width="0.75" opacity="0.4" stroke-dasharray="2 2"/>
              </svg>

              <div>
                <p style="font-size:0.62rem; font-weight:500; letter-spacing:0.1em;
                          text-transform:uppercase; color:#585E6E; margin:0 0 10px;">
                  Camera inactive
                </p>
                <p style="font-size:0.875rem; color:#5A6070; margin:0; line-height:1.65;">
                  Set your exercise, sets and reps in the sidebar<br>
                  then press <span style="color:#DCE0EA; letter-spacing:0.04em;">START WORKOUT</span> to activate pose tracking.
                </p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        context = webrtc_streamer(
            key="exercise-analysis",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=VideoProcessorClass,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={
                "video": True,
                "audio": False
            },
            async_processing=True
        )

        sync_metrics_update(context)

        if context.state.playing:
            time.sleep(0.25)
            st.rerun()

        inject_webrtc_styles()

    st.divider()

    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:4px;">
          <svg width="18" height="18" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="1"  y="8.5" width="3.5" height="3" rx="0.5" fill="#D9920A" opacity="0.85"/>
            <rect x="0"  y="7"   width="2.5" height="6" rx="0.5" fill="#D9920A"/>
            <rect x="15.5" y="8.5" width="3.5" height="3" rx="0.5" fill="#D9920A" opacity="0.85"/>
            <rect x="17.5" y="7"   width="2.5" height="6" rx="0.5" fill="#D9920A"/>
            <rect x="4.5" y="9"  width="11"  height="2" rx="0.5" fill="#5A6070"/>
          </svg>
          <p style="font-size:0.62rem; font-weight:500; letter-spacing:0.1em;
                    text-transform:uppercase; color:#585E6E; margin:0;">
            Training Dashboard
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_id = st.session_state.get("user_id", 0)

    if isinstance(user_id, int):
        history_rows = get_users_exercises(user_id)

        arr = [
            {
                "Exercise": row['exercise_name'],
                "Reps": row['reps'],
                "Sets": row['sets'],
                "Time (sec)": row['time'],
                "Date": row['created_at']
            }
            for row in history_rows
        ]

        df = pd.DataFrame(arr)

        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
            df["Week"] = pd.to_datetime(df["Date"]).dt.to_period("W").astype(str)

            agg_df = df.groupby(["Exercise", "Date"]).agg({
                "Reps": "sum",
                "Sets": "sum",
                "Time (sec)": "sum"
            }).reset_index()

            tab1, tab2, tab3 = st.tabs(["Volume", "Weekly Trend", "Exercise Mix"])

            AMBER = "#F5A623"
            CHART_BG = "#0A0D14"

            with tab1:
                chart_volume = (
                    alt.Chart(agg_df)
                    .mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
                    .encode(
                        x=alt.X("Date:T", title="Date", axis=alt.Axis(labelColor="#888", titleColor="#888")),
                        y=alt.Y("Reps:Q", title="Total Reps", axis=alt.Axis(labelColor="#888", titleColor="#888")),
                        color=alt.Color(
                            "Exercise:N",
                            scale=alt.Scale(scheme="goldorange"),
                            legend=alt.Legend(labelColor="#aaa", titleColor="#aaa"),
                        ),
                        tooltip=["Date:T", "Exercise:N", "Reps:Q", "Sets:Q"],
                    )
                    .properties(background=CHART_BG, padding={"top": 16, "bottom": 16})
                    .configure_view(strokeWidth=0)
                    .configure_axis(gridColor="rgba(255,255,255,0.05)", domainColor="rgba(255,255,255,0.1)")
                )
                st.altair_chart(chart_volume, width='stretch')

            with tab2:
                weekly_df = df.groupby("Week").agg({"Sets": "sum"}).reset_index()
                chart_trend = (
                    alt.Chart(weekly_df)
                    .mark_line(point=alt.OverlayMarkDef(color=AMBER, size=60), color=AMBER, strokeWidth=2)
                    .encode(
                        x=alt.X("Week:O", title="Week", axis=alt.Axis(labelColor="#888", titleColor="#888", labelAngle=-30)),
                        y=alt.Y("Sets:Q", title="Total Sets", axis=alt.Axis(labelColor="#888", titleColor="#888")),
                        tooltip=["Week:O", "Sets:Q"],
                    )
                    .properties(background=CHART_BG, padding={"top": 16, "bottom": 16})
                    .configure_view(strokeWidth=0)
                    .configure_axis(gridColor="rgba(255,255,255,0.05)", domainColor="rgba(255,255,255,0.1)")
                )
                st.altair_chart(chart_trend, width='stretch')

            with tab3:
                mix_df = df.groupby("Exercise").agg({"Sets": "sum"}).reset_index()
                chart_donut = (
                    alt.Chart(mix_df)
                    .mark_arc(innerRadius=60, outerRadius=110)
                    .encode(
                        theta=alt.Theta("Sets:Q"),
                        color=alt.Color(
                            "Exercise:N",
                            scale=alt.Scale(scheme="goldorange"),
                            legend=alt.Legend(labelColor="#aaa", titleColor="#aaa"),
                        ),
                        tooltip=["Exercise:N", "Sets:Q"],
                    )
                    .properties(background=CHART_BG, height=280)
                    .configure_view(strokeWidth=0)
                )
                st.altair_chart(chart_donut, width='stretch')

        else:
            st.info("Complete your first workout to see training charts here.")


if __name__ == "__main__":
    main()
    