from flask import Flask, request, redirect, session, url_for, Response, flash, send_file
import sqlite3
from datetime import datetime, timedelta
import csv
import io
import os
import qrcode
import base64

app = Flask(__name__)
app.secret_key = "beton_zavod_secret_key_2026"
DB = "batch_dosing.db"

# ==================== ИНИЦИАЛИЗАЦИЯ БД ====================
def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS company_info (id INTEGER PRIMARY KEY, name TEXT, address TEXT, phone TEXT, tax_number TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS material_labels (id INTEGER PRIMARY KEY, key_name TEXT UNIQUE, display_name TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS operators (id INTEGER PRIMARY KEY, name TEXT, phone TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS drivers (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, license_number TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY, plate_number TEXT, capacity_m3 REAL, driver_id INTEGER, tare_weight_kg REAL DEFAULT 12000.0)')
        conn.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY, name TEXT, contact TEXT, address TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY, name TEXT, contact TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS recipes (id INTEGER PRIMARY KEY, name TEXT, bunker_1 REAL, bunker_2 REAL, bunker_3 REAL, bunker_4 REAL, silo_1 REAL, silo_2 REAL, silo_3 REAL, silo_4 REAL, water REAL, qatki_percent REAL)')
        conn.execute('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, date TEXT, client_id INTEGER, vehicle_id INTEGER, recipe_id INTEGER, volume_m3 REAL, price_per_m3 REAL, operator_id INTEGER, status TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY, material_type TEXT, code_name TEXT, current_kg REAL, max_capacity_kg REAL)')
        conn.execute('CREATE TABLE IF NOT EXISTS stock_movements (id INTEGER PRIMARY KEY, date TEXT, material_code TEXT, movement_type TEXT, quantity_kg REAL, order_id INTEGER, description TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS modbus_settings (id INTEGER PRIMARY KEY, plc_ip TEXT, plc_port INTEGER, slave_id INTEGER)')
        conn.execute('CREATE TABLE IF NOT EXISTS modbus_registers (id INTEGER PRIMARY KEY, tag_name TEXT UNIQUE, data_type TEXT, address INTEGER, description TEXT)')
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM company_info")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO company_info (name, address, phone, tax_number) VALUES (?, ?, ?, ?)",
                           ("Beton Zavod LLC", "Baki, Azerbaijan", "+994558565506", "9900123456"))
            
            defaults = [('bunker_1', 'Щебень 5-20'), ('bunker_2', 'Щебень 20-40'), ('bunker_3', 'Песок'), 
                        ('bunker_4', 'Песок намывной'), ('silo_1', 'Цемент CEM I 42.5'), ('silo_2', 'Цемент CEM II 32.5'),
                        ('silo_3', 'Зола'), ('silo_4', 'Микрокремнезем'), ('water', 'Вода'), ('additive', 'Пластификатор')]
            cursor.executemany("INSERT OR IGNORE INTO material_labels (key_name, display_name) VALUES (?, ?)", defaults)
            
            cursor.executemany("INSERT INTO operators (name, phone) VALUES (?, ?)", 
                             [("Murad Ibrahimov", "+994558565506"), ("Elsen M", "+994502223344")])
            cursor.executemany("INSERT INTO drivers (name, phone, license_number) VALUES (?, ?, ?)", 
                             [("Mammad M", "+994501112233", "AZ-99-123"), ("Elchin Q", "+994552223344", "AZ-10-456")])
            cursor.executemany("INSERT INTO vehicles (plate_number, capacity_m3, driver_id, tare_weight_kg) VALUES (?, ?, ?, ?)", 
                             [("10-AA-201", 10.0, 1, 12500.0), ("90-BX-555", 12.0, 2, 13200.0)])
            cursor.executemany("INSERT INTO clients (name, contact, address) VALUES (?, ?, ?)", 
                             [("Aqrar Tikinti MMC", "+994125554433", "Baki"), ("Crystal Absheron", "+994124443322", "Xirdalan")])
            cursor.executemany("INSERT INTO suppliers (name, contact) VALUES (?, ?)", 
                             [("Holcim Azerbaijan", "+994126990000"), ("Norm Sement", "+994124250000")])
            
            stock_data = [('AGGREGATE', 'bunker_1', 85000.0, 100000.0), ('AGGREGATE', 'bunker_2', 72000.0, 100000.0),
                          ('AGGREGATE', 'bunker_3', 94000.0, 120000.0), ('AGGREGATE', 'bunker_4', 88000.0, 120000.0),
                          ('CEMENT', 'silo_1', 45000.0, 60000.0), ('CEMENT', 'silo_2', 32000.0, 60000.0),
                          ('CEMENT', 'silo_3', 15000.0, 40000.0), ('CEMENT', 'silo_4', 20000.0, 50000.0),
                          ('WATER', 'water', 50000.0, 50000.0), ('ADDITIVE', 'additive', 5000.0, 10000.0)]
            cursor.executemany("INSERT INTO stock (material_type, code_name, current_kg, max_capacity_kg) VALUES (?, ?, ?, ?)", stock_data)
            
            cursor.executemany("INSERT INTO recipes (name, bunker_1, bunker_2, bunker_3, bunker_4, silo_1, silo_2, silo_3, silo_4, water, qatki_percent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [("M-200 (B15)", 450, 320, 210, 160, 200, 50, 0, 0, 180, 1.0),
                 ("M-300 (B22.5)", 450, 350, 250, 150, 300, 100, 0, 0, 165, 2.0)])
            
            cursor.execute("INSERT INTO modbus_settings (plc_ip, plc_port, slave_id) VALUES ('192.168.1.50', 502, 1)")
            conn.commit()

try:
    init_db()
except Exception as e:
    print(f"DB Error: {e}")

# ==================== МУЛЬТИЯЗЫЧНОСТЬ ====================
TRANSLATIONS = {
    "az": {"title": "Beton Zavod SCADA", "home": "Əsas səhifə", "orders": "Sifarişlər", "recipes": "Reseptlər",
           "stock": "Anbar", "reports": "Hesabatlar", "scada": "SCADA", "settings": "Parametrlər",
           "client": "Müştəri", "mixer": "Mikser", "recipe": "Resept", "volume": "Həcm (m³)",
           "operator": "Operator", "confirm_order": "Təsdiq Et", "add": "Əlavə et", "delete": "Sil",
           "save": "Yadda saxla", "edit": "Redaktə", "export_csv": "CSV İxrac", "waybill": "Qaimə",
           "total_price": "Məbləğ", "lang_name": "AZ", "back": "Geri", "print": "Çap et",
           "stock_report": "Anbar Hesabatı", "concrete_report": "Beton Hesabatı",
           "client_report": "Müştəri Hesabatı", "vehicle_report": "Maşın Hesabatı"},
    "ru": {"title": "Бетонный Завод SCADA", "home": "Главная", "orders": "Заказы", "recipes": "Рецепты",
           "stock": "Склад", "reports": "Отчеты", "scada": "SCADA", "settings": "Настройки",
           "client": "Клиент", "mixer": "Миксер", "recipe": "Рецепт", "volume": "Объем (м³)",
           "operator": "Оператор", "confirm_order": "Подтвердить", "add": "Добавить", "delete": "Удалить",
           "save": "Сохранить", "edit": "Править", "export_csv": "Экспорт CSV", "waybill": "Накладная",
           "total_price": "Сумма", "lang_name": "RU", "back": "Назад", "print": "Печать",
           "stock_report": "Отчет по складу", "concrete_report": "Отчет по бетону",
           "client_report": "Отчет по клиентам", "vehicle_report": "Отчет по машинам"}
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

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def get_labels():
    defaults = {'bunker_1': 'Bunker 1', 'bunker_2': 'Bunker 2', 'bunker_3': 'Bunker 3', 'bunker_4': 'Bunker 4',
                'silo_1': 'Silo 1', 'silo_2': 'Silo 2', 'silo_3': 'Silo 3', 'silo_4': 'Silo 4',
                'water': 'Su', 'additive': 'Qatqı'}
    try:
        with sqlite3.connect(DB) as conn:
            rows = conn.execute("SELECT key_name, display_name FROM material_labels").fetchall()
            for r in rows:
                defaults[r[0]] = r[1]
    except:
        pass
    return defaults

def render_html(content, t, lang):
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{t['title']}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #121619; color: #e9ecef; font-family: 'Segoe UI', sans-serif; }}
        .card {{ background-color: #1d232a; border: 1px solid #2f363d; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
        .table {{ color: #e9ecef; }}
        .table-striped > tbody > tr:nth-of-type(odd) {{ background-color: #181d22; }}
        .form-control, .form-select {{ background-color: #262d35; color: #fff; border: 1px solid #3d4650; }}
        .form-control:focus, .form-select:focus {{ background-color: #262d35; color: #fff; border-color: #ffc107; }}
        label {{ font-size: 0.85rem; font-weight: 600; color: #ffc107; margin-bottom: 4px; }}
        .text-warning {{ color: #ffc107 !important; }}
        .btn-warning {{ background-color: #ffc107; color: #000; font-weight: 600; }}
        .btn-warning:hover {{ background-color: #e0a800; color: #000; }}
        @media print {{
            body {{ background-color: #fff !important; color: #000 !important; }}
            .card {{ background-color: #fff !important; color: #000 !important; border: 1px solid #000 !important; }}
            .table {{ color: #000 !important; }}
            .d-print-none {{ display: none !important; }}
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark mb-4 d-print-none">
        <div class="container-fluid">
            <a class="navbar-brand text-warning fw-bold" href="/">️ Beton Zavod</a>
            <div class="d-flex">
                <a href="/orders" class="btn btn-sm btn-outline-light me-2">{t['orders']}</a>
                <a href="/recipes" class="btn btn-sm btn-outline-light me-2">{t['recipes']}</a>
                <a href="/stock" class="btn btn-sm btn-outline-light me-2">{t['stock']}</a>
                <a href="/reports" class="btn btn-sm btn-outline-light me-2">{t['reports']}</a>
                <a href="/scada" class="btn btn-sm btn-outline-info me-2">{t['scada']}</a>
                <a href="/set_lang/az" class="btn btn-sm btn-outline-warning me-1">AZ</a>
                <a href="/set_lang/ru" class="btn btn-sm btn-outline-warning">RU</a>
            </div>
        </div>
    </nav>
    <div class="container-fluid px-4">
        {content}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

# ==================== ГЛАВНАЯ ====================
@app.route('/')
def index():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    content = f'''
    <div class="p-5 mb-4 rounded-3 card border-warning shadow">
        <h1 class="display-5 fw-bold text-warning">🏗️ Beton Zavod SCADA</h1>
        <p class="fs-5 text-secondary">Система управления бетонным заводом</p>
        <hr class="border-secondary">
        <a href="/orders" class="btn btn-warning btn-lg me-2">{t['orders']}</a>
        <a href="/recipes" class="btn btn-info btn-lg me-2 text-white">{t['recipes']}</a>
        <a href="/stock" class="btn btn-success btn-lg me-2">{t['stock']}</a>
        <a href="/reports" class="btn btn-primary btn-lg">{t['reports']}</a>
    </div>'''
    return render_html(content, t, lang)

# ==================== ЗАКАЗЫ ====================
@app.route('/orders', methods=['GET', 'POST'])
def orders():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            try:
                vol = float(request.form.get('volume_m3', 10))
                rec_id = request.form.get('recipe_id', 1)
                client_id = request.form.get('client_id', 1)
                vehicle_id = request.form.get('vehicle_id', 1)
                operator_id = request.form.get('operator_id', 1)
                price = float(request.form.get('price', 110))
                
                r = conn.execute("SELECT * FROM recipes WHERE id=?", (rec_id,)).fetchone()
                if r:
                    req = {'bunker_1': r[2]*vol, 'bunker_2': r[3]*vol, 'bunker_3': r[4]*vol, 
                           'bunker_4': r[5]*vol, 'silo_1': r[6]*vol, 'silo_2': r[7]*vol,
                           'silo_3': r[8]*vol, 'silo_4': r[9]*vol, 'water': r[10]*vol}
                    cement = (r[6]+r[7]+r[8]+r[9])*vol
                    req['additive'] = cement * (r[11]/100.0)
                    
                    # Проверка остатков
                    for code, needed in req.items():
                        stock = conn.execute("SELECT current_kg FROM stock WHERE code_name=?", (code,)).fetchone()
                        if stock and stock[0] < needed:
                            flash(f"Недостаточно {code}: нужно {needed:.1f} кг, есть {stock[0]:.1f} кг", "error")
                            return redirect('/orders')
                    
                    # Списание и запись движений
                    for code, needed in req.items():
                        conn.execute("UPDATE stock SET current_kg = current_kg - ? WHERE code_name=?", (needed, code))
                        conn.execute("INSERT INTO stock_movements (date, material_code, movement_type, quantity_kg, order_id, description) VALUES (?, ?, ?, ?, ?, ?)",
                                   (datetime.now().isoformat(), code, 'OUT', needed, None, f"Order production {vol}m³"))
                
                conn.execute("INSERT INTO orders (date, client_id, vehicle_id, recipe_id, volume_m3, price_per_m3, operator_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (datetime.now().isoformat(), client_id, vehicle_id, rec_id, vol, price, operator_id, 'Done'))
                conn.commit()
                flash("Заказ успешно создан!", "success")
            except Exception as e:
                flash(f"Ошибка: {str(e)}", "error")
            return redirect('/orders')
        
        orders_list = conn.execute('''
            SELECT o.id, o.date, c.name, v.plate_number, r.name, o.volume_m3, o.price_per_m3, (o.volume_m3 * o.price_per_m3)
            FROM orders o
            LEFT JOIN clients c ON o.client_id = c.id
            LEFT JOIN vehicles v ON o.vehicle_id = v.id
            LEFT JOIN recipes r ON o.recipe_id = r.id
            ORDER BY o.date DESC
        ''').fetchall()
        
        clients = conn.execute("SELECT * FROM clients").fetchall()
        vehicles = conn.execute("SELECT * FROM vehicles").fetchall()
        recipes = conn.execute("SELECT * FROM recipes").fetchall()
        operators = conn.execute("SELECT * FROM operators").fetchall()
    
    rows = "".join([f"""<tr>
        <td>{o[0]}</td><td>{o[1][:16] if o[1] else ''}</td><td>{o[2] or ''}</td><td>{o[3] or ''}</td>
        <td>{o[4] or ''}</td><td>{o[5]} m³</td><td class='text-warning fw-bold'>{o[7]:.2f} AZN</td>
        <td><a href='/orders/waybill/{o[0]}' class='btn btn-info btn-sm' target='_blank'>📄 {t['waybill']}</a></td>
    </tr>""" for o in orders_list])
    
    content = f'''
    <h2 class="text-warning mb-4">{t['orders']}</h2>
    <div class="card p-4 mb-4 border-warning">
        <h5 class="text-warning mb-3">➕ Новый заказ</h5>
        <form method="POST">
            <div class="row g-3">
                <div class="col-md-3"><label>{t['client']}</label><select name="client_id" class="form-select">{''.join([f'<option value="{c[0]}">{c[1]}</option>' for c in clients])}</select></div>
                <div class="col-md-3"><label>{t['mixer']}</label><select name="vehicle_id" class="form-select">{''.join([f'<option value="{v[0]}">{v[1]}</option>' for v in vehicles])}</select></div>
                <div class="col-md-2"><label>{t['recipe']}</label><select name="recipe_id" class="form-select">{''.join([f'<option value="{r[0]}">{r[1]}</option>' for r in recipes])}</select></div>
                <div class="col-md-2"><label>{t['volume']}</label><input type="number" name="volume_m3" class="form-control" value="10" step="0.5" required></div>
                <div class="col-md-2"><label>Цена за м³</label><input type="number" name="price" class="form-control" value="110" step="1" required></div>
                <div class="col-md-12"><button type="submit" class="btn btn-warning w-100 fw-bold">{t['confirm_order']}</button></div>
            </div>
        </form>
    </div>
    <div class="card p-4">
        <table class="table table-striped">
            <thead class="table-dark"><tr><th>ID</th><th>Дата</th><th>Клиент</th><th>Машина</th><th>Рецепт</th><th>Объем</th><th>Сумма</th><th>Действие</th></tr></thead>
            <tbody>{rows if rows else "<tr><td colspan='8' class='text-center'>Нет заказов</td></tr>"}</tbody>
        </table>
    </div>'''
    return render_html(content, t, lang)

# ==================== НАКЛАДНАЯ С QR-КОДОМ ====================
@app.route('/orders/waybill/<int:id>')
def waybill(id):
    lang = get_lang()
    t = TRANSLATIONS[lang]
    
    with sqlite3.connect(DB) as conn:
        o = conn.execute('''
            SELECT o.id, o.date, c.name, c.address, v.plate_number, v.tare_weight_kg, d.name, r.name, o.volume_m3, op.name,
                   r.bunker_1, r.bunker_2, r.bunker_3, r.bunker_4, r.silo_1, r.silo_2, r.silo_3, r.silo_4, r.water, r.qatki_percent
            FROM orders o
            LEFT JOIN clients c ON o.client_id = c.id
            LEFT JOIN vehicles v ON o.vehicle_id = v.id
            LEFT JOIN drivers d ON v.driver_id = d.id
            LEFT JOIN recipes r ON o.recipe_id = r.id
            LEFT JOIN operators op ON o.operator_id = op.id
            WHERE o.id=?
        ''', (id,)).fetchone()
        comp = conn.execute("SELECT * FROM company_info LIMIT 1").fetchone()
    
    if not o:
        return "Документ не найден", 404
    
    vol = o[8]
    cement_total = (o[14]+o[15]+o[16]+o[17]) * vol
    additive_kg = cement_total * (o[19]/100.0)
    c_weight = (o[10]+o[11]+o[12]+o[13] + cement_total + o[18] + additive_kg)
    tare = o[5] if o[5] else 12000.0
    gross = tare + c_weight
    
    # Генерация QR-кода
    qr_data = f"Waybill #{o[0]}|Date:{o[1]}|Client:{o[2]}|Volume:{vol}m³|Weight:{gross:.0f}kg"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    qr_base64 = base64.b64encode(img.tobytes()).decode('utf-8')
    
    html = f"""
    <!DOCTYPE html>
    <html lang="{lang}">
    <head>
        <meta charset="UTF-8">
        <title>Накладная #{o[0]}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background: #e9ecef; font-family: 'Times New Roman', serif; }}
            .a4-page {{ background: #fff; width: 210mm; min-height: 297mm; padding: 15mm; margin: 20px auto; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px; }}
            .header h2 {{ margin: 0; font-size: 18pt; font-weight: bold; text-transform: uppercase; }}
            .header p {{ margin: 2px 0; font-size: 10pt; }}
            .doc-title {{ text-align: center; font-size: 16pt; font-weight: bold; margin: 20px 0; text-decoration: underline; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; font-size: 11pt; }}
            .info-label {{ font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 11pt; }}
            th, td {{ border: 1px solid #000; padding: 8px; text-align: center; }}
            th {{ background-color: #f0f0f0; font-weight: bold; }}
            .signatures {{ margin-top: 40px; display: flex; justify-content: space-between; font-size: 11pt; }}
            .sig-block {{ width: 45%; text-align: center; }}
            .sig-line {{ border-top: 1px solid #000; margin-top: 30px; padding-top: 5px; }}
            .qr-code {{ position: absolute; top: 20mm; right: 20mm; }}
            .no-print {{ text-align: center; margin-bottom: 20px; }}
            @media print {{
                body {{ background: #fff; margin: 0; }}
                .a4-page {{ box-shadow: none; margin: 0; width: 100%; padding: 10mm; }}
                .no-print {{ display: none !important; }}
            }}
        </style>
    </head>
    <body>
        <div class="no-print">
            <button class="btn btn-primary btn-lg" onclick="window.print()">️ Печать</button>
            <a href="/orders" class="btn btn-secondary btn-lg">Назад</a>
        </div>
        <div class="a4-page" style="position: relative;">
            <div class="qr-code">
                <img src="data:image/png;base64,{qr_base64}" alt="QR Code" style="width: 100px; height: 100px;">
            </div>
            <div class="header">
                <h2>{comp[1] if comp else 'Beton Zavod'}</h2>
                <p>{comp[2] if comp else ''} | Tel: {comp[3] if comp else ''} | ИНН: {comp[4] if comp else ''}</p>
            </div>
            
            <div class="doc-title">ТОВАРНО-ТРАНСПОРТНАЯ НАКЛАДНАЯ № {o[0]}</div>
            
            <div class="info-grid">
                <div><span class="info-label">Дата:</span> {o[1][:16] if o[1] else ''}</div>
                <div><span class="info-label">Машина:</span> {o[4] or ''}</div>
                <div><span class="info-label">Клиент:</span> {o[2] or ''}</div>
                <div><span class="info-label">Водитель:</span> {o[6] or ''}</div>
                <div><span class="info-label">Адрес:</span> {o[3] or ''}</div>
                <div><span class="info-label">Оператор:</span> {o[9] or ''}</div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Наименование</th>
                        <th>Объем (м³)</th>
                        <th>Тара (кг)</th>
                        <th>Нетто (кг)</th>
                        <th>Брутто (кг)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="text-align: left;"><b>{o[7] or ''}</b></td>
                        <td><b>{o[8]}</b></td>
                        <td>{tare:,.0f}</td>
                        <td>{c_weight:,.0f}</td>
                        <td><b>{gross:,.0f}</b></td>
                    </tr>
                </tbody>
            </table>

            <div class="signatures">
                <div class="sig-block">
                    <div>Сдал (Оператор):</div>
                    <div class="sig-line">{o[9] or ''}</div>
                </div>
                <div class="sig-block">
                    <div>Принял (Заказчик):</div>
                    <div class="sig-line">{o[2] or ''}</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

# ==================== РЕЦЕПТЫ ====================
@app.route('/recipes', methods=['GET', 'POST'])
def recipes():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    labels = get_labels()
    
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            try:
                conn.execute("""
                    INSERT INTO recipes (name, bunker_1, bunker_2, bunker_3, bunker_4, silo_1, silo_2, silo_3, silo_4, water, qatki_percent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (request.form['name'], float(request.form['b1']), float(request.form['b2']), 
                      float(request.form['b3']), float(request.form['b4']), float(request.form['s1']), 
                      float(request.form['s2']), float(request.form['s3']), float(request.form['s4']), 
                      float(request.form['water']), float(request.form['qatki'])))
                conn.commit()
                flash("Рецепт добавлен!", "success")
            except Exception as e:
                flash(f"Ошибка: {str(e)}", "error")
            return redirect('/recipes')
        
        recipes_list = conn.execute("SELECT * FROM recipes").fetchall()
    
    rows = ""
    for r in recipes_list:
        total_cement = r[6] + r[7] + r[8] + r[9]
        additive_kg = total_cement * (r[11] / 100.0)
        total_weight = r[2] + r[3] + r[4] + r[5] + total_cement + r[10] + additive_kg
        rows += f"""<tr>
            <td>{r[0]}</td><td><b>{r[1]}</b></td>
            <td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td>
            <td>{r[6]}</td><td>{r[7]}</td><td>{r[8]}</td><td>{r[9]}</td>
            <td>{r[10]}</td><td><b>{r[11]}%</b> ({additive_kg:.1f} кг)</td>
            <td class='text-warning fw-bold'>{total_weight:,.1f} кг</td>
            <td><a href='/recipes/delete/{r[0]}' class='btn btn-danger btn-sm' onclick="return confirm('Удалить?')">🗑️</a></td>
        </tr>"""
    
    content = f'''
    <h2 class="text-warning mb-4">{t['recipes']}</h2>
    <div class="card p-4 mb-4 border-warning">
        <h5 class="text-warning mb-3">➕ Добавить рецепт</h5>
        <form method="POST">
            <div class="row g-2">
                <div class="col-md-3"><label>Название</label><input type="text" name="name" class="form-control" placeholder="M-350" required></div>
                <div class="col-md-1"><label>{labels['bunker_1']}</label><input type="number" name="b1" class="form-control" value="450" required></div>
                <div class="col-md-1"><label>{labels['bunker_2']}</label><input type="number" name="b2" class="form-control" value="350" required></div>
                <div class="col-md-1"><label>{labels['bunker_3']}</label><input type="number" name="b3" class="form-control" value="250" required></div>
                <div class="col-md-1"><label>{labels['bunker_4']}</label><input type="number" name="b4" class="form-control" value="150" required></div>
                <div class="col-md-1"><label>{labels['silo_1']}</label><input type="number" name="s1" class="form-control" value="300" required></div>
                <div class="col-md-1"><label>{labels['silo_2']}</label><input type="number" name="s2" class="form-control" value="100" required></div>
                <div class="col-md-1"><label>{labels['silo_3']}</label><input type="number" name="s3" class="form-control" value="0"></div>
                <div class="col-md-1"><label>{labels['silo_4']}</label><input type="number" name="s4" class="form-control" value="0"></div>
                <div class="col-md-1"><label>{labels['water']}</label><input type="number" name="water" class="form-control" value="170" required></div>
                <div class="col-md-1"><label>{labels['additive']} (%)</label><input type="number" step="0.1" name="qatki" class="form-control" value="1.5" required></div>
            </div>
            <button type="submit" class="btn btn-warning w-100 fw-bold mt-3">💾 {t['save']}</button>
        </form>
    </div>
    <div class="card p-4">
        <div class="table-responsive">
            <table class="table table-striped text-center">
                <thead class="table-dark">
                    <tr><th>ID</th><th>Марка</th><th>{labels['bunker_1']}</th><th>{labels['bunker_2']}</th><th>{labels['bunker_3']}</th><th>{labels['bunker_4']}</th>
                    <th>{labels['silo_1']}</th><th>{labels['silo_2']}</th><th>{labels['silo_3']}</th><th>{labels['silo_4']}</th><th>{labels['water']}</th><th>{labels['additive']}</th><th class="text-warning">Всего (кг)</th><th>Действие</th></tr>
                </thead>
                <tbody>{rows if rows else "<tr><td colspan='14' class='text-center'>Нет рецептов</td></tr>"}</tbody>
            </table>
        </div>
    </div>'''
    return render_html(content, t, lang)

@app.route('/recipes/delete/<int:id>')
def delete_recipe(id):
    with sqlite3.connect(DB) as conn:
        conn.execute("DELETE FROM recipes WHERE id=?", (id,))
        conn.commit()
    return redirect('/recipes')

# ==================== СКЛАД (ПОЛНЫЙ CRUD) ====================
@app.route('/stock', methods=['GET', 'POST'])
def stock():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    labels = get_labels()
    
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            action = request.form.get('action')
            try:
                if action == 'add':
                    conn.execute("INSERT INTO stock (material_type, code_name, current_kg, max_capacity_kg) VALUES (?, ?, ?, ?)",
                               (request.form['material_type'], request.form['code_name'], 
                                float(request.form['current_kg']), float(request.form['max_capacity_kg'])))
                    flash("Материал добавлен!", "success")
                elif action == 'update':
                    conn.execute("UPDATE stock SET current_kg=?, max_capacity_kg=? WHERE id=?",
                               (float(request.form['current_kg']), float(request.form['max_capacity_kg']), request.form['stock_id']))
                    flash("Обновлено!", "success")
                elif action == 'delete':
                    conn.execute("DELETE FROM stock WHERE id=?", (request.form['stock_id'],))
                    flash("Удалено!", "success")
                conn.commit()
            except Exception as e:
                flash(f"Ошибка: {str(e)}", "error")
            return redirect('/stock')
        
        stock_list = conn.execute("SELECT * FROM stock").fetchall()
    
    rows = ""
    for s in stock_list:
        pct = min(100, max(0, int((s[3] / s[4]) * 100))) if s[4] > 0 else 0
        color = "bg-success" if pct > 30 else "bg-warning" if pct > 15 else "bg-danger"
        rows += f"""<tr>
            <td>{s[0]}</td><td><span class='badge bg-secondary'>{s[1]}</span></td><td><b>{labels.get(s[2], s[2])}</b></td>
            <td class='text-warning fw-bold'>{s[3]:,.1f} кг</td><td>{s[4]:,.1f} кг</td>
            <td><div class='progress bg-dark' style='height: 20px;'><div class='progress-bar {color}' style='width: {pct}%;'>{pct}%</div></div></td>
            <td>
                <form method='POST' class='d-inline-flex gap-1'>
                    <input type='hidden' name='action' value='update'>
                    <input type='hidden' name='stock_id' value='{s[0]}'>
                    <input type='number' step='100' name='current_kg' class='form-control form-control-sm' value='{s[3]}' style='width: 100px;' required>
                    <input type='number' step='100' name='max_capacity_kg' class='form-control form-control-sm' value='{s[4]}' style='width: 100px;' required>
                    <button type='submit' class='btn btn-warning btn-sm'>💾</button>
                </form>
                <form method='POST' class='d-inline'>
                    <input type='hidden' name='action' value='delete'>
                    <input type='hidden' name='stock_id' value='{s[0]}'>
                    <button type='submit' class='btn btn-danger btn-sm' onclick="return confirm('Удалить?')">🗑️</button>
                </form>
            </td>
        </tr>"""
    
    content = f'''
    <h2 class="text-warning mb-4">{t['stock']}</h2>
    <div class="card p-4 mb-4 border-warning">
        <h5 class="text-warning mb-3">➕ Добавить материал</h5>
        <form method="POST">
            <input type="hidden" name="action" value="add">
            <div class="row g-3">
                <div class="col-md-3"><label>Тип материала</label><select name="material_type" class="form-select">
                    <option value="AGGREGATE">Инертные</option><option value="CEMENT">Цемент</option>
                    <option value="WATER">Вода</option><option value="ADDITIVE">Добавка</option>
                </select></div>
                <div class="col-md-3"><label>Код (bunker_1, silo_1, water, additive)</label><input type="text" name="code_name" class="form-control" required></div>
                <div class="col-md-3"><label>Текущий остаток (кг)</label><input type="number" name="current_kg" class="form-control" value="0" required></div>
                <div class="col-md-3"><label>Макс. вместимость (кг)</label><input type="number" name="max_capacity_kg" class="form-control" value="100000" required></div>
                <div class="col-md-12"><button type="submit" class="btn btn-warning w-100 fw-bold">➕ Добавить</button></div>
            </div>
        </form>
    </div>
    <div class="card p-4">
        <div class="table-responsive">
            <table class="table table-striped">
                <thead class="table-dark"><tr><th>ID</th><th>Тип</th><th>Название</th><th>Остаток</th><th>Макс.</th><th>Заполненность</th><th>Действия</th></tr></thead>
                <tbody>{rows if rows else "<tr><td colspan='7' class='text-center'>Нет материалов</td></tr>"}</tbody>
            </table>
        </div>
    </div>'''
    return render_html(content, t, lang)

# ==================== ОТЧЕТЫ (ОТДЕЛЬНЫЕ СТРАНИЦЫ) ====================
@app.route('/reports')
def reports():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    content = f'''
    <h2 class="text-warning mb-4">{t['reports']}</h2>
    <div class="row g-4">
        <div class="col-md-6">
            <div class="card p-4 border-warning h-100">
                <h4 class="text-warning">📊 Общий отчет</h4>
                <p>Сводная информация по всем заказам, объемам и выручке</p>
                <a href="/reports/summary" class="btn btn-warning w-100">Открыть</a>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card p-4 border-info h-100">
                <h4 class="text-info">🪨 {t['stock_report']}</h4>
                <p>Приход, расход и остатки по всем материалам</p>
                <a href="/reports/stock" class="btn btn-info w-100 text-white">Открыть</a>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card p-4 border-success h-100">
                <h4 class="text-success">🏗️ {t['concrete_report']}</h4>
                <p>Производство по маркам бетона</p>
                <a href="/reports/concrete" class="btn btn-success w-100">Открыть</a>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card p-4 border-primary h-100">
                <h4 class="text-primary">👥 {t['client_report']}</h4>
                <p>Заказы по клиентам</p>
                <a href="/reports/clients" class="btn btn-primary w-100">Открыть</a>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card p-4 border-danger h-100">
                <h4 class="text-danger"> {t['vehicle_report']}</h4>
                <p>Заказы по машинам и водителям</p>
                <a href="/reports/vehicles" class="btn btn-danger w-100">Открыть</a>
            </div>
        </div>
    </div>'''
    return render_html(content, t, lang)

@app.route('/reports/summary')
def report_summary():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        orders = conn.execute("SELECT * FROM orders").fetchall()
        total_vol = sum(o[6] for o in orders)
        total_amt = sum(o[6]*o[7] for o in orders)
    
    rows = "".join([f"<tr><td>{o[0]}</td><td>{o[1][:16] if o[1] else ''}</td><td>{o[6]} m³</td><td class='text-warning fw-bold'>{o[6]*o[7]:.2f} AZN</td></tr>" for o in orders])
    
    content = f'''
    <h2 class="text-warning mb-4">📊 Общий отчет</h2>
    <div class="row mb-4">
        <div class="col-md-4"><div class="card p-4 border-warning"><h5>Всего заказов</h5><h2 class="text-warning">{len(orders)}</h2></div></div>
        <div class="col-md-4"><div class="card p-4 border-info"><h5>Общий объем</h5><h2 class="text-info">{total_vol:.1f} m³</h2></div></div>
        <div class="col-md-4"><div class="card p-4 border-success"><h5>Общая выручка</h5><h2 class="text-success">{total_amt:.2f} AZN</h2></div></div>
    </div>
    <div class="card p-4">
        <table class="table table-striped">
            <thead class="table-dark"><tr><th>ID</th><th>Дата</th><th>Объем</th><th>Сумма</th></tr></thead>
            <tbody>{rows if rows else "<tr><td colspan='4' class='text-center'>Нет данных</td></tr>"}</tbody>
        </table>
    </div>'''
    return render_html(content, t, lang)

@app.route('/reports/stock')
def report_stock():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    labels = get_labels()
    with sqlite3.connect(DB) as conn:
        stock_list = conn.execute("SELECT * FROM stock").fetchall()
        movements = conn.execute("SELECT * FROM stock_movements ORDER BY date DESC").fetchall()
    
    stock_rows = "".join([f"<tr><td>{labels.get(s[2], s[2])}</td><td>{s[3]:,.1f} кг</td><td>{s[4]:,.1f} кг</td></tr>" for s in stock_list])
    mov_rows = "".join([f"<tr><td>{m[1][:16] if m[1] else ''}</td><td>{labels.get(m[2], m[2])}</td><td class='{'text-danger' if m[3]=='OUT' else 'text-success'}'>{m[3]}</td><td>{m[4]:,.1f} кг</td></tr>" for m in movements])
    
    content = f'''
    <h2 class="text-warning mb-4">🪨 Отчет по складу</h2>
    <div class="card p-4 mb-4">
        <h5 class="text-info mb-3">Текущие остатки</h5>
        <table class="table table-striped">
            <thead class="table-dark"><tr><th>Материал</th><th>Остаток</th><th>Макс.</th></tr></thead>
            <tbody>{stock_rows if stock_rows else "<tr><td colspan='3' class='text-center'>Нет данных</td></tr>"}</tbody>
        </table>
    </div>
    <div class="card p-4">
        <h5 class="text-warning mb-3">Движения (приход/уход)</h5>
        <table class="table table-striped">
            <thead class="table-dark"><tr><th>Дата</th><th>Материал</th><th>Тип</th><th>Количество</th></tr></thead>
            <tbody>{mov_rows if mov_rows else "<tr><td colspan='4' class='text-center'>Нет движений</td></tr>"}</tbody>
        </table>
    </div>'''
    return render_html(content, t, lang)

@app.route('/reports/concrete')
def report_concrete():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        data = conn.execute('''
            SELECT r.name, COUNT(o.id), SUM(o.volume_m3), SUM(o.volume_m3 * o.price_per_m3)
            FROM orders o
            LEFT JOIN recipes r ON o.recipe_id = r.id
            GROUP BY r.name
        ''').fetchall()
    
    rows = "".join([f"<tr><td>{d[0] or 'Неизвестно'}</td><td>{d[1]}</td><td>{d[2]:.1f} m³</td><td class='text-warning fw-bold'>{d[3]:.2f} AZN</td></tr>" for d in data])
    
    content = f'''
    <h2 class="text-warning mb-4">🏗️ Отчет по бетону (марки)</h2>
    <div class="card p-4">
        <table class="table table-striped">
            <thead class="table-dark"><tr><th>Марка бетона</th><th>Кол-во заказов</th><th>Объем</th><th>Сумма</th></tr></thead>
            <tbody>{rows if rows else "<tr><td colspan='4' class='text-center'>Нет данных</td></tr>"}</tbody>
        </table>
    </div>'''
    return render_html(content, t, lang)

@app.route('/reports/clients')
def report_clients():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        data = conn.execute('''
            SELECT c.name, COUNT(o.id), SUM(o.volume_m3), SUM(o.volume_m3 * o.price_per_m3)
            FROM orders o
            LEFT JOIN clients c ON o.client_id = c.id
            GROUP BY c.name
        ''').fetchall()
    
    rows = "".join([f"<tr><td>{d[0] or 'Неизвестно'}</td><td>{d[1]}</td><td>{d[2]:.1f} m³</td><td class='text-warning fw-bold'>{d[3]:.2f} AZN</td></tr>" for d in data])
    
    content = f'''
    <h2 class="text-warning mb-4">👥 Отчет по клиентам</h2>
    <div class="card p-4">
        <table class="table table-striped">
            <thead class="table-dark"><tr><th>Клиент</th><th>Заказов</th><th>Объем</th><th>Сумма</th></tr></thead>
            <tbody>{rows if rows else "<tr><td colspan='4' class='text-center'>Нет данных</td></tr>"}</tbody>
        </table>
    </div>'''
    return render_html(content, t, lang)

@app.route('/reports/vehicles')
def report_vehicles():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        data = conn.execute('''
            SELECT v.plate_number, d.name, COUNT(o.id), SUM(o.volume_m3)
            FROM orders o
            LEFT JOIN vehicles v ON o.vehicle_id = v.id
            LEFT JOIN drivers d ON v.driver_id = d.id
            GROUP BY v.plate_number
        ''').fetchall()
    
    rows = "".join([f"<tr><td>{d[0] or 'Неизвестно'}</td><td>{d[1] or ''}</td><td>{d[2]}</td><td>{d[3]:.1f} m³</td></tr>" for d in data])
    
    content = f'''
    <h2 class="text-warning mb-4">🚛 Отчет по машинам</h2>
    <div class="card p-4">
        <table class="table table-striped">
            <thead class="table-dark"><tr><th>Машина</th><th>Водитель</th><th>Рейсов</th><th>Объем</th></tr></thead>
            <tbody>{rows if rows else "<tr><td colspan='4' class='text-center'>Нет данных</td></tr>"}</tbody>
        </table>
    </div>'''
    return render_html(content, t, lang)

# ==================== SCADA ====================
@app.route('/scada')
def scada():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    content = f'''
    <h2 class="text-warning mb-4">🖥️ {t['scada']}</h2>
    <div class="card p-5 bg-black border-warning text-center">
        <h3 class="text-warning">Beton Batching Plant SCADA</h3>
        <p class="text-muted">PLC IP: 192.168.1.50 | Modbus TCP Online</p>
        <div class="py-4">
            <a href="#" class="btn btn-success btn-lg fw-bold px-5 me-3">▶️ START</a>
            <a href="#" class="btn btn-danger btn-lg fw-bold px-5">🛑 ESTOP</a>
        </div>
    </div>'''
    return render_html(content, t, lang)

# ==================== СПРАВОЧНИКИ (CRUD) ====================
def render_crud(table_name, display_name, fields, t):
    lang = get_lang()
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            action = request.form.get('action')
            try:
                if action == 'add':
                    cols = ", ".join(fields.keys())
                    vals = ", ".join(["?" for _ in fields])
                    data = [request.form[k] for k in fields.keys()]
                    conn.execute(f"INSERT INTO {table_name} ({cols}) VALUES ({vals})", data)
                    flash("Добавлено!", "success")
                elif action == 'delete':
                    conn.execute(f"DELETE FROM {table_name} WHERE id=?", (request.form['item_id'],))
                    flash("Удалено!", "success")
                conn.commit()
            except Exception as e:
                flash(f"Ошибка: {str(e)}", "error")
            return redirect(f'/{table_name}')
        
        try:
            rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
        except:
            rows = []
    
    rows_html = ""
    for r in rows:
        cells = "".join([f"<td>{r[i] if r[i] is not None else ''}</td>" for i in range(1, len(r))])
        rows_html += f"""<tr><td>{r[0]}</td>{cells}<td>
            <form method='POST' class='d-inline'>
                <input type='hidden' name='action' value='delete'>
                <input type='hidden' name='item_id' value='{r[0]}'>
                <button type='submit' class='btn btn-danger btn-sm' onclick="return confirm('Удалить?')">🗑️</button>
            </form>
        </td></tr>"""
    
    form_fields = ""
    for key, label in fields.items():
        form_fields += f'<div class="col-md-4 mb-2"><label>{label}</label><input type="text" name="{key}" class="form-control" required></div>'

    content = f'''
    <h2 class="text-warning mb-4">📂 {display_name}</h2>
    <div class="card p-4 mb-4 border-warning">
        <h5 class="text-warning mb-3">➕ {t['add']}</h5>
        <form method="POST"><input type="hidden" name="action" value="add"><div class="row">{form_fields}</div>
        <button type="submit" class="btn btn-warning w-100 fw-bold mt-2">{t['save']}</button></form>
    </div>
    <div class="card p-4"><table class="table table-striped"><thead class="table-dark"><tr><th>ID</th>
    {"".join([f"<th>{label}</th>" for label in fields.values()])}<th>Действие</th></tr></thead><tbody>{rows_html if rows_html else "<tr><td colspan='" + str(len(fields) + 2) + "' class='text-center'>Нет данных</td></tr>"}</tbody></table></div>'''
    return render_html(content, t, lang)

@app.route('/operators', methods=['GET', 'POST'])
def operators(): 
    return render_crud('operators', 'Операторы', {'name': 'Имя', 'phone': 'Телефон'}, TRANSLATIONS[get_lang()])

@app.route('/drivers', methods=['GET', 'POST'])
def drivers(): 
    return render_crud('drivers', 'Водители', {'name': 'Имя', 'phone': 'Телефон', 'license_number': 'Вод. удостоверение'}, TRANSLATIONS[get_lang()])

@app.route('/vehicles', methods=['GET', 'POST'])
def vehicles(): 
    return render_crud('vehicles', 'Машины', {'plate_number': 'Гос. номер', 'capacity_m3': 'Объем (м³)', 'driver_id': 'Водитель ID', 'tare_weight_kg': 'Тара (кг)'}, TRANSLATIONS[get_lang()])

@app.route('/clients', methods=['GET', 'POST'])
def clients(): 
    return render_crud('clients', 'Клиенты', {'name': 'Название', 'contact': 'Контакт', 'address': 'Адрес'}, TRANSLATIONS[get_lang()])

@app.route('/suppliers', methods=['GET', 'POST'])
def suppliers(): 
    return render_crud('suppliers', 'Поставщики', {'name': 'Название', 'contact': 'Контакт'}, TRANSLATIONS[get_lang()])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
