from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "SNEAKERPOINT2024"  # Cambiar por seguridad

# ================================
# 🔵 BASE DE DATOS (Railway / Render)
# ================================
DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print("❌ ERROR DE CONEXIÓN A LA BASE DE DATOS:", e)
        return None


# ============================
# 🌐 RUTA PRINCIPAL (HOME)
# ============================
@app.route("/")
def index():
    conn = get_conn()
    if conn is None:
        return "❌ No se pudo conectar a la base de datos"

    cur = conn.cursor()

    cur.execute("""
        SELECT id_producto, nombre, marca, talla, color, precio, descripcion, stock 
        FROM productos
    """)
    datos = cur.fetchall()

    productos = []
    for p in datos:
        productos.append({
            "id_producto": p[0],
            "nombre": p[1],
            "marca": p[2],
            "talla": p[3],
            "color": p[4],
            "precio": p[5],
            "descripcion": p[6],
            "stock": p[7]
        })

    cur.close()
    conn.close()

    return render_template("index.html", productos=productos)


# ============================
# 🟦 REGISTRO
# ============================
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        telefono = request.form["telefono"]
        correo = request.form["correo"]
        contraseña = request.form["contraseña"]

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO usuarios(nombre, apellido, telefono, correo, password)
            VALUES (%s, %s, %s, %s, %s)
        """, (nombre, apellido, telefono, correo, contraseña))

        conn.commit()
        cur.close()
        conn.close()

        flash("Registro exitoso. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("login"))

    return render_template("registro.html")


# ============================
# 🟩 LOGIN
# ============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        contraseña = request.form["contraseña"]

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT id_usuario, nombre 
            FROM usuarios 
            WHERE correo=%s AND password=%s
        """, (correo, contraseña))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session["loggedin"] = True
            session["id_usuario"] = user[0]
            session["nombre_cliente"] = user[1]

            return redirect(url_for("index"))
        else:
            flash("Correo o contraseña incorrectos", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


# ============================
# 🔴 LOGOUT
# ============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ============================
# 🛒 CARRITO
# ============================
@app.route("/carrito")
def carrito():
    cart = session.get("cart", [])
    total = sum(item["subtotal"] for item in cart)
    return render_template("carrito.html", items=cart, total=total)


@app.route("/add_cart", methods=["POST"])
def add_cart():
    idp = request.form["id_producto"]

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT id_producto, nombre, precio 
        FROM productos 
        WHERE id_producto=%s
    """, (idp,))

    prod = cur.fetchone()

    cur.close()
    conn.close()

    if not prod:
        flash("Producto no encontrado", "danger")
        return redirect(url_for("index"))

    item = {
        "producto": {
            "id_producto": prod[0],
            "nombre": prod[1],
            "precio": prod[2]
        },
        "cantidad": 1,
        "subtotal": float(prod[2])
    }

    cart = session.get("cart", [])
    cart.append(item)
    session["cart"] = cart

    flash("Producto agregado al carrito", "success")
    return redirect(url_for("index"))


@app.route("/eliminar/<idp>")
def eliminar(idp):
    cart = session.get("cart", [])
    cart = [item for item in cart if str(item["producto"]["id_producto"]) != idp]
    session["cart"] = cart
    return redirect(url_for("carrito"))


# ============================
# 🟡 COMPRAR
# ============================
@app.route("/comprar", methods=["GET", "POST"])
def comprar():
    if request.method == "POST":
        session["cart"] = []
        flash("Compra realizada con éxito 🎉", "success")
        return redirect(url_for("index"))

    return render_template("comprar.html")


# ============================
# 🔧 RUN (Render)
# ============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 3000)))
