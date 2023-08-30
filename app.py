import sqlite3
import streamlit as st
from PIL import Image
from model import get_caption_model, generate_caption
from googletrans import Translator
import requests

# Initialize Streamlit app
st.set_page_config(page_title="Image Caption Generator", layout="wide")

# Initialize Translator
translator = Translator()

# Constants
SIGNUP_SUCCESS_MSG = "Signup successful! You can now login."
SIGNUP_ERROR_EXISTING_USER = "Username already exists. Please choose a different username."
LOGIN_SUCCESS_MSG = "Login successful!"
LOGIN_ERROR_INVALID_CREDENTIALS = "Login failed. Invalid username or password."

# Define CSS styles
heading_style = "font-size: 24px; font-weight: bold; text-align: center;"
input_style = "margin-top: 10px; padding: 5px; width: 100%;"

# Function to create the SQLite table if it doesn't exist
@st.cache_resource
def create_table():
    with sqlite3.connect("login.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')

# Function for signup section
def signup_section():

    st.markdown(f"<p style='{heading_style}'>Signup</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please fill in the details to sign up:</p>", unsafe_allow_html=True)

    new_username = st.text_input("New Username", key="new_username", help="Choose a unique username")
    new_password = st.text_input("New Password", type="password", key="new_password",  help="Password should be at least 8 characters long")
    new_email = st.text_input("Email", key="new_email", help="Enter a valid email address")

    if st.button("Signup"):
        if not new_username or not new_password or not new_email:
            st.error("All fields are required for signup.")
            return

        role = "user"

        try:
            with sqlite3.connect("login.db") as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                               (new_username, new_password, new_email, role))
            st.success(SIGNUP_SUCCESS_MSG)
            st.balloons()
        except sqlite3.IntegrityError:
            st.error(SIGNUP_ERROR_EXISTING_USER)

# Function for login section
def login_section():
    
    st.markdown(f"<p style='{heading_style}'>Login</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please enter your login details:</p>", unsafe_allow_html=True)

    username = st.text_input("Username", key="login_username", help="Enter your username")
    password = st.text_input("Password", type="password", key="login_password",help="Enter your password")

    if st.button("Login"):
        if not username or not password:
            st.error("Username and password are required for login.")
            return
        
        try:
            with sqlite3.connect("login.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                user = cursor.fetchone()

            if user and user[2] == password:
                st.success(LOGIN_SUCCESS_MSG)
                st.write(f"You are logged in as: {user[1]}")
                st.image("profile_image_placeholder.jpg", caption="Your Profile Image", width=100)

                st.session_state.username = username
                st.session_state.selected_tab = "Generate Caption"
                st.balloons()
            else:
                st.error(LOGIN_ERROR_INVALID_CREDENTIALS)
        except sqlite3.OperationalError as e:
            st.error(f"An error occurred while trying to log in: {e}")

def main():
    # Create the database table if it doesn't exist
    create_table()

    # Define the navigation tabs
    tabs = ["Signup", "Login", "Generate Caption"]

    # Select the active tab based on user input
    selected_tab = st.sidebar.selectbox("Navigation", tabs)

    # Route to the appropriate section based on the selected tab
    if selected_tab == "Signup":
        signup_section()
    elif selected_tab == "Login":
        login_section()
    elif selected_tab == "Generate Caption":
        # Check if a user is logged in before accessing the caption generation feature
        if hasattr(st.session_state, "username"):
            st.title("Generate Caption")
            st.markdown("Upload an image to generate a caption:")

            with st.sidebar:
                st.title("Options")
                selected_languages = st.multiselect("Select languages for translation:", ['en', 'ta', 'hi', 'zh-cn', 'es', 'fr', 'de', 'it', 'ja'])
                img_url = st.text_input("Enter Image URL:")
                img_upload = st.file_uploader("Upload Image:", type=['jpg', 'png', 'jpeg'])

            col1, col2 = st.columns([2, 3])

            if img_url or img_upload:
                if img_url:
                    img = Image.open(requests.get(img_url, stream=True).raw)
                else:
                    img = Image.open(img_upload)

                img = img.convert('RGB')
                col1.image(img, caption="Input Image", use_column_width=True)

                caption_model = get_caption_model()
                generated_caption = generate_caption(img, caption_model)

                if generated_caption:
                    col2.markdown('<div style="margin-top: 15px; padding: 10px; background-color: #e6f7ff; border-radius: 5px;">' + generated_caption + '</div>', unsafe_allow_html=True)
                else:
                    col2.markdown('<div style="margin-top: 15px; padding: 10px; background-color: #e6f7ff; border-radius: 5px;">Caption generation failed.</div>', unsafe_allow_html=True)

                if generated_caption:
                    st.markdown("<p style='font-size: 24px; font-weight: bold; margin-bottom: 20px;'>Generated Caption:</p>", unsafe_allow_html=True)
                    st.write(generated_caption)

                    if "en" in selected_languages:
                        st.markdown("<p style='font-size: 24px; font-weight: bold; margin-bottom: 20px;'>Edit Caption:</p>", unsafe_allow_html=True)
                        edited_caption = st.text_area("Edit the caption", value=generated_caption)

                        if edited_caption:
                            st.markdown("<p style='font-size: 24px; font-weight: bold; margin-bottom: 20px;'>Edited Caption:</p>", unsafe_allow_html=True)
                            st.write(edited_caption)

                            for lang in selected_languages:
                                if lang != "en":
                                    translated_caption = translator.translate(edited_caption, src="en", dest=lang)
                                    st.markdown(f"<p style='font-size: 24px; font-weight: bold; margin-bottom: 20px;'>{lang.upper()} Translation:</p>", unsafe_allow_html=True)
                                    st.write(translated_caption.text)

                            username = st.session_state.username
                            update_caption(username, edited_caption)  # Update the caption in the database

                            st.success("Caption updated and saved successfully!")
                    else:
                        st.info("Caption editing is only available for English language captions.")
        else:
            st.write("Please login to access this feature.")

if __name__ == "__main__":
    main() 
