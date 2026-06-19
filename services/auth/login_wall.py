import streamlit as st


def render_login_wall():
    if st.session_state.get("user_idx") is not None and st.session_state.get("username"):
        return True
    
    st.title("🏋️‍♂️ AI Real-time GYM Trainer")
    st.markdown("### Welcome to the AI Real-time GYM Trainer! Please log in to continue.❤️")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Name (unique)", placeholder="unique name e.g. Pratap")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Start Training", width="stretch")

        if submit_button:
            if not username:
                st.error("Name cannot be empty.")
                return False
            if not password:
                st.error("Password cannot be empty.")
                return False

            st.session_state.user_idx = 1
            st.session_state.username = username
            st.rerun()

    return False