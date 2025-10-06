import streamlit as st
import requests
import uuid


st.title("chatbot")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Enter text")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        with st.spinner("thinking"):
            try:
                response = requests.post(
                    "http://127.0.0.1:5000/chat",
                    json={
                        "message": user_input, 
                        "session_id": st.session_state.session_id
                    },
                    timeout=35
                )
                
                if response.status_code == 200:
                    reply = response.json()["reply"]
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                else:
                    error_msg = f"Error: Server returned status {response.status_code}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    
            except requests.exceptions.ConnectionError:
                error_msg = "Cannot connect to Flask server. Make sure it's running on http://127.0.0.1:5000"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except requests.exceptions.Timeout:
                error_msg = "Request timed out. The model might be taking too long to respond."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

with st.sidebar:
    st.header("Chat Controls")
    
    if st.button("Clear Chat", use_container_width=True):
        try:
            requests.post(
                "http://127.0.0.1:5000/clear", 
                json={"session_id": st.session_state.session_id},
                timeout=5
            )
        except:
            pass
        
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.caption(f"Session ID: {st.session_state.session_id[:8]}...")
    st.caption(f"Messages: {len(st.session_state.messages)}")