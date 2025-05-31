import streamlit as st
from audio_recorder_streamlit import audio_recorder
import requests
import os
from gtts import gTTS
import io
import speech_recognition as sr

st.set_page_config(page_title="🎙️ Voice Bot (Groq + gTTS)", layout="wide")
st.title("🎙️ Speech Bot with Voice Reply 🔊")
st.sidebar.title("`Speak with LLMs + Hear the Answer!`")

def language_selector():
    lang_options = ["ar", "de", "en", "es", "fr", "it", "ja", "nl", "pl", "pt", "ru", "zh"]
    with st.sidebar:
        return st.selectbox("Speech Input Language", ["en"] + lang_options)

def tts_language_selector(key="tts_lang"):
    lang_map = {
        "English": "en",
        "Spanish": "es",
        "French": "fr",
        "Arabic": "ar",
        "German": "de",
        "Italian": "it",
        "Portuguese": "pt",
        "Russian": "ru",
        "Chinese": "zh-CN",
        "Japanese": "ja"
    }
    with st.sidebar:
        lang_choice = st.selectbox("TTS Language", list(lang_map.keys()), key=key)
        return lang_map[lang_choice]

def print_txt(text):
    if any("\u0600" <= c <= "\u06FF" for c in text):
        text = f"<p style='direction: rtl; text-align: right;'>{text}</p>"
    st.markdown(text, unsafe_allow_html=True)

def print_chat_message(message):
    text = message["content"]
    if message["role"] == "user":
        with st.chat_message("user", avatar="🎙️"):
            print_txt(text)
    else:
        with st.chat_message("assistant", avatar="🦙"):
            print_txt(text)

def groq_chat(api_key, model, chat_history):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": chat_history,
        "temperature": 0.2
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

def text_to_speech(text, lang_code):
    tts = gTTS(text=text, lang=lang_code)
    filename = "output.mp3"
    tts.save(filename)
    return filename
def main():
    with st.sidebar:
        groq_api_key = st.text_input("🔑 Groq API Key", type="password")
        model = st.selectbox("LLM Model", ["llama3-70b-8192", "mixtral-8x7b-32768", "gemma-7b-it"])
        input_lang = language_selector()
        tts_lang = tts_language_selector(key="tts_lang_sidebar")
    st.write("Record your question below and click 'Transcribe' to ask:")
    audio_bytes = audio_recorder()
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
    question = None
    if audio_bytes is not None:
        if st.button("Transcribe"):
            recognizer = sr.Recognizer()
            with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
                audio = recognizer.record(source)
            try:
                question = recognizer.recognize_google(audio, language=input_lang)
                st.success(f"Transcribed: {question}")
            except Exception as e:
                st.error(f"Speech recognition failed: {e}")
        #tts_lang = tts_language_selector(key="tts_lang_main")

    if not groq_api_key:
        st.info("Please enter your Groq API key to start chatting.")
        return

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    chat_history = st.session_state.chat_history

    for message in chat_history:
        print_chat_message(message)

    if question:
        user_message = {"role": "user", "content": question}
        print_chat_message(user_message)
        chat_history.append(user_message)

        with st.spinner("Groq is generating a response... ⚡️"):
            try:
                answer = groq_chat(groq_api_key, model, chat_history)
                ai_message = {"role": "assistant", "content": answer}
                print_chat_message(ai_message)
                chat_history.append(ai_message)

                if len(chat_history) > 20:
                    chat_history = chat_history[-20:]
                st.session_state.chat_history = chat_history

                # ---- TTS output ----
                with st.spinner(f"Generating voice reply with gTTS... 🔊"):
                    audio_file = text_to_speech(answer, lang_code=tts_lang)
                    st.audio(audio_file, format="audio/mp3", start_time=0)

            except Exception as e:
                st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
