from flask import Flask, render_template, request, redirect, url_for, session, flash
from GestorTareas import GestorTareas

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

gestor = GestorTareas()


@app.route('/')
def inicio():
    if 'usuario_id' not in session:
        return render_template('login.html')
    return redirect(url_for('panel'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():

    if request.method == 'POST':

        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        confirmar = request.form['confirm_password']

        if nombre == "" or email == "" or password == "":
            flash("Llena todos los campos")
            return redirect(url_for('registro'))

        if password != confirmar:
            flash("Las contraseñas no coinciden")
            return redirect(url_for('registro'))

       
        usuario_id = gestor.crear_usuario(nombre, email, password)

        if not usuario_id:
            flash("Ese correo ya existe")
            return redirect(url_for('registro'))

        flash("Usuario registrado")
        return redirect(url_for('inicio'))

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

    return render_template('panel.html', nombre=session['nombre'])

@app.route('/salir')
def salir():
    session.clear()
    return redirect(url_for('inicio'))


if __name__ == "__main__":
    app.run(debug=True)