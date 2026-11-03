import streamlit as st
import sys
import textwrap
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT /  ".env")

# Add project root to Python path
sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="ATS Resume Scorer",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# AUTH state. Populated by Supabase signin/ signup /OAuth.
# All Four are None when signed out, all four are set when signed in.
for key, default in [
    ("access_token", None),
    ("refresh_token", None),
    ("user_id", None),  # Supabase auth user id (uuid); also used by api_client
    ("user_email", None),
    ("auth_error", None),
    ("auth_info", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# If we Just came back from Google OAuth, Supabase, appends `?code=<authcode>`
# To the redirect URL. Exchange it for a session before rendering anything.

if (
    not st.session_state.access_token
    and "code" in st.query_params
):
    from frontend.services import supabase_client
    result = supabase_client.exchange_code_for_session(st.query_params["code"])

    # Always clear the ?code= param so a refresh doesn't try to re-exchange.
    st.query_params.clear()
    if "error" in result:
        st.session_state.auth_error = f"Google sign-in failed: {result['error']}"

    else:
        st.session_state.access_token = result["access_token"]
        st.session_state.refresh_token = result["refresh_token"]
        st.session_state.user_id       = result["user_id"]
        st.session_state.user_email    = result["email"]
        st.rerun()

# Load Custom CSS
def load_css():
    try:
        css_path = Path(__file__).parent / 'assets' / 'style.css'
        with open(css_path, 'r') as f:
            return f'<style>{f.read()}</style>'
    except FileNotFoundError:
        return ''


if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True

light_theme_css = ''
if not st.session_state.dark_mode:
    light_theme_css = textwrap.dedent("""
    <style>
    :root {
        color-scheme: light;
        --primary-color: #087F6B;
        --primary-hover: #066A59;
        --primary-light: #50B99B;
        --primary-dark: #155E46;
        --text-primary: #172033;
        --text-secondary: #596579;
        --text-muted: #8490A3;
        --background-light: #D6E2D9;
        --background-white: #F7FAF7;
        --border-color: #C6D6CC;
        --border-light: #E4ECE6;
    }
    .stApp, [data-testid="stAppViewContainer"] {
        color: #172033 !important;
        background: radial-gradient(ellipse at 82% 0%, rgba(75,145,111,.24), transparent 40rem),
                    linear-gradient(145deg, #DCE7DE, #CCDAD1 58%, #D7E1DA) !important;
    }
    [data-testid="stMain"], [data-testid="stMainBlockContainer"], [data-testid="stHeader"] {
        background: transparent !important;
    }
    [data-testid="stSidebar"] {
        color: #172033 !important;
        background: linear-gradient(180deg, #EEF3EF, #E2EBE4) !important;
        border-right: 1px solid #C6D6CC;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color: #526176 !important; }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp [data-testid="stMarkdownContainer"] h1,
    .stApp [data-testid="stMarkdownContainer"] h2,
    .stApp [data-testid="stMarkdownContainer"] h3,
    .stApp [data-testid="stMarkdownContainer"] h4 { color: #172033 !important; }
    .stApp p, .stApp li, .stApp [data-testid="stMarkdownContainer"] { color: #45546A; }
    .stApp [data-testid="stMarkdownContainer"] strong {
        color: #263B31 !important; -webkit-text-fill-color: #263B31 !important;
    }
    .stApp .main-header h1, .stApp .main-header h2, .stApp .main-header h3,
    .stApp .main-header p, .main-header [data-testid="stMarkdownContainer"] {
        color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important;
    }
    .main-header h3 { color: #E8F1FC !important; }
    .main-header p { color: #D4E2F2 !important; }
    .main-header {
        background: linear-gradient(125deg, #142923, #0B5B48 58%, #0C7860) !important;
        box-shadow: 0 18px 42px rgba(12,78,55,.22) !important;
    }
    [data-testid="stMetric"], [data-testid="stExpander"],
    [data-testid="stVerticalBlockBorderWrapper"], .metric-card, .feature-card, .card-elevated {
        color: #172033 !important;
        background: linear-gradient(145deg, #F9FCF9, #EEF4EF) !important;
        border-color: #C6D6CC !important;
        box-shadow: 0 5px 16px rgba(34,55,86,.07);
    }
    [data-testid="stMetricLabel"] { color: #596579 !important; }
    [data-testid="stMetricValue"] { color: #172033 !important; }
    [data-testid="stExpander"] summary { color: #25344A !important; }
    [data-testid="stTextInput"] [data-baseweb="input"],
    [data-testid="stTextInput"] [data-baseweb="base-input"] {
        background: #FFFFFF !important; border: 1px solid #C6D6CC !important;
        border-radius: 11px !important; box-shadow: none !important; overflow: hidden !important;
    }
    [data-testid="stTextInput"] input, .stTextArea textarea, .stNumberInput input,
    [data-baseweb="select"] > div, [data-baseweb="input"] > div {
        color: #263B31 !important; background: #FFFFFF !important; border-color: #C6D6CC !important;
        box-shadow: none !important;
    }
    [data-testid="stTextInput"] input {
        border: 0 !important; border-radius: 0 !important; outline: none !important;
    }
    [data-testid="stTextInput"] button {
        color: #45645A !important; background: #EAF1EB !important;
        border: 0 !important; border-left: 1px solid #D4E0D7 !important;
        border-radius: 0 !important; box-shadow: none !important;
        width: 44px !important; min-width: 44px !important;
        align-self: stretch !important; display: inline-flex !important;
        align-items: center !important; justify-content: center !important;
    }
    [data-testid="stTextInput"] button:hover { background: #DDEBE0 !important; }
    [data-testid="stTextInput"] button svg { color: #45645A !important; }
    [data-testid="stTextInput"] button svg * { stroke: currentColor !important; }
    [data-baseweb="select"] > div { border-radius: 10px !important;
    }
    [data-testid="stTextInput"] input::placeholder, .stTextArea textarea::placeholder { color: #84978B !important; }
    .stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primary"] {
        color: #FFFFFF !important;
        background: linear-gradient(110deg, #087F6B, #159875 52%, #257F69) !important;
        border-color: rgba(255,255,255,.25) !important;
        box-shadow: 0 7px 18px rgba(12,137,94,.25) !important;
    }
    .stButton > button[kind="primary"] *, [data-testid="stFormSubmitButton"] > button[kind="primary"] * {
        color: #FFFFFF !important;
    }
    .stButton > button:not([kind="primary"]), .stDownloadButton > button {
        color: #315144 !important; background: #F7FAF7 !important; border-color: #C6D6CC !important;
    }
    .stButton > button:not([kind="primary"]):hover, .stDownloadButton > button:hover {
        color: #155E46 !important; background: #E5F0E7 !important; border-color: #9BC4A9 !important;
    }
    [data-testid="stFormSubmitButton"] > button:not([kind="primary"]),
    .stLinkButton a, [data-testid="stLinkButton"] {
        color: #315144 !important; background: #F7FAF7 !important; border: 1px solid #C6D6CC !important;
    }
    .stLinkButton a:hover, [data-testid="stLinkButton"]:hover {
        color: #155E46 !important; background: #E5F0E7 !important; border-color: #9BC4A9 !important;
    }
    .stLinkButton { background: transparent !important; border: 0 !important; }
    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus,
    [data-baseweb="select"] > div:focus-within {
        border-color: #087F6B !important; box-shadow: 0 0 0 3px rgba(8,127,107,.16) !important; outline: none !important;
    }
    .st-key-theme_toggle button {
        color: #315144 !important; background: linear-gradient(145deg, #F8FBF8, #E9F0EA) !important;
        border-color: #C6D6CC !important; box-shadow: 0 4px 12px rgba(35,65,48,.12);
    }
    .st-key-theme_toggle button:hover { background: #E5F0E7 !important; border-color: #9BC4A9 !important; }
    .stTabs [data-baseweb="tab-list"] { border-bottom-color: #DCE4EF; }
    .stTabs [data-baseweb="tab"] { color: #596579; }
    .stTabs [aria-selected="true"] { color: #087F6B !important; }
    [data-testid="stDataFrame"], [data-testid="stTable"] { border-color: #DCE4EF; }
    [data-testid="stAlert"] { color: #25344A; background: #FFFFFF; border-color: #DCE4EF; }
    .stMainBlockContainer [data-testid="stHorizontalBlock"] > [data-testid="column"]:has([data-testid="stMarkdownContainer"] h3),
    .stMainBlockContainer [data-testid="stHorizontalBlock"] > [data-testid="column"]:has([data-testid="stMarkdownContainer"] h4) {
        color: #34463B !important; background: linear-gradient(145deg, #F8FBF8, #EAF1EB) !important;
        border: 1px solid #C6D6CC !important; border-top: 3px solid #B68A43 !important;
        border-radius: 16px; padding: 1rem 1.15rem; box-shadow: 0 8px 22px rgba(35,65,48,.08) !important;
    }
    .stMainBlockContainer [data-testid="stHorizontalBlock"] > [data-testid="column"]:has([data-testid="stMarkdownContainer"] h3):hover,
    .stMainBlockContainer [data-testid="stHorizontalBlock"] > [data-testid="column"]:has([data-testid="stMarkdownContainer"] h4):hover {
        border-color: #9BC4A9 !important; box-shadow: 0 14px 28px rgba(35,65,48,.12) !important;
    }
    .stMainBlockContainer [data-testid="stHorizontalBlock"] > [data-testid="column"]:has([data-testid="stMarkdownContainer"] h3) strong,
    .stMainBlockContainer [data-testid="stHorizontalBlock"] > [data-testid="column"]:has([data-testid="stMarkdownContainer"] h4) strong {
        color: #263B31 !important; -webkit-text-fill-color: #263B31 !important;
    }
    </style>
    """)

st.markdown(load_css() + "\n" + light_theme_css, unsafe_allow_html=True)

# Initialize session state for View Management
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'landing'


# Sidebar Navigation
with st.sidebar:
    st.markdown("## Navigation")

    if st.button("🏠 Home", use_container_width=True):
        st.session_state.current_view = 'landing'
        st.rerun()
    
    if st.button("🎯 ATS Scorer", use_container_width=True):
        st.session_state.current_view = 'scorer'
        st.rerun()
    
    if st.button("📊 History", use_container_width=True):
        st.session_state.current_view = 'history'
        st.rerun()
    
    if st.button("📚 Resources", use_container_width=True):
        st.session_state.current_view = 'resources'
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 👤 Account")

    from frontend.services import supabase_client

    if st.session_state.access_token:
        # Signed-In state: show email + sign-out button.
        from frontend.services import supabase_client
        user_name = "User"

        try:
            user = supabase_client.get_current_user()

            if user:
                metadata = user.user_metadata or {}

                user_name = (
                    metadata.get("full_name")
                    or metadata.get("name")
                    or metadata.get("username")
                    or (st.session_state.user_email or "").split("@")[0]
                    or "User"
                )

        except Exception:
            user_name = (
                (st.session_state.user_email or "").split("@")[0]
                or "User"
            )

        st.caption(f"Signed in as: **{user_name}**")


        if st.button("Signed Out", use_container_width=True):
            supabase_client.sign_out()
            for k in ("access_token", "refresh_token", "user_id","user_email"):
                st.session_state[k] = None
            st.rerun()
    else:
        # Signed-Out state: Tabs for Sign-In vs Sign-Up + Google OAuth Button.
        if st.session_state.auth_error:
            st.error(st.session_state.auth_error)
            st.session_state.auth_error = None
        if st.session_state.auth_info:
            st.info(st.session_state.auth_info)
            st.session_state.auth_info = None

        tab_in, tab_up = st.tabs(["Sign In", "Sign Up"])

        with tab_in:
            with st.form("signin_form", clear_on_submit=False):
                email  =st.text_input("Email", key="signin_email")
                password = st.text_input("Password", type="password", key="signin_pw")
                submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                result = supabase_client.sign_in_with_password(email, password)
                if "error" in result:
                    st.session_state.auth_error = result["error"]

                else:
                    st.session_state.access_token  = result["access_token"]
                    st.session_state.refresh_token = result["refresh_token"]
                    st.session_state.user_id       = result["user_id"]
                    st.session_state.user_email    = result["email"]
                st.rerun()

            with tab_up:
                with st.form("signup_form", clear_on_submit=False):
                    email_up = st.text_input("Email", key="signup_email")
                    password_up = st.text_input("Password (min 6 chars)", type="password", key="signup_pw")
                    submitted_up = st.form_submit_button("Create account", use_container_width=True)
                if submitted_up:
                    result = supabase_client.sign_up_with_password(email_up, password_up)
                    if "error" in result:
                        st.session_state.auth_error = result["error"]
                    elif result.get("pending_confirmation"):
                        st.session_state.auth_info = (
                            f"Check your inbox — confirmation email sent to {result['email']}."
                        )
                    else:
                        st.session_state.access_token  = result["access_token"]
                        st.session_state.refresh_token = result["refresh_token"]
                        st.session_state.user_id       = result["user_id"]
                        st.session_state.user_email    = result["email"]
                    st.rerun()

            st.markdown("<div style='text-align:center; margin: 8px 0; color:#94a3b8;'>or</div>",
                        unsafe_allow_html=True)

            oauth = supabase_client.google_oauth_url()
            if "error" in oauth:
                st.caption(f"Google sign-in unavailable: {oauth['error']}")
            else:
                # Streamlit's native link handles external OAuth navigation safely
                # from its sandboxed app frame (it opens in a new tab).
                st.link_button(
                    "Continue with Google",
                    oauth["url"],
                    use_container_width=True,
                )
                

# Main content appearance control
_, theme_control = st.columns([18, 1])
with theme_control:
    next_icon = ":material/light_mode:" if st.session_state.dark_mode else ":material/dark_mode:"
    next_mode = "light" if st.session_state.dark_mode else "dark"
    if st.button(" ", icon=next_icon, key="theme_toggle", help=f"Switch to {next_mode} mode"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# Main Content Area - Render bases on current View
if st.session_state.current_view == 'landing':
    # Import and render landing page
    from frontend.views import landing
    landing.render()

elif st.session_state.current_view == 'scorer':
    # Import and render scorer page
    from frontend.views import scorer
    scorer.render()

elif st.session_state.current_view == 'history':
    # Improt and render history page
    from frontend.views import history
    history.render()

elif st.session_state.current_view == 'resources':
    # Import and render resource page
    from frontend.views import resources
    resources.render()


