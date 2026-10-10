from flask import Flask, request, redirect, session, url_for, Response
import sqlite3
from datetime import datetime
import csv
import io

app = Flask(__name__)
app.secret_key = "beton_zavod_secret_key_2026"
DB = "batch_dosing.db"

# Инициализация БД
def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS company_info (id INTEGER PRIMARY KEY, name TEXT, address TEXT, phone TEXT, tax_number TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS material_labels (id INTEGER PRIMARY KEY, key_name TEXT UNIQUE, display_name TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS operators (id INTEGER PRIMARY KEY, name TEXT, phone TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS drivers (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, license_number TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY, plate_number TEXT, capacity_m3 REAL, driver_id INTEGER, tare_weight_kg REAL DEFAULT 12000.0)')
        conn.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY, name TEXT, contact TEXT, address TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS recipes (id INTEGER PRIMARY KEY, name TEXT, bunker_1 REAL, bunker_2 REAL, bunker_3 REAL, bunker_4 REAL, silo_1 REAL, silo_2 REAL, silo_3 REAL, silo_4 REAL, water REAL, qatki_percent REAL)')
        conn.execute('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, date TEXT, client_id INTEGER, vehicle_id INTEGER, recipe_id INTEGER, volume_m3 REAL, price_per_m3 REAL, operator_id INTEGER, status TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY, material_type TEXT, code_name TEXT, current_kg REAL, max_capacity_kg REAL)')
        
        # Проверка наличия данных
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM company_info")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO company_info (name, address, phone, tax_number) VALUES (?, ?, ?, ?)",
                           ("Beton Zavod LLC", "Baki", "+994558565506", "9900123456"))
            
            cursor.executemany("INSERT INTO operators (name, phone) VALUES (?, ?)", 
                             [("Murad", "+994558565506"), ("Elsen", "+994502223344")])
            cursor.executemany("INSERT INTO drivers (name, phone, license_number) VALUES (?, ?, ?)", 
                             [("Mammad", "+994501112233", "AZ-99-123"), ("Elchin", "+994552223344", "AZ-10-456")])
            cursor.executemany("INSERT INTO vehicles (plate_number, capacity_m3, driver_id, tare_weight_kg) VALUES (?, ?, ?, ?)", 
                             [("10-AA-201", 10.0, 1, 12500.0), ("90-BX-555", 12.0, 2, 13200.0)])
            cursor.executemany("INSERT INTO clients (name, contact, address) VALUES (?, ?, ?)", 
                             [("Client 1", "+994125554433", "Baki"), ("Client 2", "+994124443322", "Xirdalan")])
            
            stock_data = [('AGGREGATE', 'bunker_1', 85000.0, 100000.0), ('AGGREGATE', 'bunker_2', 72000.0, 100000.0),
                          ('AGGREGATE', 'bunker_3', 94000.0, 120000.0), ('AGGREGATE', 'bunker_4', 88000.0, 120000.0),
                          ('CEMENT', 'silo_1', 45000.0, 60000.0), ('CEMENT', 'silo_2', 32000.0, 60000.0),
                          ('CEMENT', 'silo_3', 15000.0, 40000.0), ('CEMENT', 'silo_4', 20000.0, 50000.0),
                          ('WATER', 'water', 50000.0, 50000.0), ('ADDITIVE', 'additive', 5000.0, 10000.0)]
            cursor.executemany("INSERT INTO stock (material_type, code_name, current_kg, max_capacity_kg) VALUES (?, ?, ?, ?)", stock_data)
            
            cursor.executemany("INSERT INTO recipes (name, bunker_1, bunker_2, bunker_3, bunker_4, silo_1, silo_2, silo_3, silo_4, water, qatki_percent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [("M-200", 450, 320, 210, 160, 200, 50, 0, 0, 180, 1.0),
                 ("M-300", 450, 350, 250, 150, 300, 100, 0, 0, 165, 2.0)])
            conn.commit()

try:
    init_db()
except Exception as e:
    print(f"DB Error: {e}")

TRANSLATIONS = {
    "az": {"title": "Beton Zavod", "home": "Əsas səhifə", "orders": "Sifarişlər", "recipes": "Reseptlər", 
           "stock": "Anbar", "reports": "Hesabatlar", "scada": "SCADA", "client": "Müştəri", 
           "mixer": "Mikser", "recipe": "Resept", "volume": "Həcm (m³)", "operator": "Operator",
           "confirm_order": "Təsdiq Et", "add": "Əlavə et", "delete": "Sil", "save": "Yadda saxla",
           "export_csv": "CSV İxrac", "waybill": "Qaimə", "total_price": "Məbləğ", "lang_name": "AZ"},
    "ru": {"title": "Бетонный Завод", "home": "Главная", "orders": "Заказы", "recipes": "Рецепты",
           "stock": "Склад", "reports": "Отчеты", "scada": "SCADA", "client": "Клиент",
           "mixer": "Миксер", "recipe": "Рецепт", "volume": "Объем (м³)", "operator": "Оператор",
           "confirm_order": "Подтвердить", "add": "Добавить", "delete": "Удалить", "save": "Сохранить",
           "export_csv": "Экспорт CSV", "waybill": "Накладная", "total_price": "Сумма", "lang_name": "RU"}
}

def get_lang():
    if 'lang' not in session:
        session['lang'] = 'ru'
    return session['lang']

@app.route('/set_lang/<lang_code>')
def set_lang(lang_code):
    if lang_code in TRANSLATIONS:
        session['lang'] = lang_code
    return redirect(request.referrer or url_for('index'))

@app.route('/')
def index():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    content = f'''
    <div class="p-5 mb-4 rounded-3 card border-warning shadow">
        <h1 class="text-warning">🏗️ Beton Zavod SCADA</h1>
        <a href="/orders" class="btn btn-warning btn-lg me-2">{t['orders']}</a>
        <a href="/recipes" class="btn btn-info btn-lg me-2">{t['recipes']}</a>
        <a href="/stock" class="btn btn-success btn-lg me-2">{t['stock']}</a>
        <a href="/reports" class="btn btn-primary btn-lg">{t['reports']}</a>
    </div>'''
    return render_html(content, t, lang)

@app.route('/orders', methods=['GET', 'POST'])
def orders():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            try:
                vol = float(request.form.get('volume_m3', 10))
                rec_id = request.form.get('recipe_id', 1)
                
                r = conn.execute("SELECT * FROM recipes WHERE id=?", (rec_id,)).fetchone()
                if r:
                    # Проверка остатков
                    req = {'bunker_1': r[2]*vol, 'bunker_2': r[3]*vol, 'bunker_3': r[4]*vol, 
                           'bunker_4': r[5]*vol, 'silo_1': r[6]*vol, 'silo_2': r[7]*vol,
                           'silo_3': r[8]*vol, 'silo_4': r[9]*vol, 'water': r[10]*vol}
                    cement = (r[6]+r[7]+r[8]+r[9])*vol
                    req['additive'] = cement * (r[11]/100.0)
                    
                    for code, needed in req.items():
                        stock = conn.execute("SELECT current_kg FROM stock WHERE code_name=?", (code,)).fetchone()
                        if stock and stock[0] < needed:
                            return f"Error: Not enough {code}", 400
                    
                    # Списание
                    for code, needed in req.items():
                        conn.execute("UPDATE stock SET current_kg = current_kg - ? WHERE code_name=?", (needed, code))
                
                conn.execute("INSERT INTO orders (date, client_id, vehicle_id, recipe_id, volume_m3, price_per_m3, operator_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (datetime.now().isoformat(), request.form.get('client_id', 1), 
                            request.form.get('vehicle_id', 1), rec_id, vol, 
                            float(request.form.get('price', 110)), request.form.get('operator_id', 1), 'Done'))
                conn.commit()
            except Exception as e:
                return f"Error: {str(e)}", 500
            return redirect('/orders')
        
        orders_list = conn.execute("SELECT * FROM orders ORDER BY date DESC").fetchall()
        clients = conn.execute("SELECT * FROM clients").fetchall()
        vehicles = conn.execute("SELECT * FROM vehicles").fetchall()
        recipes = conn.execute("SELECT * FROM recipes").fetchall()
        operators = conn.execute("SELECT * FROM operators").fetchall()
    
    rows = "".join([f"<tr><td>{o[0]}</td><td>{o[1]}</td><td>{o[6]} m³</td><td>${o[7]*o[6]:.2f}</td></tr>" for o in orders_list])
    
    content = f'''
    <h2 class="text-warning mb-4">{t['orders']}</h2>
    <form method="POST" class="card p-4 mb-4">
        <div class="row">
            <div class="col-md-3"><select name="client_id" class="form-select">{''.join([f'<option value="{c[0]}">{c[1]}</option>' for c in clients])}</select></div>
            <div class="col-md-3"><select name="vehicle_id" class="form-select">{''.join([f'<option value="{v[0]}">{v[1]}</option>' for v in vehicles])}</select></div>
            <div class="col-md-2"><select name="recipe_id" class="form-select">{''.join([f'<option value="{r[0]}">{r[1]}</option>' for r in recipes])}</select></div>
            <div class="col-md-2"><input type="number" name="volume_m3" class="form-control" value="10" step="0.5"></div>
            <div class="col-md-2"><button type="submit" class="btn btn-warning w-100">{t['confirm_order']}</button></div>
        </div>
    </form>
    <table class="table table-striped"><thead><tr><th>ID</th><th>Date</th><th>Volume</th><th>Price</th></tr></thead><tbody>{rows}</tbody></table>'''
    
    return render_html(content, t, lang)

@app.route('/recipes')
def recipes():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        recipes = conn.execute("SELECT * FROM recipes").fetchall()
    
    rows = "".join([f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]+r[3]+r[4]+r[5]} kg</td></tr>" for r in recipes])
    content = f'<h2>{t["recipes"]}</h2><table class="table"><thead><tr><th>ID</th><th>Name</th><th>Total</th></tr></thead><tbody>{rows}</tbody></table>'
    return render_html(content, t, lang)

@app.route('/stock')
def stock():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        stock_list = conn.execute("SELECT * FROM stock").fetchall()
    
    rows = "".join([f"<tr><td>{s[2]}</td><td>{s[3]:.1f} kg</td><td>{s[4]:.1f} kg</td></tr>" for s in stock_list])
    content = f'<h2>{t["stock"]}</h2><table class="table"><thead><tr><th>Material</th><th>Current</th><th>Max</th></tr></thead><tbody>{rows}</tbody></table>'
    return render_html(content, t, lang)

@app.route('/reports')
def reports():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        orders = conn.execute("SELECT * FROM orders").fetchall()
        total_vol = sum(o[6] for o in orders)
        total_amt = sum(o[6]*o[7] for o in orders)
    
    content = f'''
    <h2>{t['reports']}</h2>
    <div class="card p-4">
        <p>Total Volume: <b>{total_vol:.1f} m³</b></p>
        <p>Total Revenue: <b>${total_amt:.2f}</b></p>
        <p>Total Orders: <b>{len(orders)}</b></p>
    </div>'''
    return render_html(content, t, lang)

@app.route('/scada')
def scada():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    content = '<h2>🖥️ SCADA</h2><div class="alert alert-success">System Online</div>'
    return render_html(content, t, lang)

def render_html(content, t, lang):
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{t['title']}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #121619; color: #e9ecef; }}
        .card {{ background-color: #1d232a; border: 1px solid #2f363d; }}
        .table {{ color: #e9ecef; }}
        .table-striped > tbody > tr:nth-of-type(odd) {{ background-color: #181d22; }}
        .form-control, .form-select {{ background-color: #262d35; color: #fff; border: 1px solid #3d4650; }}
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark mb-4">
        <div class="container">
            <a class="navbar-brand" href="/">🏗️ Beton Zavod</a>
            <div>
                <a href="/set_lang/az" class="btn btn-sm btn-outline-light me-2">AZ</a>
                <a href="/set_lang/ru" class="btn btn-sm btn-outline-light">RU</a>
            </div>
        </div>
    </nav>
    <div class="container">{content}</div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
