from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Configuración de rutas
UPLOAD_FOLDER = 'fotos'
DATABASE = 'db.db'

# Asegurarse de que exista la carpeta de fotos
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Crear la base de datos si no existe
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            message TEXT,
            image_path TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Configuración de la carpeta para subir archivos
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    """Guarda un mensaje de texto en la base de datos."""
    data = request.json
    sender = data.get('sender', 'anonymous')
    message = data.get('message', '')
    image_path = None

    # Guardar en la base de datos
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chats (sender, message, image_path)
        VALUES (?, ?, ?)
    ''', (sender, message, image_path))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})

@app.route('/send_image', methods=['POST'])
def send_image():
    """Guarda una imagen y su información en la base de datos."""
    if 'image' not in request.files:
        return jsonify({'status': 'error', 'message': 'No image provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400

    filename = datetime.now().strftime('%Y%m%d%H%M%S_') + file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Guardar en la base de datos
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chats (sender, message, image_path)
        VALUES (?, ?, ?)
    ''', ('anonymous', None, filepath))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'image_path': filepath})

@app.route('/get_chats', methods=['GET'])
def get_chats():
    """Obtiene todos los chats de la base de datos."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT sender, message, image_path, timestamp FROM chats ORDER BY timestamp ASC')
    chats = cursor.fetchall()
    conn.close()

    chat_list = []
    for sender, message, image_path, timestamp in chats:
        chat_list.append({
            'sender': sender,
            'message': message,
            'image_path': image_path,
            'timestamp': timestamp
        })

    return jsonify(chat_list)

@app.route('/fotos/<filename>')
def uploaded_file(filename):
    """Sirve archivos de la carpeta de fotos."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)