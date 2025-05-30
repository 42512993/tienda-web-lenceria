
from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'

DB_PATH = "stock.db"

def inicializar_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock (
            codigo TEXT PRIMARY KEY,
            descripcion TEXT,
            valor REAL,
            cantidad INTEGER
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM stock")
    if cursor.fetchone()[0] == 0:
        productos = [
            ("101", "Corpiño Triángulo", 3500, 10),
            ("102", "Bombacha Colaless", 2200, 15),
            ("103", "Conjunto de encaje", 6900, 8)
        ]
        cursor.executemany("INSERT INTO stock VALUES (?, ?, ?, ?)", productos)
        conn.commit()
    conn.close()

def obtener_productos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT codigo, descripcion, valor, cantidad FROM stock WHERE cantidad > 0")
    productos = cursor.fetchall()
    conn.close()
    return productos

def descontar_stock(codigo, cantidad):
    print(f"Intentando descontar {cantidad} unidades del producto {codigo}")
    try:
        cantidad = int(cantidad)
    except ValueError:
        print(f"❌ Error: cantidad inválida para {codigo}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT cantidad FROM stock WHERE codigo = ?", (codigo,))
    actual = cursor.fetchone()
    if actual:
        print(f"Stock actual de {codigo}: {actual[0]}")
        if actual[0] >= cantidad:
            cursor.execute("UPDATE stock SET cantidad = cantidad - ? WHERE codigo = ?", (cantidad, codigo))
            conn.commit()
            print(f"✅ Descontado correctamente")
        else:
            print(f"⚠️ No hay suficiente stock para {codigo}")
    else:
        print(f"❌ Producto {codigo} no encontrado")
    conn.close()

@app.route('/')
def home():
    productos = obtener_productos()
    return render_template("home.html", productos=productos)

@app.route('/agregar', methods=['POST'])
def agregar():
    codigo = request.form['codigo']
    descripcion = request.form['descripcion']
    cantidad = int(request.form['cantidad'])
    valor = float(request.form['valor'])

    item = {'codigo': codigo, 'descripcion': descripcion, 'cantidad': cantidad, 'valor': valor}

    if 'carrito' not in session:
        session['carrito'] = []
    session['carrito'].append(item)

    return redirect('/carrito')

@app.route('/carrito')
def carrito():
    carrito = session.get('carrito', [])
    total = sum(item['cantidad'] * item['valor'] for item in carrito)
    return render_template("carrito.html", carrito=carrito, total=total)

@app.route('/confirmar', methods=['POST'])
def confirmar():
    carrito = session.get('carrito', [])
    print("🛒 Confirmando compra con los siguientes productos:")
    for item in carrito:
        print(item)
        descontar_stock(item['codigo'], item['cantidad'])
    session.pop('carrito', None)
    return redirect('/confirmado')

@app.route('/confirmado')
def confirmado():
    return render_template("confirmado.html")

@app.route('/admin')
def admin():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stock")
    stock = cursor.fetchall()
    conn.close()
    return render_template("admin.html", stock=stock)

@app.route('/actualizar_stock', methods=['POST'])
def actualizar_stock():
    codigo = request.form['codigo']
    descripcion = request.form['descripcion']
    valor = float(request.form['valor'])
    cantidad = int(request.form['cantidad'])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE stock SET descripcion = ?, valor = ?, cantidad = ? WHERE codigo = ?",
                   (descripcion, valor, cantidad, codigo))
    conn.commit()
    conn.close()
    return redirect('/admin')

if __name__ == '__main__':
    inicializar_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
