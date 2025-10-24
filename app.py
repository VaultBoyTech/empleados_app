from flask import Flask, render_template, request, redirect, url_for
import sqlite3, uuid, qrcode, os

app = Flask(__name__)

# === Configuración ===
DB = "empleados.db"
QR_FOLDER = "static/qrs"
BASE_URL = "https://tu-dominio.com"  # <-- cambia por tu dominio real

os.makedirs(QR_FOLDER, exist_ok=True)


# === Inicializar BD ===
def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS empleados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                dni TEXT,
                activo INTEGER DEFAULT 1,
                token TEXT UNIQUE
            )
        """)
init_db()


# === Funciones auxiliares ===
def generar_qr(token):
    url = f"{BASE_URL}/validar/{token}"
    img = qrcode.make(url)
    path = os.path.join(QR_FOLDER, f"{token}.png")
    img.save(path)
    return path


# === Rutas internas (panel de gestión) ===
@app.route("/")
def index():
    conn = sqlite3.connect(DB)
    empleados = conn.execute("SELECT * FROM empleados").fetchall()
    conn.close()
    return render_template("index.html", empleados=empleados)


@app.route("/agregar", methods=["POST"])
def agregar():
    nombre = request.form["nombre"]
    dni = request.form["dni"]
    token = str(uuid.uuid4())

    conn = sqlite3.connect(DB)
    conn.execute("INSERT INTO empleados (nombre, dni, activo, token) VALUES (?, ?, 1, ?)",
                 (nombre, dni, token))
    conn.commit()
    conn.close()

    generar_qr(token)
    return redirect(url_for("index"))


@app.route("/cambiar_estado/<int:id>")
def cambiar_estado(id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT activo FROM empleados WHERE id=?", (id,))
    estado = cur.fetchone()[0]
    nuevo_estado = 0 if estado else 1
    cur.execute("UPDATE empleados SET activo=? WHERE id=?", (nuevo_estado, id))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


# === Ruta pública de validación ===
@app.route("/validar/<token>")
def validar(token):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT nombre, activo FROM empleados WHERE token=?", (token,))
    empleado = cur.fetchone()
    conn.close()

    if empleado:
        nombre, activo = empleado
        return render_template("validar.html", nombre=nombre, activo=activo)
    else:
        return render_template("validar.html", nombre=None, activo=None)


if __name__ == "__main__":
    app.run(debug=True)
