from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
app = Flask(__name__)
CORS(app)  # Esto habilitará CORS para todas las rutas

class Contacto:
    #----------------------------------------------------------------
    # Constructor de la clase
    def __init__(self, host, user, password, database):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        self.cursor = self.conn.cursor()
        # Intentamos seleccionar la base de datos
        try:
            self.cursor.execute(f"USE {database}")
        except mysql.connector.Error as err:
            # Si la base de datos no existe, la creamos
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.cursor.execute(f"CREATE DATABASE {database}")
                self.conn.database = database
            else:
                raise err

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS comentarios (
            nombre VARCHAR(20) NOT NULL,
            apellido VARCHAR(20) NOT NULL,
            email VARCHAR(30) NOT NULL,
            origen VARCHAR(20) NOT NULL,
            paquete VARCHAR(10) NOT NULL,
            comentario VARCHAR(200) NOT NULL)''')
        self.conn.commit()
        
        # Cerrar el cursor inicial y abrir uno nuevo con el parámetro dictionary=True
        self.cursor.close()
        self.cursor = self.conn.cursor(dictionary=True)

    def listar_comentario(self):
        self.cursor.execute("SELECT * FROM comentarios")
        comentarios = self.cursor.fetchall()
        return comentarios
    
    def consultar_comentario(self, email):
        # Consultamos un producto a partir de su código
        self.cursor.execute(f"SELECT * FROM comentarios WHERE email = {email}")
        return self.cursor.fetchone()

    def mostrar_comentario(self, email):
        # Mostramos los datos de un producto a partir de su código
        comentario = self.consultar_comentario(email)
        if comentario:
            print("-" * 40)
            print(f"Nombre.....: {comentario['nombre']}")
            print(f"Apellido: {comentario['apellido']}")
            print(f"Email...: {comentario['email']}")
            print(f"Origen.....: {comentario['origen']}")
            print(f"Paquete.....: {comentario['paquete']}")
            print(f"Comentario..: {comentario['comentario']}")
            print("-" * 40)
        else:
            print("Comentario no encontrado.")

    def agregar_comentario(self, nombre, apellido, email, origen, paquete, comentario):
        sql = "INSERT INTO comentarios (nombre, apellido, email, origen, paquete, comentario) VALUES (%s, %s, %s, %s, %s,%s)"
        valores = (nombre, apellido, email, origen, paquete, comentario)

        self.cursor.execute(sql,valores)
        self.conn.commit()
        return self.cursor.lastrowid

    def modificar_comentario(self, email, nuevo_nombre, nuevo_apellido, nuevo_email, nuevo_origen, nuevo_paquete, nuevo_comentario):
        sql = "UPDATE comentarios SET nombre = %s, apellido = %s, email = %s, origen = %s, paquete = %s, comentario = %s WHERE email = %s"
        valores = (nuevo_nombre, nuevo_apellido, nuevo_email, nuevo_origen, nuevo_paquete, nuevo_comentario, email)
        self.cursor.execute(sql, valores)
        self.conn.commit()
        return self.cursor.rowcount > 0

    def eliminar_comentario(self, email):
        # Eliminamos un producto de la tabla a partir de su código
        self.cursor.execute(f"DELETE FROM comentarios WHERE email = {email}")
        self.conn.commit()
        return self.cursor.rowcount > 0

#--------------------------------------------------------------------
# Cuerpo del programa
#--------------------------------------------------------------------
# Crear una instancia de la clase Catalogo
contacto = Contacto(host='rodamrtnz.mysql.pythonanywhere-services.com', user='rodamrtnz', password='TIF12345', database='rodamrtnz$miapp')

@app.route("/comentarios", methods=["GET"])
def listar_comentarios():
    comentarios = contacto.listar_comentario()
    return jsonify(comentarios)

@app.route("/comentarios/<string:email>", methods=["GET"])
def mostrar_comentario(email):
    comentario = contacto.consultar_comentario(email)
    if comentario:
        return jsonify(comentario)
    else:
        return "Comentarios no encontrado", 404

@app.route("/comentarios", methods=["POST"])
def agregar_comentario():
    #Recojo los datos del form
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    email = request.form['email']
    origen = request.files['origen']
    paquete = request.form['paquete']  
    comentario = request.form['comentario']

    nuevo_comentario = contacto.agregar_comentario(nombre, apellido, email, origen, paquete, comentario)
    if nuevo_comentario:    
        return jsonify({"mensaje": "Comentario agregado correctamente.", "email": nuevo_comentario}), 201
    else:
        return jsonify({"mensaje": "Error al agregar el comentario."}), 500

@app.route("/comentarios/<string:email>", methods=["PUT"])
def modificar_comentario(email):
    #Se recuperan los nuevos datos del formulario
    nueva_nombre = request.form.get("nombre")
    nueva_apellido = request.form.get("apellido")
    nuevo_email = request.form.get("email")
    nuevo_origen = request.form.get("origen")
    nuevo_paquete = request.form.get("paquete")
    nuevo_comentario = request.form.get("comentario")

   # Se llama al método modificar_producto pasando el codigo del producto y los nuevos datos.
    if contacto.modificar_comentario(email, nueva_nombre, nueva_apellido, nuevo_email, nuevo_origen, nuevo_paquete, nuevo_comentario):
        return jsonify({"mensaje": "Comentario modificado"}), 200
    else:
        return jsonify({"mensaje": "Comentario no encontrado"}), 403

@app.route("/comentarios/<string:email>", methods=["DELETE"])
def eliminar_comentario(email):
    # Primero, obtiene la información del producto para encontrar la imagen
    comentario = contacto.consultar_comentario(email)
    if comentario:

        # Luego, elimina el producto del catálogo
        if contacto.eliminar_comentario(email):
            return jsonify({"mensaje": "Comentario eliminado"}), 200
        else:
            return jsonify({"mensaje": "Error al eliminar el comentario"}), 500
    else:
        return jsonify({"mensaje": "Comentario no encontrado"}), 404


if __name__ == "__main__":
    app.run(debug=True)