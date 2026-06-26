import streamlit as st
from services.persistence.exercise_repository import register_user, verify_user


_HERO_SVG = """
<div style="
  display:flex; flex-direction:column; align-items:center;
  padding: 48px 24px 40px; gap: 20px;
">
  <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- barbell -->
    <rect x="6" y="29" width="10" height="6" rx="1" fill="#D9920A" opacity="0.9"/>
    <rect x="4"  y="25" width="6"  height="14" rx="1" fill="#D9920A"/>
    <rect x="2"  y="27" width="4"  height="10" rx="1" fill="#E8A020"/>
    <rect x="48" y="29" width="10" height="6" rx="1" fill="#D9920A" opacity="0.9"/>
    <rect x="54" y="25" width="6"  height="14" rx="1" fill="#D9920A"/>
    <rect x="58" y="27" width="4"  height="10" rx="1" fill="#E8A020"/>
    <rect x="16" y="30" width="32" height="4" rx="1" fill="#5A6070"/>
    <!-- person silhouette -->
    <circle cx="32" cy="10" r="4.5" fill="#DCE0EA" opacity="0.55"/>
    <path d="M26 18 Q32 14 38 18 L40 30 H24 Z" fill="#DCE0EA" opacity="0.35"/>
    <path d="M27 30 L25 44 M37 30 L39 44" stroke="#DCE0EA" stroke-width="2.5" stroke-linecap="round" opacity="0.3"/>
  </svg>
  <div style="text-align:center;">
    <p style="font-size:0.62rem; font-weight:500; letter-spacing:0.12em; text-transform:uppercase;
              color:#585E6E; margin:0 0 8px;">AI-Powered</p>
    <h1 style="font-size:1.6rem; font-weight:300; color:#DCE0EA; margin:0; letter-spacing:-0.01em;">
      GymPulse Coach
    </h1>
    <p style="font-size:0.85rem; color:#5A6070; margin:10px 0 0; line-height:1.5;">
      Real-time pose detection &middot; Voice coaching &middot; Progress tracking
    </p>
  </div>
</div>
"""


def render_login_wall() -> bool:
    if st.session_state.get("user_id") is not None and st.session_state.get("username"):
        return True

    st.markdown(_HERO_SVG, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="e.g. Pratap")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", width='stretch')

            if submit:
                if not username or not password:
                    st.error("Username and password are required.")
                    return False

                user = verify_user(username, password)
                if user is None:
                    st.error("Invalid username or password.")
                    return False

                st.session_state.user_id = user["id"]
                st.session_state.username = user["username"]
                st.rerun()

    with tab_register:
        with st.form("register_form", clear_on_submit=False):
            new_username = st.text_input("Choose a username", placeholder="e.g. Pratap")
            new_password = st.text_input("Choose a password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            submit_reg = st.form_submit_button("Create Account", width='stretch')

            if submit_reg:
                if not new_username or not new_password:
                    st.error("All fields are required.")
                    return False
                if len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                    return False
                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                    return False

                user = register_user(new_username, new_password)
                if user is None:
                    st.error(f"Username '{new_username}' is already taken. Try another.")
                    return False

                st.session_state.user_id = user["id"]
                st.session_state.username = user["username"]
                st.success(f"Account created! Welcome, {user['username']}.")
                st.rerun()

    return False
