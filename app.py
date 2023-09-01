import io
import os
import streamlit as st
import requests
from PIL import Image
from model import get_caption_model, generate_caption
from googletrans import Translator
import sqlite3

# Initialize Streamlit app
st.set_page_config(page_title="Image Caption Generator", layout="wide")

translator = Translator()

@st.cache_resource
def get_model():
    return get_caption_model()

caption_model = get_model()

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
                st.session_state.username = username
                st.session_state.selected_tab = "Generate Caption"
                st.balloons()
            else:
                st.error(LOGIN_ERROR_INVALID_CREDENTIALS)
        except sqlite3.OperationalError as e:
            st.error(f"An error occurred while trying to log in: {e}")            
        


def predict(cap_col):
    captions = []
    pred_caption = generate_caption('tmp.jpg', caption_model)

    cap_col.markdown('#### Predicted Captions:')
    captions.append(pred_caption)

    for _ in range(4):
        pred_caption = generate_caption('tmp.jpg', caption_model, add_noise=True)
        if pred_caption not in captions:
            captions.append(pred_caption)
    
    cap_col.markdown('<div class="caption-container">', unsafe_allow_html=True)
    for c in captions:
        cap_col.markdown(f'<div class="cap-line" style="color: black; background-color: light grey; padding: 5px; margin-bottom: 5px; font-family: \'Palatino Linotype\', \'Book Antiqua\', Palatino, serif;">{c}</div>', unsafe_allow_html=True)
    cap_col.markdown('</div>', unsafe_allow_html=True)
    
    

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
            st.markdown(f"<p style='{heading_style}'>Generate Caption</p>", unsafe_allow_html=True)
            st.markdown("Upload an image to generate a caption:")

            with st.sidebar:
                st.title("Options")
                selected_languages = st.multiselect("Select languages for translation:", ['en', 'ta', 'hi', 'zh-cn', 'es', 'fr', 'de', 'it', 'ja'])
                img_url = st.text_input("Enter Image URL:")
                img_upload = st.file_uploader("Upload Image:", type=['jpg', 'png', 'jpeg'])

            col1, col2 = st.columns(2)
            if img_url or img_upload:
                if img_url:
                    img = Image.open(requests.get(img_url, stream=True).raw)
                else:
                    img = Image.open(img_upload)

                img = img.convert('RGB')
                col1.image(img, caption="Input Image", use_column_width=True)
                img.save('tmp.jpg')
                predict(col2)

                for lang in selected_languages:
                    if lang != "en":
                         translated_caption = translator.translate(generate_caption, src="en", dest=lang)
                         st.markdown(f"<p style='font-size: 24px; font-weight: bold; margin-bottom: 20px;'>{lang.upper()} Translation:</p>", unsafe_allow_html=True)
                         st.write(translated_caption.text)

                              # Update the caption in the database

                            
        
                
    else:
        st.write("Please login to access this feature.")

    
            

if __name__ == "__main__":
    main() 