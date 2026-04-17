from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from flask import Flask, render_template, url_for, request, redirect, session

app = Flask(__name__)
app.secret_key = "41234567654321"


class GestorTareas:
    def __init__(self, uri: str = 'mongodb://localhost:27017/'):
        try:
            self.cliente = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.db = self.cliente['gestor_tareas']
            self.tareas = self.db['tareas']
            self.usuarios = self.db['usuarios']
            self._crear_indices()
            print("✅ Conectado a MongoDB")
        except ConnectionFailure:
            print("❌ Error conexión MongoDB")
            raise

    def _crear_indices(self):
        self.usuarios.create_index("email", unique=True)
        self.tareas.create_index([("usuario_id", 1), ("fecha_creacion", -1)])
        self.tareas.create_index("estado")

    def crear_usuario(self, nombre: str, email: str, password: str) -> Optional[str]:
        try:
            res = self.usuarios.insert_one({
                "nombre": nombre,
                "email": email,
                "password": password,
                "fecha_registro": datetime.now(),
                "activo": True
            })
            return str(res.inserted_id)
        except DuplicateKeyError:
            return None

    def obtener_usuario(self, usuario_id: str) -> Optional[Dict]:
        try:
            user = self.usuarios.find_one({"_id": ObjectId(usuario_id)})
            if user:
                user['_id'] = str(user['_id'])
            return user
        except:
            return None

    def crear_tarea(self, usuario_id: str, titulo: str, descripcion: str = ""):
        tarea = {
            "usuario_id": ObjectId(usuario_id),
            "titulo": titulo,
            "descripcion": descripcion,
            "estado": "pendiente",
            "fecha_creacion": datetime.now()
        }
        self.tareas.insert_one(tarea)

    def obtener_tareas_usuario(self, usuario_id: str) -> List[Dict]:
        tareas = self.tareas.find({"usuario_id": ObjectId(usuario_id)}).sort("fecha_creacion", -1)
        resultado = []
        for t in tareas:
            t['_id'] = str(t['_id'])
            t['usuario_id'] = str(t['usuario_id'])
            resultado.append(t)
        return resultado

    def actualizar_estado_tarea(self, tarea_id: str, estado: str):
        self.tareas.update_one(
            {"_id": ObjectId(tarea_id)},
            {"$set": {"estado": estado}}
        )

    def eliminar_tarea(self, tarea_id: str):
        self.tareas.delete_one({"_id": ObjectId(tarea_id)})



gestor = GestorTareas()



@app.route('/')
def inicio():
    if 'usuario_id' not in session:
        return render_template('login.html')
    return redirect(url_for('panel'))


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if password != confirm:
            return render_template('registro.html', error="Las contraseñas no coinciden")

        usuario_id = gestor.crear_usuario(nombre, email, password)

        if not usuario_id:
            return render_template('registro.html', error="Correo ya registrado")

        session['usuario_id'] = usuario_id
        session['nombre'] = nombre

        return redirect(url_for('panel'))

    return render_template('registro.html')


@app.route('/acceso', methods=['POST'])
def acceso():
    email = request.form.get('email')
    password = request.form.get('password')

    usuario = gestor.usuarios.find_one({"email": email})

    if usuario and usuario['password'] == password:
        session['usuario_id'] = str(usuario['_id'])
        session['nombre'] = usuario['nombre']
        return redirect(url_for('panel'))

    return render_template('login.html', error="Credenciales incorrectas")


@app.route('/panel')
def panel():
    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))

    tareas = gestor.obtener_tareas_usuario(session['usuario_id'])
    return render_template('panel.html', tareas=tareas)


@app.route('/nueva_tarea', methods=['GET', 'POST'])
def nueva_tarea():

    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))

    if request.method == 'POST':
        gestor.crear_tarea(
            session['usuario_id'],
            request.form['titulo'],
            request.form['descripcion']
        )
        return redirect(url_for('panel'))

    return render_template('nueva_tarea.html')

@app.route('/cambiar_estado/<tarea_id>', methods=['POST'])
def cambiar_estado(tarea_id):
    gestor.actualizar_estado_tarea(
        tarea_id,
        request.form['estado']
    )
    return redirect(url_for('panel'))


@app.route('/borrar_tarea/<tarea_id>', methods=['POST'])
def borrar_tarea(tarea_id):
    gestor.eliminar_tarea(tarea_id)
    return redirect(url_for('panel'))


@app.route('/salir')
def salir():
    session.clear()
    return redirect(url_for('inicio'))



if __name__ == "__main__":
    app.run(debug=True)