from flask import Flask, render_template, request, jsonify
import pyrebase
from openai import OpenAI
import os
from werkzeug.utils import secure_filename
from config import firebaseConfig


# Initialize Flask App
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Firebase
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# Initialize OpenAI Client

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")

    if not user_input:
        return jsonify({"error": "Message cannot be empty"}), 400

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful and empathetic therapist AI."},
            {"role": "user", "content": user_input}
        ]
    )

    return jsonify({"response": response.choices[0].message.content})
@app.route('/describe-image', methods=['POST'])
def describe_image():
    filename = request.json.get("filename")
    if not filename:
        return jsonify({"error": "Filename missing"}), 400

    # More therapeutic, emotional, and supportive instruction
    prompt = (
        f"A young student has uploaded a drawing titled '{filename}'. "
        "You are a friendly, encouraging art teacher for children. "
        "First, say something kind and supportive about their art (1–2 sentences), like what feelings it shows or what makes it special. "
        "Then, suggest one fun idea they could add to it to make it even cooler. "
        # "After that, give a gentle idea for what they could draw next time. "
    )
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are an art therapist AI helping users reflect emotionally on their art and suggesting gentle next steps for healing and creativity."
            },
            {"role": "user", "content": prompt}
        ]
    )

    full_reply = response.choices[0].message.content.strip()

    # Extract last line in quotes as DALL·E prompt
    dalle_prompt = ""
    for line in reversed(full_reply.splitlines()):
        if line.strip().startswith('"') and line.strip().endswith('"'):
            dalle_prompt = line.strip().strip('"')
            break

    if not dalle_prompt:
        dalle_prompt = "A peaceful forest path in pastel watercolor style"

    # Generate DALL·E image
    image_response = client.images.generate(
        model="dall-e-3",
        prompt=dalle_prompt,
        size="1024x1024",
        n=1
    )

    return jsonify({
        "description": full_reply,
        "image_url": image_response.data[0].url,
        "dalle_prompt": dalle_prompt
    })




@app.route('/generate-image', methods=['POST'])
def generate_image():
    prompt = request.json.get("prompt")

    if not prompt:
        return jsonify({"error": "Prompt cannot be empty"}), 400

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        n=1
    )

    return jsonify({"image_url": response.data[0].url})

@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    analysis = analyze_image(filepath)
    return jsonify({"message": "Image uploaded successfully", "analysis": analysis})

def analyze_image(filepath):
    return "The image has been analyzed. Suggestions: Add more calming colors."

@app.route('/register', methods=["GET", "POST"])
def register():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        user = auth.create_user_with_email_and_password(email, password)
        return jsonify({"message": "Registration successful!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)