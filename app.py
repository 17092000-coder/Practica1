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

            flash('Completa la información')
            return redirect(url_for('signup'))

        if clave != repetir:

            flash('Las contraseñas no coinciden')
            return redirect(url_for('signup'))

        existe = base.usuarios.find_one({
            "email": correo
        })

        if existe:

            flash('Correo ya registrado')
            return redirect(url_for('signup'))

        nuevo_usuario = {
            "nombre": usuario,
            "email": correo,
            "password": clave,
            "fecha_registro": datetime.now()
        }

        base.usuarios.insert_one(nuevo_usuario)

        flash('Cuenta creada')

        return redirect(url_for('home'))

    return render_template('registro.html')


@app.route('/login', methods=['POST'])
def login():

    correo = request.form.get('email')
    clave = request.form.get('password')

    buscar = base.usuarios.find_one({"email": correo})

    if buscar is None:
        flash('Usuario no encontrado')
        return redirect(url_for('home'))

    if buscar['password'] != clave:
        flash('Contraseña incorrecta')
        return redirect(url_for('home'))

    session['id_user'] = str(buscar['_id'])
    session['usuario'] = buscar.get('nombre', 'Usuario')

    flash('Bienvenido')

    return redirect(url_for('panel'))




@app.route('/panel', methods=['GET', 'POST'])
def panel():
    if 'id_user' not in session:
        return redirect(url_for('home'))

    usuario = session['id_user']
    

    lista_pendientes = base.obtener_tareas_usuario(usuario, 'pendiente')
    lista_en_progreso = base.obtener_tareas_usuario(usuario, 'en_progreso')
    

    tareas_activas = lista_pendientes + lista_en_progreso

    lista_completadas = base.obtener_tareas_usuario(usuario, 'completada')
    lista_canceladas = base.obtener_tareas_usuario(usuario, 'cancelada')

    return render_template(
        'panel.html',
        pendientes=tareas_activas,
        completadas=lista_completadas,
        canceladas=lista_canceladas,
        usuario=session['usuario']
    )


@app.route('/cambiar_estado/<id>', methods=['POST'])
def cambiar_estado(id):

    if 'id_user' not in session:
        return redirect(url_for('home'))

    nuevo_estado = request.form.get('estado')

    print("ID:", id)
    print("Estado:", nuevo_estado)

    resultado = base.tareas.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estado": nuevo_estado}}
    )

    print("Matched:", resultado.matched_count)
    print("Modified:", resultado.modified_count)

    flash('Estado actualizado')

    return redirect(url_for('panel'))



@app.route('/borrar_tarea/<id>', methods=['POST'])
def borrar_tarea(id):

    if 'id_user' in session:

        resultado = base.tareas.delete_one({"_id": ObjectId(id)})

        if resultado.deleted_count == 0:
            flash('No se encontró la tarea')
        else:
            flash('Actividad eliminada')

    return redirect(url_for('panel'))


@app.route('/cancelar/<id>', methods=['POST'])
def cancel(id):

    if 'id_user' not in session:
        return redirect(url_for('home'))

    motivo = request.form.get('motivo')

    base.tareas.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "estado": "cancelada",
                "motivo": motivo
            }
        }
    )

    flash('Actividad cancelada')

    return redirect(url_for('panel'))

@app.route('/editar/<id>', methods=['GET', 'POST'])
def editar(id):
    if 'id_user' not in session:
        return redirect(url_for('home'))

    try:
        tarea_actual = base.tareas.find_one({"_id": ObjectId(id)})
    except Exception as e:
        flash('ID de tarea inválido')
        return redirect(url_for('panel'))

    if not tarea_actual:
        flash('Tarea no encontrada')
        return redirect(url_for('panel'))

    if request.method == 'POST':
        nuevo_titulo = request.form.get('titulo')
        nueva_descripcion = request.form.get('descripcion')

        base.tareas.update_one(
            {"_id": ObjectId(id)}, 
            {
                "$set": {
                    "titulo": nuevo_titulo,
                    "descripcion": nueva_descripcion,
                    "fecha_actualizacion": datetime.now()
                }
            }
        )
        flash('Actividad actualizada correctamente')
        return redirect(url_for('panel'))

    return render_template('editar.html', tarea=tarea_actual)

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión finalizada')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)