from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime
from flask_cors import CORS
from flask_socketio import SocketIO, emit

app = Flask(__name__)
CORS(app)

# Inicializar SocketIO
socketio = SocketIO(app)

# Configuración de rutas
UPLOAD_FOLDER = 'fotos'
DATABASE = 'db.db'

# Asegurarse de que exista la carpeta de fotos
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Crear la base de datos si no existe y agregar columnas si faltan
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Crear la tabla si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            message TEXT,
            image_path TEXT,
            reply_to INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Verificar si la columna reply_to existe, si no, agregarla
    cursor.execute("PRAGMA table_info(chats)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'reply_to' not in columns:
        cursor.execute('ALTER TABLE chats ADD COLUMN reply_to INTEGER')
        print("Columna 'reply_to' agregada exitosamente.")
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
    """Guarda un mensaje de texto en la base de datos y lo envía en tiempo real."""
    data = request.json
    sender = data.get('sender', 'anonymous')
    message = data.get('message', '')
    reply_to = data.get('replyTo', None)  # Obtener el mensaje al que se está respondiendo
    image_path = None

    # Guardar en la base de datos
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chats (sender, message, image_path, reply_to)
        VALUES (?, ?, ?, ?)
    ''', (sender, message, image_path, reply_to))
    conn.commit()
    conn.close()

    # Obtener el contenido del mensaje al que se está respondiendo
    reply_message = None
    if reply_to:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT message FROM chats WHERE id = ?', (reply_to,))
        reply_message_row = cursor.fetchone()
        conn.close()
        reply_message = reply_message_row[0] if reply_message_row else None

    # Emitir el mensaje a todos los clientes conectados
    socketio.emit('new_message', {
        'sender': sender,
        'message': message,
        'replyTo': reply_message,  # Incluir el contenido del mensaje al que se responde
        'image_path': image_path
    })

    return jsonify({'status': 'success'})

@app.route('/send_image', methods=['POST'])
def send_image():
    """Guarda una imagen y su información en la base de datos."""
    if 'image' not in request.files:
        return jsonify({'status': 'error', 'message': 'No se envió ninguna imagen'})

    file = request.files['image']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'El archivo no tiene nombre'})

    # Generar un nombre único para la imagen
    filename = datetime.now().strftime('%Y%m%d%H%M%S_') + file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Crear la carpeta si no existe
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    file.save(filepath)

    # Guardar en la base de datos solo el nombre del archivo
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chats (sender, message, image_path)
        VALUES (?, ?, ?)
    ''', ('anonymous', None, filename))
    conn.commit()
    conn.close()

    # Emitir el evento de WebSocket con la información de la imagen
    socketio.emit('new_message', {
        'sender': 'anonymous',
        'message': None,
        'image_path': f"/fotos/{filename}",
        'replyTo': None
    })

    return jsonify({'status': 'success', 'image_path': f"/fotos/{filename}"})

@app.route('/get_chats', methods=['GET'])
def get_chats():
    """Obtiene todos los chats de la base de datos."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, sender, message, image_path, reply_to, timestamp FROM chats ORDER BY timestamp ASC')
    chats = cursor.fetchall()
    conn.close()

    chat_list = []
    for chat_id, sender, message, image_path, reply_to, timestamp in chats:
        # Obtener el contenido del mensaje al que se está respondiendo
        reply_message = None
        if reply_to:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT message FROM chats WHERE id = ?', (reply_to,))
            reply_message_row = cursor.fetchone()
            conn.close()
            reply_message = reply_message_row[0] if reply_message_row else None

        chat_list.append({
            'id': chat_id,
            'sender': sender,
            'message': message,
            'image_path': f"/fotos/{image_path}" if image_path else None,
            'replyTo': reply_message,
            'timestamp': timestamp
        })

    return jsonify(chat_list)

@app.route('/fotos/<filename>')
def uploaded_file(filename):
    """Sirve archivos de la carpeta de fotos."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/send_vibrate', methods=['POST'])
def send_vibrate():
    """Emite un evento de vibración a todos los clientes conectados."""
    socketio.emit('vibrate')
    return jsonify({'status': 'success'})

from flask import send_from_directory

@app.route('/fondo.jpg')
def serve_background():
    return send_from_directory('.', 'fondo.jpg')  # Sirve el archivo desde la raíz

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)