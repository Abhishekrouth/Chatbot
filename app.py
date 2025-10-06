from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

app = Flask(__name__)

model_name = "Qwen/Qwen1.5-0.5B-Chat"

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True,torch_dtype=torch.float32)
sessions = {}

def format_history(history):
    messages = []
    for msg in history:
        messages.append({"role": "user", "content": msg["user"]})
        messages.append({"role": "assistant", "content": msg["bot"]})
    return messages

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").strip()
    session_id = data.get("session_id", "default")

    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    history = sessions.setdefault(session_id, [])

    messages = format_history(history[-2:])
    messages.append({"role": "user", "content": user_input})

    try:
        text = tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)\
        
        model_inputs = tokenizer([text], return_tensors="pt")
        with torch.no_grad():generated_ids = model.generate(model_inputs.input_ids,max_new_tokens=50,temperature=0.9,do_sample=True,
                top_p=0.9,pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id)
    
        generated_ids = [
            output_ids[len(input_ids):] 
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        
        bot_reply = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        if not bot_reply:
            bot_reply = "Error"
        
    except Exception as e:
        print(f"Error generating response: {e}")
        bot_reply = "Sorry, I encountered an error processing your message."
    history.append({"user": user_input, "bot": bot_reply})

    return jsonify({"reply": bot_reply})

@app.route("/clear", methods=["POST"])
def clear_session():

    data = request.get_json()
    session_id = data.get("session_id", "default")
    sessions.pop(session_id, None)
    return jsonify({"message": f"Session '{session_id}' cleared."})


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)