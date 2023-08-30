import io
import os
import streamlit as st
import requests
from PIL import Image
from model import get_caption_model, generate_caption
from googletrans import Translator

translator = Translator()

@st.cache_resource
def get_model():
    return get_caption_model()

caption_model = get_model()

def translate_caption(caption, target_language='en'):
    translated = translator.translate(caption, dest=target_language)
    return translated.text

def predict(cap_col):
    captions = []
    pred_caption = generate_caption('tmp.jpg', caption_model)

    cap_col.markdown('#### Predicted Captions:')
    translated_caption = translate_caption(pred_caption, target_language)
    captions.append(translated_caption)

    for _ in range(4):
        pred_caption = generate_caption('tmp.jpg', caption_model, add_noise=True)
        if pred_caption not in captions:
            translated_caption = translate_caption(pred_caption, target_language)
            captions.append(translated_caption)
    
    cap_col.markdown('<div class="caption-container">', unsafe_allow_html=True)
    for c in captions:
        cap_col.markdown(f'<div class="cap-line" style="color: black; background-color: light grey; padding: 5px; margin-bottom: 5px; font-family: \'Palatino Linotype\', \'Book Antiqua\', Palatino, serif;">{c}</div>', unsafe_allow_html=True)
    cap_col.markdown('</div>', unsafe_allow_html=True)

st.markdown('<h1 style="text-align:center; font-family:Arial; width:fit-content; font-size:3em; color:black; text-shadow: 2px 2px 4px #000000;">IMAGE CAPTION GENERATOR</h1>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

# Image URL input
img_url = st.text_input(label='Enter Image URL')

# Image upload input
img_upload = st.file_uploader(label='Upload Image', type=['jpg', 'png', 'jpeg'])

# Language selection dropdown
target_language = st.selectbox('Select Target Language', ['en', 'ta', 'hi', 'es', 'fr', 'zh-cn'], index=0)

# Process image and generate captions
if img_url:
    img = Image.open(requests.get(img_url, stream=True).raw)
    img = img.convert('RGB')
    col1.image(img, caption="Input Image", use_column_width=True)
    img.save('tmp.jpg')
    predict(col2)

    st.markdown('<center style="opacity: 70%">OR</center>', unsafe_allow_html=True)

elif img_upload:
    img = img_upload.read()
    img = Image.open(io.BytesIO(img))
    img = img.convert('RGB')
    col1.image(img, caption="Input Image", use_column_width=True)
    img.save('tmp.jpg')
    predict(col2)

# Remove temporary image file
if img_url or img_upload:
    os.remove('tmp.jpg')
