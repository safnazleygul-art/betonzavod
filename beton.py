from flask import Flask, render_template_string, request, redirect, session, url_for
import sqlite3
import os
import csv
import io
import codecs
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "beton_zavod_ultimate_complete_key"
DB = "batch_dosing.db"

# Единоформатные переводы (строго на русском языке для единого стандарта)
TRANSLATIONS = {
    "ru": {
        "title": "SmartBeton SCADA & MES",
        "dashboard": "Панель управления",
        "orders": "Заказы и накладные",
        "recipes": "Рецепты бетона",
        "stock": "Склад и сырье",
        "reports": "Отчеты и аналитика",
        "scada": "SCADA пульт",
        "settings": "Настройки завода",
        "modbus": "Карта Modbus",
        "modbus_control": "Тест-пульт Modbus",
        "directories": "Справочники",
        "drivers": "Водители",
        "vehicles": "Миксеры / Авто",
        "clients": "Клиенты",
        "suppliers": "Поставщики",
        "operators": "Операторы",
        "company": "Предприятие",
        "lang_name": "Русский",
        "delete": "Удалить", "edit": "Править", "add": "Добавить", "save": "Сохранить",
        "back": "Назад", "sub_title": "Система промышленной автоматизации и управления бетонным заводом",
        "action": "Действие", "id": "ID", "date": "Дата"
    }
}

def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS company_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, address TEXT, phone TEXT, tax_number TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS factory_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mixer_capacity_m3 REAL, mixing_time_sec REAL, gate_open_time_sec REAL,
            gate_pulse_period_sec REAL, discharge_time_sec REAL, transporter_stop_delay_sec REAL,
            inter_hopper_open_sec REAL, cement_delay_sec REAL, water_delay_sec REAL, additive_delay_sec REAL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS operators (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS drivers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, license_number TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT, plate_number TEXT, capacity_m3 REAL, driver_id INTEGER, tare_weight_kg REAL DEFAULT 12000.0
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, contact TEXT, address TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, contact TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, 
            bunker_1 REAL, bunker_2 REAL, bunker_3 REAL, bunker_4 REAL, 
            silo_1 REAL, silo_2 REAL, silo_3 REAL, silo_4 REAL, 
            water REAL, qatki_percent REAL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, client_id INTEGER, 
            vehicle_id INTEGER, recipe_id INTEGER, volume_m3 REAL, price_per_m3 REAL DEFAULT 110.0, operator_id INTEGER, status TEXT DEFAULT 'Выполнено'
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT, material_type TEXT, code_name TEXT, current_kg REAL, max_capacity_kg REAL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS modbus_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, plc_ip TEXT DEFAULT '192.168.1.50', plc_port INTEGER DEFAULT 502, slave_id INTEGER DEFAULT 1
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS modbus_registers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, tag_name TEXT, data_type TEXT, address INTEGER, description TEXT, current_val REAL DEFAULT 0.0
        )''')
        try:
            conn.execute("ALTER TABLE modbus_registers ADD COLUMN current_val REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM company_info")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO company_info (name, address, phone, tax_number) VALUES (?, ?, ?, ?)",
                           ("Industrial Automation", "Sanqaçal 70 il oktyar küç. 17/15", "+994 55 856 55 06", "9900123456"))
            cursor.execute("INSERT INTO factory_settings (mixer_capacity_m3, mixing_time_sec, gate_open_time_sec, gate_pulse_period_sec, discharge_time_sec, transporter_stop_delay_sec, inter_hopper_open_sec, cement_delay_sec, water_delay_sec, additive_delay_sec) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (2.0, 45.0, 5.0, 1.0, 30.0, 3.5, 4.0, 2.0, 1.0, 1.5))
            
            cursor.executemany("INSERT INTO operators (name, phone) VALUES (?, ?)", [
                ("Мюрад Ибрагимов", "+994558565506"), ("Эльшан Мамедов", "+994502223344")
            ])
            cursor.executemany("INSERT INTO drivers (name, phone, license_number) VALUES (?, ?, ?)", [
                ("Мамед Мамедов", "+994501112233", "AZ-99-123"), ("Эльчин Касымов", "+994552223344", "AZ-10-456")
            ])
            cursor.executemany("INSERT INTO vehicles (plate_number, capacity_m3, driver_id, tare_weight_kg) VALUES (?, ?, ?, ?)", [
                ("10-AA-201", 10.0, 1, 12500.0), ("90-BX-555", 12.0, 2, 13200.0)
            ])
            cursor.executemany("INSERT INTO clients (name, contact, address) VALUES (?, ?, ?)", [
                ("Аграр Тикинти ООО", "+994125554433", "г. Баку, пр. З. Буниядова"),
                ("Crystal Absheron", "+994124443322", "г. Хырдалан, пр. Г. Алиева")
            ])
            cursor.executemany("INSERT INTO suppliers (name, contact) VALUES (?, ?)", [
                ("Holcim Азербайджан", "+994126990000"), ("Norm Цемент", "+994124250000")
            ])
            cursor.executemany("INSERT INTO stock (material_type, code_name, current_kg, max_capacity_kg) VALUES (?, ?, ?, ?)", [
                ('AGGREGATE', 'Бункер 1', 85000.0, 100000.0), ('AGGREGATE', 'Бункер 2', 72000.0, 100000.0),
                ('CEMENT', 'Силос 1', 45000.0, 60000.0), ('CEMENT', 'Силос 2', 32000.0, 60000.0),
                ('WATER', 'Вода', 50000.0, 50000.0), ('ADDITIVE', 'Хим. добавка', 5000.0, 10000.0)
            ])
            cursor.executemany("INSERT INTO recipes (name, bunker_1, bunker_2, bunker_3, bunker_4, silo_1, silo_2, silo_3, silo_4, water, qatki_percent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
                ("М-200 (B15)", 450, 320, 210, 160, 200, 50, 0, 0, 180, 1.0),
                ("М-250 (B20)", 400, 300, 200, 150, 250, 50, 0, 0, 175, 1.5)
            ])
            cursor.executemany("INSERT INTO orders (date, client_id, vehicle_id, recipe_id, volume_m3, price_per_m3, operator_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
                (datetime.now().isoformat(), 1, 1, 1, 10.0, 110.0, 1, 'Выполнено'),
                (datetime.now().isoformat(), 2, 2, 2, 14.0, 120.0, 2, 'Выполнено')
            ])

            if os.path.exists('shabran.gpf.csv'):
                try:
                    mod_records = []
                    with codecs.open('shabran.gpf.csv', 'r', encoding='utf-16le') as f:
                        reader = csv.reader(f, delimiter='\t')
                        next(reader, None)
                        next(reader, None)
                        for row in reader:
                            if len(row) >= 8:
                                tag = row[0].strip(' "')
                                if not tag: continue
                                try:
                                    data_type = int(row[3].strip(' "')) if row[3].strip(' "').isdigit() else 0
                                    addr_type = int(row[4].strip(' "')) if row[4].strip(' "').isdigit() else 0
                                    addr = int(row[5].strip(' "')) if row[5].strip(' "').isdigit() else 0
                                except ValueError:
                                    data_type, addr_type, addr = 0, 0, 0
                                
                                tag_upper = tag.upper()
                                bit_keywords = ['START', 'ULD', 'UC', 'BANDI', 'SILO', 'AC', 'KC', 'ALMAQ', 'VERME', 'BOSALT', 'STOP', 'SU', 'MIKSER']
                                if addr_type == 1 or (any(kw in tag_upper for kw in bit_keywords) and data_type == 0 and addr_type == 0):
                                    dtype = "BIT"
                                elif data_type == 2 or addr_type == 4:
                                    dtype = "REAL / DWORD"
                                else:
                                    dtype = "REGISTER (WORD)"
                                
                                mod_records.append((tag, dtype, addr, f"CSV (DataType:{data_type}, AddrType:{addr_type})", 0.0))
                    if mod_records:
                        cursor.executemany("INSERT INTO modbus_registers (tag_name, data_type, address, description, current_val) VALUES (?, ?, ?, ?, ?)", mod_records)
                except Exception as e:
                    print("CSV Load Error:", e)

            cursor.execute("INSERT INTO modbus_settings (plc_ip, plc_port, slave_id) VALUES ('192.168.1.50', 502, 1)")
            conn.commit()

init_db()

def get_lang():
    if 'lang' not in session: session['lang'] = 'ru'
    return session['lang']

def render_page(content_html, t, hide_nav=False):
    with sqlite3.connect(DB) as conn:
        comp = conn.execute("SELECT name FROM company_info LIMIT 1").fetchone()
        comp_name = comp[0] if comp else "Industrial Automation"

    nav_bar = ""
    if not hide_nav:
        nav_bar = f"""
        <nav class="navbar navbar-expand-xl navbar-dark bg-dark border-bottom border-secondary mb-4 shadow-sm px-3 d-print-none" style="background-color: #0f141a !important;">
          <div class="container-fluid">
            <a class="navbar-brand text-warning fw-bold fs-5 d-flex align-items-center gap-2" href="/">
              <span class="p-1 bg-warning text-dark rounded fs-6">🏗️</span> {comp_name}
            </a>
            <button class="navbar-toggler border-secondary" type="button" data-bs-toggle="collapse" data-bs-target="#modernNavbar">
              <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="modernNavbar">
              <ul class="navbar-nav me-auto mb-2 mb-xl-0 align-items-xl-center gap-1">
                <li class="nav-item"><a class="nav-link px-2 rounded" href="/">{t['dashboard']}</a></li>
                <li class="nav-item"><a class="nav-link px-2 rounded" href="/orders">{t['orders']}</a></li>
                <li class="nav-item"><a class="nav-link px-2 rounded" href="/recipes">{t['recipes']}</a></li>
                <li class="nav-item"><a class="nav-link px-2 rounded" href="/stock">{t['stock']}</a></li>
                <li class="nav-item"><a class="nav-link px-2 rounded" href="/reports">{t['reports']}</a></li>
                <li class="nav-item"><a class="nav-link px-2 rounded text-warning fw-bold" href="/scada">🖥️ {t['scada']}</a></li>
                <li class="nav-item"><a class="nav-link px-2 rounded text-info fw-bold" href="/settings">⚙️ {t['settings']}</a></li>
                <li class="nav-item"><a class="nav-link px-2 rounded text-danger fw-bold" href="/modbus">🔌 {t['modbus']}</a></li>
                <li class="nav-item"><a class="nav-link px-2 rounded text-success fw-bold" href="/modbus/control">⚡ {t['modbus_control']}</a></li>
                <li class="nav-item dropdown ms-xl-2">
                  <a class="nav-link dropdown-toggle px-2 rounded text-light fw-semibold" href="#" role="button" data-bs-toggle="dropdown">📂 {t['directories']}</a>
                  <ul class="dropdown-menu dropdown-menu-dark shadow border-secondary">
                    <li><a class="dropdown-item py-2" href="/company">🏢 {t['company']}</a></li>
                    <li><a class="dropdown-item py-2" href="/operators">👷 {t['operators']}</a></li>
                    <li><a class="dropdown-item py-2" href="/drivers">🚚 {t['drivers']}</a></li>
                    <li><a class="dropdown-item py-2" href="/vehicles">🚛 {t['vehicles']}</a></li>
                    <li><a class="dropdown-item py-2" href="/clients">🤝 {t['clients']}</a></li>
                    <li><a class="dropdown-item py-2" href="/suppliers">📦 {t['suppliers']}</a></li>
                  </ul>
                </li>
              </ul>
              <ul class="navbar-nav ms-auto align-items-center">
                <li class="nav-item text-warning fw-bold px-3 py-1 border border-warning rounded-pill">
                  🇷🇺 Русский
                </li>
              </ul>
            </div>
          </div>
        </nav>"""

    return f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{t['title']}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #0d1117; color: #e6edf3; font-family: system-ui, -apple-system, sans-serif; }}
            .card {{ background-color: #161b22; border: 1px solid #30363d; color: #e6edf3; border-radius: 10px; }}
            .table {{ color: #e6edf3; font-size: 0.9rem; }}
            .table-striped > tbody > tr:nth-of-type(odd) {{ background-color: #11161d; color: #e6edf3; }}
            .form-control, .form-select {{ background-color: #0d1117; color: #fff; border: 1px solid #30363d; }}
            .form-control:focus, .form-select:focus {{ background-color: #0d1117; color: #fff; border-color: #f0883e; box-shadow: 0 0 0 0.25rem rgba(240, 136, 62, 0.25); }}
            label {{ font-size: 0.8rem; font-weight: 600; color: #8b949e; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}
        </style>
    </head>
    <body>
        {nav_bar}
        <div class="container mb-5">{content_html}</div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

@app.route('/')
def index():
    t = TRANSLATIONS['ru']
    with sqlite3.connect(DB) as conn:
        comp = conn.execute("SELECT * FROM company_info LIMIT 1").fetchone()
    comp_name, comp_addr = (comp[1], comp[2]) if comp else ('Industrial Automation', '')
    content = f'''
    <div class="p-5 mb-4 rounded-3 card border-warning shadow-lg">
        <div class="container-fluid py-4">
            <h1 class="display-5 fw-bold text-warning">🏗️ {comp_name}</h1>
            <p class="fs-5 text-light mb-2">📍 {comp_addr}</p>
            <p class="col-md-9 fs-5 text-secondary">{t['sub_title']}</p>
            <hr class="border-secondary my-4">
            <div class="d-flex flex-wrap gap-3">
                <a href="/scada" class="btn btn-warning btn-lg fw-bold px-4">🖥️ {t['scada']}</a>
                <a href="/modbus/control" class="btn btn-success btn-lg fw-bold px-4">⚡ {t['modbus_control']}</a>
                <a href="/reports" class="btn btn-info btn-lg fw-bold px-4">📊 {t['reports']}</a>
            </div>
        </div>
    </div>'''
    return render_page(content, t)

@app.route('/orders')
def orders():
    t = TRANSLATIONS['ru']
    with sqlite3.connect(DB) as conn:
        data = conn.execute('''
            SELECT o.id, o.date, c.name, v.plate_number, r.name, o.volume_m3, o.price_per_m3, (o.volume_m3 * o.price_per_m3), o.status 
            FROM orders o 
            LEFT JOIN clients c ON o.client_id = c.id 
            LEFT JOIN vehicles v ON o.vehicle_id = v.id 
            LEFT JOIN recipes r ON o.recipe_id = r.id
        ''').fetchall()
    
    rows = "".join([f"<tr><td>{r[0]}</td><td>{r[1][:19]}</td><td><b>{r[2]}</b></td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]} м³</td><td>{r[6]} AZN</td><td class='text-warning fw-bold'>{r[7]} AZN</td><td><span class='badge bg-success'>{r[8]}</span></td></tr>" for r in data])
    
    content = f'''
    <h2 class="text-warning mb-4">📦 Журнал заказов и накладных</h2>
    <div class="card p-4 shadow">
        <div class="table-responsive">
            <table class="table table-dark table-striped align-middle">
                <thead><tr><th>ID</th><th>Дата</th><th>Клиент</th><th>Миксер</th><th>Рецепт</th><th>Объем</th><th>Цена/м³</th><th>Сумма</th><th>Статус</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>'''
    return render_page(content, t)

@app.route('/recipes')
def recipes():
    t = TRANSLATIONS['ru']
    with sqlite3.connect(DB) as conn:
        data = conn.execute("SELECT id, name, bunker_1, bunker_2, bunker_3, bunker_4, silo_1, silo_2, water, qatki_percent FROM recipes").fetchall()
    rows = "".join([f"<tr><td>{r[0]}</td><td><b>{r[1]}</b></td><td>{r[2]} кг</td><td>{r[3]} кг</td><td>{r[4]} кг</td><td>{r[5]} кг</td><td>{r[6]} кг</td><td>{r[7]} кг</td><td>{r[8]} л</td><td>{r[9]}%</td></tr>" for r in data])
    
    content = f'''
    <h2 class="text-warning mb-4">🧪 Рецепты бетонных смесей</h2>
    <div class="card p-4 shadow">
        <div class="table-responsive">
            <table class="table table-dark table-striped align-middle">
                <thead><tr><th>ID</th><th>Марка / Название</th><th>Бункер 1</th><th>Бункер 2</th><th>Бункер 3</th><th>Бункер 4</th><th>Силос 1</th><th>Силос 2</th><th>Вода</th><th>Хим. добавка</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>'''
    return render_page(content, t)

@app.route('/stock')
def stock():
    t = TRANSLATIONS['ru']
    with sqlite3.connect(DB) as conn:
        data = conn.execute("SELECT id, material_type, code_name, current_kg, max_capacity_kg FROM stock").fetchall()
    rows = "".join([f"<tr><td>{r[0]}</td><td>{r[1]}</td><td><b>{r[2]}</b></td><td class='text-success fw-bold'>{r[3]} кг</td><td>{r[4]} кг</td></tr>" for r in data])
    
    content = f'''
    <h2 class="text-warning mb-4">📦 Состояние складов и силосов</h2>
    <div class="card p-4 shadow">
        <div class="table-responsive">
            <table class="table table-dark table-striped align-middle">
                <thead><tr><th>ID</th><th>Тип материала</th><th>Наименование</th><th>Текущий остаток</th><th>Макс. емкость</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>'''
    return render_page(content, t)

@app.route('/reports')
def reports():
    t = TRANSLATIONS['ru']
    content = f'''
    <h2 class="text-warning mb-4">📊 Отчеты и аналитика производства</h2>
    <div class="card p-4 shadow">
        <p class="text-secondary">Здесь отображаются агрегированные данные по отгрузкам, расходу цемента и инертных материалов по водителям и клиентам.</p>
        <a href="/orders" class="btn btn-warning fw-bold">Перейти к журналу заказов</a>
    </div>'''
    return render_page(content, t)

@app.route('/scada')
def scada():
    t = TRANSLATIONS['ru']
    content = f'''
    <h2 class="text-warning mb-4">🖥️ SCADA пульт управления заводом</h2>
    <div class="card p-4 shadow text-center py-5">
        <h3 class="text-success mb-3">🟢 Система в режиме готовности</h3>
        <p class="text-secondary mb-4">Интерактивная визуализация дозаторов, смесителя и конвейерных лент.</p>
        <a href="/modbus/control" class="btn btn-success btn-lg fw-bold">⚡ Открыть тест-пульт управления</a>
    </div>'''
    return render_page(content, t)

@app.route('/settings')
def settings():
    t = TRANSLATIONS['ru']
    with sqlite3.connect(DB) as conn:
        cfg = conn.execute("SELECT mixer_capacity_m3, mixing_time_sec, gate_open_time_sec, discharge_time_sec FROM factory_settings LIMIT 1").fetchone()
    content = f'''
    <h2 class="text-warning mb-4">⚙️ Настройки завода и тайминги</h2>
    <div class="card p-4 shadow w-50">
        <p><b>Объем смесителя:</b> {cfg[0]} м³</p>
        <p><b>Время перемешивания:</b> {cfg[1]} сек</p>
        <p><b>Время открытия затвора:</b> {cfg[2]} сек</p>
        <p><b>Время выгрузки:</b> {cfg[3]} сек</p>
    </div>'''
    return render_page(content, t)

@app.route('/modbus', methods=['GET', 'POST'])
def modbus():
    t = TRANSLATIONS['ru']
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            if 'save_config' in request.form:
                conn.execute("UPDATE modbus_settings SET plc_ip=?, plc_port=?, slave_id=? WHERE id=1",
                           (request.form['plc_ip'], request.form['plc_port'], request.form['slave_id']))
            elif 'add_tag' in request.form:
                conn.execute("INSERT INTO modbus_registers (tag_name, data_type, address, description, current_val) VALUES (?, ?, ?, ?, 0.0)",
                           (request.form['tag_name'], request.form['data_type'], request.form['address'], request.form['description']))
            conn.commit()
            return redirect('/modbus')

        cfg = conn.execute("SELECT plc_ip, plc_port, slave_id FROM modbus_settings LIMIT 1").fetchone()
        registers = conn.execute("SELECT id, tag_name, data_type, address, description FROM modbus_registers ORDER BY data_type, address").fetchall()

    rows = "".join([f"<tr><td>{r[0]}</td><td><b>{r[1]}</b></td><td><span class='badge bg-info text-dark'>{r[2]}</span></td><td class='font-monospace text-warning fw-bold'>{r[3]}</td><td>{r[4]}</td><td><a href='/modbus/delete/{r[0]}' class='btn btn-danger btn-sm'>🗑️ {t['delete']}</a></td></tr>" for r in registers])

    content = f'''
    <h2 class="text-warning mb-4">🔌 Конфигурация Modbus TCP и Карта Регистров ({len(registers)} Тегов)</h2>
    <div class="row mb-4">
        <div class="col-md-4">
            <div class="card p-4 shadow mb-3 border-info">
                <h4 class="text-info mb-3">🌐 Сетевые настройки</h4>
                <form method="POST">
                    <input type="hidden" name="save_config" value="1">
                    <div class="mb-2"><label>IP-адрес ПЛК</label><input type="text" name="plc_ip" class="form-control" value="{cfg[0]}" required></div>
                    <div class="mb-2"><label>Порт Modbus</label><input type="number" name="plc_port" class="form-control" value="{cfg[1]}" required></div>
                    <div class="mb-3"><label>ID Устройства (Slave)</label><input type="number" name="slave_id" class="form-control" value="{cfg[2]}" required></div>
                    <button type="submit" class="btn btn-info w-100 fw-bold">{t['save']}</button>
                </form>
            </div>
        </div>
        <div class="col-md-8">
            <div class="card p-4 shadow border-secondary">
                <h4 class="text-light mb-3">📋 Реестр Modbus Тегов</h4>
                <div class="table-responsive" style="max-height: 450px; overflow-y: auto;">
                    <table class="table table-dark table-striped align-middle">
                        <thead><tr><th>ID</th><th>Имя тега</th><th>Тип</th><th>Адрес</th><th>Описание</th><th>Действие</th></tr></thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>'''
    return render_page(content, t)

@app.route('/modbus/delete/<int:reg_id>')
def delete_modbus_tag(reg_id):
    with sqlite3.connect(DB) as conn:
        conn.execute("DELETE FROM modbus_registers WHERE id = ?", (reg_id,))
        conn.commit()
    return redirect('/modbus')

@app.route('/modbus/control', methods=['GET', 'POST'])
def modbus_control():
    t = TRANSLATIONS['ru']
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            tag_id = request.form.get('tag_id')
            new_val = request.form.get('value')
            if tag_id and new_val is not None:
                try:
                    conn.execute("UPDATE modbus_registers SET current_val = ? WHERE id = ?", (float(new_val), tag_id))
                    conn.commit()
                except ValueError:
                    pass
            return redirect('/modbus/control')
        registers = conn.execute("SELECT id, tag_name, data_type, address, description, current_val FROM modbus_registers ORDER BY data_type, address").fetchall()

    rows = ""
    for r in registers:
        reg_id, tag_name, dtype, addr, desc, val = r
        val_display = int(val) if val.is_integer() else val
        if dtype == "BIT":
            is_active = val > 0
            status_badge = "<span class='badge bg-success'>ON (1)</span>" if is_active else "<span class='badge bg-secondary'>OFF (0)</span>"
            toggle_val = 0 if is_active else 1
            controls = f'''
                <div class="d-flex align-items-center gap-2">
                    {status_badge}
                    <form method="POST" class="d-inline"><input type="hidden" name="tag_id" value="{reg_id}"><input type="hidden" name="value" value="{toggle_val}"><button type="submit" class="btn btn-sm btn-outline-warning fw-bold">🔄 Toggle</button></form>
                    <form method="POST" class="d-inline"><input type="hidden" name="tag_id" value="{reg_id}"><input type="hidden" name="value" value="1"><button type="submit" class="btn btn-sm btn-outline-success">Set 1</button></form>
                    <form method="POST" class="d-inline"><input type="hidden" name="tag_id" value="{reg_id}"><input type="hidden" name="value" value="0"><button type="submit" class="btn btn-sm btn-outline-danger">Reset 0</button></form>
                </div>'''
        else:
            controls = f'''
                <form method="POST" class="d-flex align-items-center gap-2">
                    <input type="hidden" name="tag_id" value="{reg_id}">
                    <input type="number" step="any" name="value" value="{val_display}" class="form-control form-control-sm w-50 font-monospace text-warning fw-bold">
                    <button type="submit" class="btn btn-sm btn-info fw-bold">📥 Write</button>
                </form>'''

        rows += f"<tr><td>{reg_id}</td><td><b>{tag_name}</b></td><td>{dtype}</td><td>{addr}</td><td>{controls}</td><td>{desc}</td></tr>"

    content = f'''
    <h2 class="text-success mb-4">⚡ Тест-пульт Modbus</h2>
    <div class="card p-4 shadow">
        <div class="table-responsive" style="max-height: 600px; overflow-y: auto;">
            <table class="table table-dark table-striped align-middle">
                <thead><tr><th>ID</th><th>Имя тега</th><th>Тип</th><th>Адрес</th><th>Значение и управление</th><th>Описание</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>'''
    return render_page(content, t)

@app.route('/company')
def company():
    t = TRANSLATIONS['ru']
    with sqlite3.connect(DB) as conn:
        comp = conn.execute("SELECT name, address, phone, tax_number FROM company_info LIMIT 1").fetchone()
    content = f'''
    <h2 class="text-warning mb-4">🏢 Данные предприятия</h2>
    <div class="card p-4 shadow w-50">
        <p><b>Название:</b> {comp[0]}</p>
        <p><b>Адрес:</b> {comp[1]}</p>
        <p><b>Телефон:</b> {comp[2]}</p>
        <p><b>ИНН / VÖEN:</b> {comp[3]}</p>
    </div>'''
    return render_page(content, t)

@app.route('/operators')
def operators():
    t = TRANSLATIONS['ru']
    with sqlite3.connect(DB) as conn:
        data = conn.execute("SELECT id, name, phone FROM operators").fetchall()
    rows = "".join([f"<tr><td>{r[0]}</td><td><b>{r[1]}</b></td><td>{r[2]}</td></tr>" for r in data])
    content = f'''
    <h2 class="text-warning mb-4">👷 Список операторов</h2>
    <div class="card p-4 shadow w-75">
        <table class="table table-dark table-striped">
            <thead><tr><th>ID</th><th>Имя оператора</th><th>Телефон</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>'''
    return render_page(content, t)

@app.route('/drivers')
def drivers():
    t = TRANSLATIONS['ru']
    with sqlite3.connect(DB) as conn:
        data = conn.execute("SELECT id, name, phone, license_number FROM drivers").fetchall()
    rows = "".join([f"<tr><td>{r[0]}</td><td><b>{r[1]}</b></td><td>{r[2]}</td><td>{r[3]}</td></tr>" for r in data])
    content = f'''
    <h2 class="text-warning mb-4">🚚 Список водителей</h2>
    <div class="card p-4 shadow w-75">
        <table class="table table-dark table-striped">
            <thead><tr><th>ID</th><th>Имя водителя</th><th>Телефон</th><th>№ Удостоверения</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>'''
    return render_page(content, t)

@app.route('/vehicles')
def vehicles():
    t = TRANSLATIONS['ru']
    with sqlite3.connect(DB) as conn:
        data = conn.execute("SELECT v.id, v.plate_number, v.capacity_m3, d.name, v.tare_weight_kg FROM vehicles v LEFT JOIN drivers d ON v.driver_id = d.id").fetchall()
    rows = "".join([f"<tr><td>{r[0]}</td><td><b>{r[1]}</b></td><td>{r[2]} м³</td><td>{r[3]}</td><td>{r[4]} кг</td></tr>" for r in data])
    content = f'''
    <h2 class="text-warning mb-4">🚛 Миксеры и автотранспорт</h2>
    <div class="card p-4 shadow">
        <table class="table table-dark table-striped">
            <thead><tr><th>ID</th><th>Гос. номер</th><th>Объем (м³)</th><th>Водитель</th><th>Тара (кг)</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>'''
    return render_page(content, t)

@app.route('/clients')
def clients():
    t = TRANSLATIONS['ru']
    with sqlite3.connect(DB) as conn:
        data = conn.execute("SELECT id, name, contact, address FROM clients").fetchall()
    rows = "".join([f"<tr><td>{r[0]}</td><td><b>{r[1]}</b></td><td>{r[2]}</td><td>{r[3]}</td></tr>" for r in data])
    content = f'''
    <h2 class="text-warning mb-4">🤝 База клиентов</h2>
    <div class="card p-4 shadow">
        <table class="table table-dark table-striped">
            <thead><tr><th>ID</th><th>Наименование компании</th><th>Контакты</th><th>Адрес</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>'''
    return render_page(content, t)

@app.route('/suppliers')
def suppliers():
    t = TRANSLATIONS['ru']
    with sqlite3.connect(DB) as conn:
        data = conn.execute("SELECT id, name, contact FROM suppliers").fetchall()
    rows = "".join([f"<tr><td>{r[0]}</td><td><b>{r[1]}</b></td><td>{r[2]}</td></tr>" for r in data])
    content = f'''
    <h2 class="text-warning mb-4">📦 База поставщиков</h2>
    <div class="card p-4 shadow w-75">
        <table class="table table-dark table-striped">
            <thead><tr><th>ID</th><th>Поставщик сырья</th><th>Контакты</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>'''
    return render_page(content, t)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
