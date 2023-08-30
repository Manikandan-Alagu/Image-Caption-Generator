import sqlite3
import streamlit as st
from passlib.hash import bcrypt
from PIL import Image
from model import get_caption_model, generate_caption
from googletrans import Translator
import requests

# Initialize Streamlit app
st.set_page_config(page_title="Image Caption Generator", layout="wide")

# Initialize Translator
translator = Translator()

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

# Function to handle user signup
def signup():
    st.markdown("<p style='font-size: 24px; font-weight: bold; margin-bottom: 20px; text-align: center;'>Signup</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please fill in the details to sign up:</p>", unsafe_allow_html=True)
    
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    new_email = st.text_input("Email")

    if st.button("Signup"):
        if not new_username or not new_password or not new_email:
            st.error("All fields are required for signup.")
            return

        role = "user"
        hashed_password = bcrypt.hash(new_password)

        try:
            with sqlite3.connect("login.db") as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                               (new_username, hashed_password, new_email, role))
            st.success("Signup successful! You can now login.")
        except sqlite3.IntegrityError:
            st.error("Username already exists. Please choose a different username.")

# Function to handle user login
def login():
    st.markdown("<p style='font-size: 24px; font-weight: bold; margin-bottom: 20px; text-align: center;'>Login</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please enter your login details:</p>", unsafe_allow_html=True)
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not username or not password:
            st.error("Username and password are required for login.")
            return
        
        try:
            with sqlite3.connect("login.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                user = cursor.fetchone()

            if user and bcrypt.verify(password, user[2]):
                st.success("Login successful!")
                st.write(f"You are logged in as: {user[1]}")
                st.image("profile_image_placeholder.jpg", caption="Your Profile Image", width=100)

                st.session_state.username = username
                st.session_state.selected_tab = "Generate Caption"
            else:
                st.error("Login failed. Invalid username or password.")
        except sqlite3.OperationalError as e:
            st.error(f"An error occurred while trying to log in: {e}")

# Function to generate image caption and edit captions
@st.cache_resource
def generate_image_caption(img, caption_model):
    return generate_caption(img, caption_model)

def display_edit_caption(selected_languages, generated_caption):
    st.markdown("<p style='font-size: 24px; font-weight: bold; margin-bottom: 20px;'>Edit Caption:</p>", unsafe_allow_html=True)
    edited_caption = st.text_area("Edit the caption", value=generated_caption, key="edited_caption")

    if edited_caption:
        st.markdown("<p style='font-size: 24px; font-weight: bold; margin-bottom: 20px;'>Edited Caption:</p>", unsafe_allow_html=True)
        st.write(edited_caption)

        for lang in selected_languages:
            if lang != "en":
                translated_caption = translator.translate(edited_caption, src="en", dest=lang)
                st.markdown(f"<p style='font-size: 24px; font-weight: bold; margin-bottom: 20px;'>{lang.upper()} Translation:</p>", unsafe_allow_html=True)
                st.write(translated_caption.text)

        username = st.session_state.username
        st.balloons()
        st.success("Caption editing complete!")

# Main function to control the application flow
def main():
    create_table()

    tabs = ["Signup", "Login", "Generate Caption"]
    selected_tab = st.sidebar.selectbox("Navigation", tabs)

    if selected_tab == "Signup":
        signup()
    elif selected_tab == "Login":
        login()
    elif selected_tab == "Generate Caption":
        if hasattr(st.session_state, "username"):
            st.sidebar.info("Welcome to the Image Caption Generator!")
            st.sidebar.warning("Be sure to upload a clear and relevant image.")
            generate_caption_button = st.sidebar.button("Generate Caption")
            
            if generate_caption_button:
                st.sidebar.info("Generating caption... Please wait.")
                
                with st.spinner("Generating caption..."):
                    img_url = st.sidebar.text_input("Enter Image URL:")
                    img_upload = st.sidebar.file_uploader("Upload Image:", type=['jpg', 'png', 'jpeg'])

                    if img_url or img_upload:
                        if img_url:
                            img = Image.open(requests.get(img_url, stream=True).raw)
                        else:
                            img = Image.open(img_upload)

                        img = img.convert('RGB')
                        caption_model = get_caption_model()
                        generated_caption = generate_image_caption(img, caption_model)

                        if generated_caption:
                            st.sidebar.success("Caption generated successfully!")
                            selected_languages = st.sidebar.multiselect("Select languages for translation:", ['en', 'ta', 'hi', 'zh-cn', 'es', 'fr', 'de', 'it', 'ja'])
                            display_edit_caption(selected_languages, generated_caption)
                        else:
                            st.sidebar.error("Caption generation failed.")
            else:
                generate_image_caption()

        else:
            st.write("Please login to access this feature.")

if __name__ == "__main__":
    main()
