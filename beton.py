from flask import Flask, render_template_string, request, redirect, session, url_for, jsonify
import sqlite3
import os
import csv
import io
import codecs
from datetime import datetime

app = Flask(__name__)
app.secret_key = "beton_zavod_ultimate_secret_key"
DB = "batch_dosing.db"

TRANSLATIONS = {
    "az": {
        "title": "SmartBeton SCADA & MES",
        "dashboard": "İdarəetmə Paneli",
        "orders": "Sifarişlər & Qaimələr",
        "recipes": "Reseptlər",
        "stock": "Anbar & Xammal",
        "reports": "Analitika & Hesabatlar",
        "scada": "SCADA Pult",
        "settings": "Zavod Parametrləri",
        "modbus": "Modbus Xritələmə",
        "modbus_control": "⚡ Modbus Test Pultu",
        "directories": "Kataloqlar",
        "drivers": "Sürücülər",
        "vehicles": "Mikserlər",
        "clients": "Müştərilər",
        "suppliers": "Təchizatçılar",
        "operators": "Operatorlar",
        "company": "Müəssisə",
        "lang_name": "Azərbaycan",
        "delete": "Sil", "edit": "Redaktə", "add": "Əlavə et", "save": "Yadda saxla",
        "back": "Geri qayıt", "sub_title": "Sənaye Avtomatlaşdırma və Beton İstehsalının İdarəetmə Sistemi",
        "action": "Əməliyyat", "id": "ID", "date": "Tarix"
    },
    "tr": {
        "title": "SmartBeton SCADA & MES",
        "dashboard": "Kontrol Paneli",
        "orders": "Siparişler & İrsaliyeler",
        "recipes": "Reçeteler",
        "stock": "Stok & Hammadde",
        "reports": "Analitik & Raporlar",
        "scada": "SCADA Kontrol",
        "settings": "Santral Ayarları",
        "modbus": "Modbus Haritalama",
        "modbus_control": "⚡ Modbus Test Paneli",
        "directories": "Tanımlamalar",
        "drivers": "Şoförler",
        "vehicles": "Mikseller",
        "clients": "Müşteriler",
        "suppliers": "Tedarikçiler",
        "operators": "Operatörler",
        "company": "İşletme",
        "lang_name": "Türkçe",
        "delete": "Sil", "edit": "Düzenle", "add": "Ekle", "save": "Kaydet",
        "back": "Geri Dön", "sub_title": "Endüstriyel Otomasyon ve Beton Üretim Yönetim Sistemi",
        "action": "İşlem", "id": "ID", "date": "Tarih"
    },
    "ru": {
        "title": "SmartBeton SCADA & MES",
        "dashboard": "Панель управления",
        "orders": "Заказы и Накладные",
        "recipes": "Рецепты",
        "stock": "Склад и Сырье",
        "reports": "Аналитика и Отчеты",
        "scada": "SCADA Пульт",
        "settings": "Настройки завода",
        "modbus": "Modbus Карты",
        "modbus_control": "⚡ Тест-пульт Modbus",
        "directories": "Справочники",
        "drivers": "Водители",
        "vehicles": "Миксеры",
        "clients": "Клиенты",
        "suppliers": "Поставщики",
        "operators": "Операторы",
        "company": "Предприятие",
        "lang_name": "Русский",
        "delete": "Удалить", "edit": "Править", "add": "Добавить", "save": "Сохранить",
        "back": "Назад", "sub_title": "Промышленная автоматизация и система управления бетонным заводом",
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
            vehicle_id INTEGER, recipe_id INTEGER, volume_m3 REAL, price_per_m3 REAL DEFAULT 110.0, operator_id INTEGER, status TEXT DEFAULT 'Hazır'
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT, material_type TEXT, code_name TEXT, current_kg REAL, max_capacity_kg REAL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS modbus_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, plc_ip TEXT DEFAULT '192.168.1.50', plc_port INTEGER DEFAULT 502, slave_id INTEGER DEFAULT 1
        )''')
        
        # Таблица регистров с полем текущего значения current_val для интерактивного пульта
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
                ("Mürad İbrahimov", "+994558565506"), ("Elşən Məmmədov", "+994502223344")
            ])
            cursor.executemany("INSERT INTO drivers (name, phone, license_number) VALUES (?, ?, ?)", [
                ("Məmməd Məmmədov", "+994501112233", "AZ-99-123"), ("Elçin Qasımov", "+994552223344", "AZ-10-456")
            ])
            cursor.executemany("INSERT INTO vehicles (plate_number, capacity_m3, driver_id, tare_weight_kg) VALUES (?, ?, ?, ?)", [
                ("10-AA-201", 10.0, 1, 12500.0), ("90-BX-555", 12.0, 2, 13200.0)
            ])
            cursor.executemany("INSERT INTO clients (name, contact, address) VALUES (?, ?, ?)", [
                ("Aqrar Tikinti MMC", "+994125554433", "Bakı ş., Ziya Bünyadov pr."),
                ("Crystal Absheron", "+994124443322", "Xırdalan ş., Heydər Əliyev pr.")
            ])
            cursor.executemany("INSERT INTO suppliers (name, contact) VALUES (?, ?)", [
                ("Holcim Azərbaycan", "+994126990000"), ("Norm Sement", "+994124250000")
            ])
            cursor.executemany("INSERT INTO stock (material_type, code_name, current_kg, max_capacity_kg) VALUES (?, ?, ?, ?)", [
                ('AGGREGATE', 'Bunker 1', 85000.0, 100000.0), ('AGGREGATE', 'Bunker 2', 72000.0, 10000.0),
                ('CEMENT', 'Silo 1', 45000.0, 60000.0), ('CEMENT', 'Silo 2', 32000.0, 60000.0),
                ('WATER', 'Su', 50000.0, 50000.0), ('ADDITIVE', 'Qatqı', 5000.0, 10000.0)
            ])
            cursor.executemany("INSERT INTO recipes (name, bunker_1, bunker_2, bunker_3, bunker_4, silo_1, silo_2, silo_3, silo_4, water, qatki_percent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
                ("M-200 (B15)", 450, 320, 210, 160, 200, 50, 0, 0, 180, 1.0),
                ("M-250 (B20)", 400, 300, 200, 150, 250, 50, 0, 0, 175, 1.5)
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
                                
                                if addr_type == 1:
                                    dtype = "BIT"
                                elif data_type == 2 or addr_type == 4:
                                    dtype = "REAL / DWORD"
                                else:
                                    dtype = "REGISTER (WORD)"
                                
                                mod_records.append((tag, dtype, addr, f"DataType:{data_type}, AddrType:{addr_type}", 0.0))
                    if mod_records:
                        cursor.executemany("INSERT INTO modbus_registers (tag_name, data_type, address, description, current_val) VALUES (?, ?, ?, ?, ?)", mod_records)
                except Exception as e:
                    print("CSV Load Error:", e)

            cursor.execute("INSERT INTO modbus_settings (plc_ip, plc_port, slave_id) VALUES ('192.168.1.50', 502, 1)")
            conn.commit()

init_db()

def get_lang():
    if 'lang' not in session: session['lang'] = 'az'
    return session['lang']

@app.route('/set_lang/<lang_code>')
def set_lang(lang_code):
    if lang_code in TRANSLATIONS: session['lang'] = lang_code
    return redirect(request.referrer or url_for('index'))

def render_page(content_html, t, current_lang, hide_nav=False):
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
                <li class="nav-item"><a class="nav-link px-2 rounded text-info fw-bold" href="/modbus">🔌 {t['modbus']}</a></li>
                <li class="nav-item"><a class="nav-link px-2 rounded text-success fw-bold" href="/modbus/control">{t['modbus_control']}</a></li>
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
                <li class="nav-item dropdown">
                  <a class="nav-link dropdown-toggle text-warning fw-bold px-3 py-1 border border-warning rounded-pill" href="#" role="button" data-bs-toggle="dropdown">
                    🌐 {t['lang_name']}
                  </a>
                  <ul class="dropdown-menu dropdown-menu-dark dropdown-menu-end shadow border-secondary">
                    <li><a class="dropdown-item" href="/set_lang/az">🇦🇿 Azərbaycan dili</a></li>
                    <li><a class="dropdown-item" href="/set_lang/tr">🇹🇷 Türkçe</a></li>
                    <li><a class="dropdown-item" href="/set_lang/ru">🇷🇺 Русский</a></li>
                  </ul>
                </li>
              </ul>
            </div>
          </div>
        </nav>"""

    return f"""
    <!DOCTYPE html>
    <html lang="{current_lang}">
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
            @media print {{
                body {{ background-color: #fff !important; color: #000 !important; }}
                .card {{ background-color: #fff !important; color: #000 !important; border: 1px solid #ddd !important; box-shadow: none !important; }}
                .table {{ color: #000 !important; }}
                .d-print-none {{ display: none !important; }}
            }}
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
    lang = get_lang()
    t = TRANSLATIONS[lang]
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
                <a href="/scada" class="btn btn-warning btn-lg fw-bold px-4">🖥️ SCADA Pult & Start</a>
                <a href="/modbus/control" class="btn btn-success btn-lg fw-bold px-4">{t['modbus_control']}</a>
                <a href="/reports" class="btn btn-info btn-lg fw-bold px-4">📊 Analitika & Hesabatlar</a>
            </div>
        </div>
    </div>'''
    return render_page(content, t, lang)

@app.route('/modbus', methods=['GET', 'POST'])
def modbus():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            if 'save_config' in request.form:
                conn.execute("UPDATE modbus_settings SET plc_ip=?, plc_port=?, slave_id=? WHERE id=1",
                           (request.form['plc_ip'], request.form['plc_port'], request.form['slave_id']))
            elif 'add_tag' in request.form:
                conn.execute("INSERT INTO modbus_registers (tag_name, data_type, address, description, current_val) VALUES (?, ?, ?, ?, 0.0)",
                           (request.form['tag_name'], request.form['data_type'], request.form['address'], request.form['description']))
            elif 'upload_csv' in request.files:
                file = request.files['upload_csv']
                if file and file.filename.endswith('.csv'):
                    content_bytes = file.read()
                    text_content = ""
                    for enc in ['utf-16le', 'utf-8', 'cp1251']:
                        try:
                            text_content = content_bytes.decode(enc)
                            break
                        except Exception:
                            continue
                    if text_content:
                        f_stream = io.StringIO(text_content)
                        reader = csv.reader(f_stream, delimiter='\t')
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
                                
                                if addr_type == 1:
                                    dtype = "BIT"
                                elif data_type == 2 or addr_type == 4:
                                    dtype = "REAL / DWORD"
                                else:
                                    dtype = "REGISTER (WORD)"

                                conn.execute("INSERT INTO modbus_registers (tag_name, data_type, address, description, current_val) VALUES (?, ?, ?, ?, 0.0)",
                                             (tag, dtype, addr, f"CSV (DataType:{data_type}, AddrType:{addr_type})"))
            conn.commit()
            return redirect('/modbus')

        cfg = conn.execute("SELECT plc_ip, plc_port, slave_id FROM modbus_settings LIMIT 1").fetchone()
        if not cfg:
            conn.execute("INSERT INTO modbus_settings (plc_ip, plc_port, slave_id) VALUES ('192.168.1.50', 502, 1)")
            conn.commit()
            cfg = ('192.168.1.50', 502, 1)

        registers = conn.execute("SELECT id, tag_name, data_type, address, description FROM modbus_registers ORDER BY data_type, address").fetchall()

    rows = ""
    for r in registers:
        if r[2] == "BIT":
            badge = "<span class='badge bg-info text-dark'>BIT</span>"
        elif "REAL" in r[2]:
            badge = "<span class='badge bg-success'>REAL / DWORD</span>"
        else:
            badge = "<span class='badge bg-warning text-dark'>REGISTER (WORD)</span>"

        rows += f"""<tr>
            <td>{r[0]}</td>
            <td><b>{r[1]}</b></td>
            <td>{badge}</td>
            <td class='font-monospace text-warning fw-bold'>{r[3]}</td>
            <td>{r[4]}</td>
            <td><a href='/modbus/delete/{r[0]}' class='btn btn-danger btn-sm' onclick="return confirm('Silmek istediyinizden əminsiniz?')">🗑️ {t['delete']}</a></td>
        </tr>"""

    content = f'''
    <h2 class="text-warning mb-4">🔌 Modbus TCP Configuration & Register Mapping ({len(registers)} Tags)</h2>
    <div class="row mb-4">
        <div class="col-md-4">
            <div class="card p-4 shadow mb-3 border-info">
                <h4 class="text-info mb-3">🌐 Connection</h4>
                <form method="POST">
                    <input type="hidden" name="save_config" value="1">
                    <div class="mb-2"><label>PLC IP Address</label><input type="text" name="plc_ip" class="form-control" value="{cfg[0]}" required></div>
                    <div class="mb-2"><label>Modbus Port</label><input type="number" name="plc_port" class="form-control" value="{cfg[1]}" required></div>
                    <div class="mb-3"><label>Slave / Unit ID</label><input type="number" name="slave_id" class="form-control" value="{cfg[2]}" required></div>
                    <button type="submit" class="btn btn-info w-100 fw-bold">{t['save']}</button>
                </form>
            </div>
            <div class="card p-4 shadow border-success mb-3">
                <h4 class="text-success mb-3">📁 Импорт CSV Тегов</h4>
                <form method="POST" enctype="multipart/form-data">
                    <div class="mb-3">
                        <input type="file" name="upload_csv" class="form-control" accept=".csv" required>
                    </div>
                    <button type="submit" class="btn btn-success w-100 fw-bold">📥 Загрузить и Импортировать</button>
                </form>
            </div>
        </div>
        <div class="col-md-8">
            <div class="card p-4 shadow mb-4 border-warning">
                <h4 class="text-warning mb-3">➕ Add Tag / Address</h4>
                <form method="POST">
                    <input type="hidden" name="add_tag" value="1">
                    <div class="row">
                        <div class="col-md-6 mb-2"><label>Tag Name</label><input type="text" name="tag_name" class="form-control" placeholder="e.g. Bunker1_Weight" required></div>
                        <div class="col-md-6 mb-2"><label>Type</label><select name="data_type" class="form-select"><option value="REGISTER (WORD)">REGISTER (WORD)</option><option value="BIT">BIT</option><option value="REAL / DWORD">REAL / DWORD</option></select></div>
                        <div class="col-md-6 mb-2"><label>Address Offset</label><input type="number" name="address" class="form-control" placeholder="e.g. 40001" required></div>
                        <div class="col-md-6 mb-2"><label>Description</label><input type="text" name="description" class="form-control" placeholder="Description"></div>
                    </div>
                    <button type="submit" class="btn btn-success w-100 fw-bold mt-2">{t['add']}</button>
                </form>
            </div>
            <div class="card p-4 shadow border-secondary">
                <h4 class="text-light mb-3">📋 Реестр Modbus Тегов и Типов</h4>
                <div class="table-responsive" style="max-height: 450px; overflow-y: auto;">
                    <table class="table table-dark table-striped align-middle">
                        <thead><tr><th>{t['id']}</th><th>Tag Name</th><th>Type</th><th>Address</th><th>Description</th><th>{t['action']}</th></tr></thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>'''
    return render_page(content, t, lang)

@app.route('/modbus/delete/<int:reg_id>')
def delete_modbus_tag(reg_id):
    with sqlite3.connect(DB) as conn:
        conn.execute("DELETE FROM modbus_registers WHERE id = ?", (reg_id,))
        conn.commit()
    return redirect('/modbus')

# НОВЫЙ ИНТЕРАКТИВНЫЙ ТЕСТ-ПУЛЬТ (MODBUS CONTROL & MONITOR)
@app.route('/modbus/control', methods=['GET', 'POST'])
def modbus_control():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            tag_id = request.form.get('tag_id')
            new_val = request.form.get('value')
            if tag_id and new_val is not None:
                try:
                    val_float = float(new_val)
                    conn.execute("UPDATE modbus_registers SET current_val = ? WHERE id = ?", (val_float, tag_id))
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
            
            controls = f"""
                <div class="d-flex align-items-center gap-2">
                    {status_badge}
                    <form method="POST" class="d-inline">
                        <input type="hidden" name="tag_id" value="{reg_id}">
                        <input type="hidden" name="value" value="{toggle_val}">
                        <button type="submit" class="btn btn-sm btn-outline-warning fw-bold">🔄 Toggle</button>
                    </form>
                    <form method="POST" class="d-inline">
                        <input type="hidden" name="tag_id" value="{reg_id}">
                        <input type="hidden" name="value" value="1">
                        <button type="submit" class="btn btn-sm btn-outline-success">Set 1</button>
                    </form>
                    <form method="POST" class="d-inline">
                        <input type="hidden" name="tag_id" value="{reg_id}">
                        <input type="hidden" name="value" value="0">
                        <button type="submit" class="btn btn-sm btn-outline-danger">Reset 0</button>
                    </form>
                </div>
            """
        else:
            controls = f"""
                <form method="POST" class="d-flex align-items-center gap-2">
                    <input type="hidden" name="tag_id" value="{reg_id}">
                    <input type="number" step="any" name="value" value="{val_display}" class="form-control form-control-sm w-50 font-monospace text-warning fw-bold">
                    <button type="submit" class="btn btn-sm btn-info fw-bold">📥 Write</button>
                </form>
            """

        type_badge = "<span class='badge bg-info text-dark'>BIT</span>" if dtype == "BIT" else ("<span class='badge bg-success'>REAL</span>" if "REAL" in dtype else "<span class='badge bg-warning text-dark'>WORD</span>")

        rows += f"""<tr>
            <td>{reg_id}</td>
            <td><b>{tag_name}</b></td>
            <td>{type_badge}</td>
            <td class='font-monospace text-info fw-bold'>{addr}</td>
            <td>{controls}</td>
            <td class='text-muted small'>{desc}</td>
        </tr>"""

    content = f'''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h2 class="text-success mb-1">⚡ Modbus TCP Test & Control Panel</h2>
            <p class="text-secondary mb-0">Отправка команд, переключение битов (Toggle / Reset / Set) и запись значений в регистры в реальном времени.</p>
        </div>
        <a href="/modbus" class="btn btn-outline-light btn-sm">⚙️ Настройка тегов</a>
    </div>

    <div class="card p-4 shadow border-success">
        <div class="table-responsive" style="max-height: 650px; overflow-y: auto;">
            <table class="table table-dark table-striped align-middle">
                <thead>
                    <tr>
                        <th>{t['id']}</th>
                        <th>Tag Name</th>
                        <th>Type</th>
                        <th>Address</th>
                        <th>Value & Control (Read / Write / Toggle)</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
    </div>
    '''
    return render_page(content, t, lang)

# Остальные заглушки навигации
@app.route('/orders')
def orders(): return render_page("<h2 class='text-warning'>📦 Sifarişlər Modulu</h2>", TRANSLATIONS[get_lang()], get_lang())
@app.route('/recipes')
def recipes(): return render_page("<h2 class='text-warning'>🧪 Reseptlər Modulu</h2>", TRANSLATIONS[get_lang()], get_lang())
@app.route('/stock')
def stock(): return render_page("<h2 class='text-warning'>📦 Anbar və Xammal</h2>", TRANSLATIONS[get_lang()], get_lang())
@app.route('/reports')
def reports(): return render_page("<h2 class='text-warning'>📊 Analitika və Hesabatlar</h2>", TRANSLATIONS[get_lang()], get_lang())
@app.route('/scada')
def scada(): return render_page("<h2 class='text-warning'>🖥️ SCADA Pult İdarəetmə Paneli</h2>", TRANSLATIONS[get_lang()], get_lang())
@app.route('/settings')
def settings(): return render_page("<h2 class='text-warning'>⚙️ Zavod Parametrləri</h2>", TRANSLATIONS[get_lang()], get_lang())
@app.route('/company')
def company(): return render_page("<h2 class='text-warning'>🏢 Müəssisə Məlumatları</h2>", TRANSLATIONS[get_lang()], get_lang())
@app.route('/operators')
def operators(): return render_page("<h2 class='text-warning'>👷 Operatorlar Siyahısı</h2>", TRANSLATIONS[get_lang()], get_lang())
@app.route('/drivers')
def drivers(): return render_page("<h2 class='text-warning'>🚚 Sürücülər Siyahısı</h2>", TRANSLATIONS[get_lang()], get_lang())
@app.route('/vehicles')
def vehicles(): return render_page("<h2 class='text-warning'>🚛 Mikserlər və Avtomaşınlar</h2>", TRANSLATIONS[get_lang()], get_lang())
@app.route('/clients')
def clients(): return render_page("<h2 class='text-warning'>🤝 Müştərilər Bazası</h2>", TRANSLATIONS[get_lang()], get_lang())
@app.route('/suppliers')
def suppliers(): return render_page("<h2 class='text-warning'>📦 Təchizatçılar Bazası</h2>", TRANSLATIONS[get_lang()], get_lang())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
