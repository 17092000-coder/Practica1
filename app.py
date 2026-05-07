from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from bson import ObjectId
from GestorTareas import GestorTareas

app = Flask(__name__)
app.secret_key = "sistema123"

base = GestorTareas()

@app.route('/')
def home():
    if 'id_user' in session:
        return redirect(url_for('panel'))
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        usuario = request.form.get('nombre')
        correo = request.form.get('email')
        clave = request.form.get('password')
        repetir = request.form.get('confirm_password')

        if not usuario or not correo or not clave:
            flash('Completa toda la información')
            return redirect(url_for('signup'))

        if clave != repetir:
            flash('Las contraseñas no coinciden')
            return redirect(url_for('signup'))

        if base.usuarios.find_one({"email": correo}):
            flash('Este correo ya está registrado')
            return redirect(url_for('signup'))

        base.usuarios.insert_one({
            "nombre": usuario,
            "email": correo,
            "password": clave,
            "fecha_registro": datetime.now()
        })
        flash('Cuenta creada exitosamente')
        return redirect(url_for('home'))
    return render_template('registro.html')

@app.route('/login', methods=['POST'])
def login():
    correo = request.form.get('email')
    clave = request.form.get('password')
    user = base.usuarios.find_one({"email": correo, "password": clave})

    if not user:
        flash('Correo o contraseña incorrectos')
        return redirect(url_for('home'))

    session['id_user'] = str(user['_id'])
    session['usuario'] = user.get('nombre', 'Usuario')
    flash(f'Bienvenido {session["usuario"]}')
    return redirect(url_for('panel'))

@app.route('/panel', methods=['GET', 'POST'])
def panel():
    if 'id_user' not in session:
        return redirect(url_for('home'))

    uid = session['id_user']

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        desc = request.form.get('descripcion')
        fecha_limite = request.form.get('fecha_limite')
        
        f_dt = None
        if fecha_limite:
            try:
                f_dt = datetime.strptime(fecha_limite, '%Y-%m-%d')
            except:
                f_dt = None

        base.crear_tarea(uid, titulo, desc, f_dt)
        flash('Tarea agregada')
        return redirect(url_for('panel'))

    
    activas = base.obtener_tareas_usuario(uid, 'pendiente') + \
              base.obtener_tareas_usuario(uid, 'en_progreso')
    
    completadas = base.obtener_tareas_usuario(uid, 'completada')
    canceladas = base.obtener_tareas_usuario(uid, 'cancelada')

    return render_template('panel.html', 
                           pendientes=activas, 
                           completadas=completadas, 
                           canceladas=canceladas, 
                           usuario=session['usuario'])

@app.route('/cambiar_estado/<id>', methods=['POST'])
def cambiar_estado(id):
    if 'id_user' not in session: return redirect(url_for('home'))
    
    nuevo_estado = request.form.get('estado')
    base.tareas.update_one({"_id": ObjectId(id)}, {"$set": {"estado": nuevo_estado}})
    flash('Estado actualizado')
    return redirect(url_for('panel'))

@app.route('/editar/<id>', methods=['GET', 'POST'])
def editar(id):
    if 'id_user' not in session: return redirect(url_for('home'))
    
    tarea = base.tareas.find_one({"_id": ObjectId(id)})
    if not tarea:
        flash('Tarea no encontrada')
        return redirect(url_for('panel'))

    if request.method == 'POST':
        nuevo_titulo = request.form.get('titulo')
        nueva_desc = request.form.get('descripcion')
        base.tareas.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"titulo": nuevo_titulo, "descripcion": nueva_desc}}
        )
        flash('Tarea actualizada')
        return redirect(url_for('panel'))
    
    return render_template('editar.html', tarea=tarea)

@app.route('/cancelar/<id>', methods=['POST'])
def cancelar(id):
    if 'id_user' not in session: return redirect(url_for('home'))
    motivo = request.form.get('motivo')
    base.tareas.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estado": "cancelada", "motivo": motivo}}
    )
    flash('Tarea cancelada')
    return redirect(url_for('panel'))

@app.route('/borrar_tarea/<id>', methods=['POST'])
def borrar(id):
    if 'id_user' not in session: return redirect(url_for('home'))
    base.tareas.delete_one({"_id": ObjectId(id)})
    flash('Tarea eliminada')
    return redirect(url_for('panel'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)