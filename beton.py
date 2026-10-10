from flask import Flask, render_template_string, request, redirect, session, url_for, jsonify, Response
import sqlite3
import urllib.parse
from datetime import datetime, timedelta
import os
import threading
import webbrowser
import pystray
from PIL import Image, ImageDraw
import csv
import io

app = Flask(__name__)
app.secret_key = "beton_zavod_secret_key"
DB = "batch_dosing.db"

TRANSLATIONS = {
    "az": {
        "title": "Beton Zavod SCADA", "home": "Əsas səhifə", "orders": "Sifarişlər və Qaimələr",
        "recipes": "Reseptlər", "stock": "Anbar və Xammal", "reports": "Hesabatlar",
        "scada": "SCADA Pult", "settings": "PLC Tənzimləmələri", "directories": "Sorğular",
        "drivers": "Sürücülər", "vehicles": "Mikserlər", "clients": "Müştərilər",
        "suppliers": "Təchizatçılar", "operators": "Operatorlar", "company": "Müəssisə",
        "lang_name": "Azərbaycan dili", "home_scada": "🖥️ SCADA Pult & Start",
        "home_reports": "📊 Hesabatlar", "home_orders": "📦 Sifarişlər",
        "delete": "Sil", "edit": "Redaktə", "add": "Əlavə et", "save": "Yadda saxla",
        "print_version": "Çap Versiyası", "export_csv": "📥 CSV İxrac", "back": "Geri qayıt", "nakladnoy": "Nəqliyyat Qaiməsi",
        "sub_title": "SCADA və Beton Zavod İdarəetmə Sistemi",
        "client": "Müştəri", "mixer": "Mikser", "recipe": "Resept", "volume": "Həcm (m³)",
        "price_m3": "1 m³ Qiyməti (AZN)", "total_price": "Ümumi Məbləğ", "operator": "Operator",
        "confirm_order": "💾 Sifarişi Təsdiq Et", "id": "ID", "date": "Tarix", "document": "Sənəd", "action": "Əməliyyat",
        "start_date": "Başlanğıc", "end_date": "Bitmə", "material": "Material", "op_type": "Əməliyyat",
        "all_materials": "Bütün Materiallar", "all_silos": "🪨 Bütün Silolar", "all_recipes": "Bütün Markalar",
        "all_ops": "Bütün Əməliyyatlar", "all_clients": "Bütün Müştərilər", "all_drivers": "Bütün Sürücülər",
        "consumption": "Sərfiyyat", "income": "Gəliş", "search": "🔍 Axtar", "total_volume": "Ümumi Həcm",
        "total_qty": "Ümumi Miqdar", "total_amount": "Ümumi Məbləğ", "driver_rep": "🚚 Sürücülər Üzrə",
        "client_rep": "🏢 Müştərilər Üzrə", "trips": "Reys", "order_count": "Sifariş Sayı",
        "note": "Qeyd", "supplier": "Təchizatçı", "add_stock": "📥 Yeni Xammal Girişi",
        "save_stock": "💾 Anbara Daxil Et", "current_stock": "Cari Qalıq", "max_capacity": "Max Tutum",
        "refill": "➕ Dolu", "start_prod": "▶️ Başla", "estop": "🛑 ESTOP",
        "phase1": "1. Dozaj", "phase2": "2. Yükləmə", "phase3": "3. Zames & Sliv",
        "ready": "Hazırdır", "waiting": "Gözləyir", "phone": "Telefon", "license": "Vəsiqə",
        "address": "Ünvan", "tax_no": "VÖEN", "company_name": "Müəssisə Adı", "close": "Bağla", "print": "🖨️ Çap",
        "delivered_by": "Təhvil Verən", "received_by": "Təhvil Alan", "product_name": "Məhsul",
        "phone_label": "Tel", "address_label": "Ünvan", "driver_label": "Sürücü",
        "tare_weight": "Tara", "concrete_weight": "Beton Çəkisi", "gross_weight": "Brutto",
        "added_by": "Əlavə edən", "vehicle": "Maşın", "stock_rep": "Anbar Hesabatı",
        "concrete_rep": "Beton Hesabatı", "vehicle_rep": "Maşın Hesabatı"
    },
    "ru": {
        "title": "Бетонный Завод SCADA", "home": "Главная", "orders": "Заказы и Накладные",
        "recipes": "Рецепты", "stock": "Склад и Сырье", "reports": "Отчеты",
        "scada": "SCADA Пульт", "settings": "Настройки ПЛК", "directories": "Справочники",
        "drivers": "Водители", "vehicles": "Миксеры", "clients": "Клиенты",
        "suppliers": "Поставщики", "operators": "Операторы", "company": "Предприятие",
        "lang_name": "Русский", "home_scada": "🖥️ SCADA Пульт & Старт",
        "home_reports": "📊 Отчеты", "home_orders": "📦 Заказы",
        "delete": "Удалить", "edit": "Править", "add": "Добавить", "save": "Сохранить",
        "print_version": "Версия для печати", "export_csv": "📥 Экспорт CSV", "back": "Назад", "nakladnoy": "ТТН",
        "sub_title": "SCADA и Система Управления Бетонным Заводом",
        "client": "Клиент", "mixer": "Миксер", "recipe": "Рецепт", "volume": "Объем (м³)",
        "price_m3": "Цена за 1 м³", "total_price": "Общая Стоимость", "operator": "Оператор",
        "confirm_order": "💾 Подтвердить и Списать", "id": "ID", "date": "Дата", "document": "Документ", "action": "Действие",
        "start_date": "Начало", "end_date": "Конец", "material": "Материал", "op_type": "Тип Операции",
        "all_materials": "Все Материалы", "all_silos": "🪨 Все Силосы", "all_recipes": "Все Марки",
        "all_ops": "Все Операции", "all_clients": "Все Клиенты", "all_drivers": "Все Водители",
        "consumption": "Расход", "income": "Приход", "search": "🔍 Найти", "total_volume": "Общий Объем",
        "total_qty": "Общее Кол-во", "total_amount": "Общая Сумма", "driver_rep": "🚚 По Водителям",
        "client_rep": "🏢 По Клиентам", "trips": "Рейсов", "order_count": "Заказов",
        "note": "Примечание", "supplier": "Поставщик", "add_stock": "📥 Поступление Сырья",
        "save_stock": "💾 Внести на Склад", "current_stock": "Текущий Остаток", "max_capacity": "Макс Емкость",
        "refill": "➕ Заполнить", "start_prod": "▶️ Начать", "estop": "🛑 ESTOP",
        "phase1": "1. Дозирование", "phase2": "2. Загрузка", "phase3": "3. Замес и Слив",
        "ready": "Готов", "waiting": "Ожидание", "phone": "Телефон", "license": "Вод. Удостоверение",
        "address": "Адрес", "tax_no": "ИНН", "company_name": "Название Предприятия", "close": "Закрыть", "print": "🖨️ Печать",
        "delivered_by": "Сдал", "received_by": "Принял", "product_name": "Продукция",
        "phone_label": "Тел", "address_label": "Адрес", "driver_label": "Водитель",
        "tare_weight": "Тара", "concrete_weight": "Вес Бетона", "gross_weight": "Брутто",
        "added_by": "Кто добавил", "vehicle": "Машина", "stock_rep": "Отчет по Складу",
        "concrete_rep": "Отчет по Бетону", "vehicle_rep": "Отчет по Машинам"
    }
}

def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS company_info (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, address TEXT, phone TEXT, tax_number TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS factory_settings (id INTEGER PRIMARY KEY AUTOINCREMENT, mixer_capacity_m3 REAL, mixing_time_sec REAL, gate_open_time_sec REAL, gate_pulse_period_sec REAL, discharge_time_sec REAL, transporter_stop_delay_sec REAL, inter_hopper_open_sec REAL, cement_delay_sec REAL, water_delay_sec REAL, additive_delay_sec REAL)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS operators (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS drivers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, license_number TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY AUTOINCREMENT, plate_number TEXT, capacity_m3 REAL, driver_id INTEGER, tare_weight_kg REAL DEFAULT 12000.0)''')
        try: conn.execute("ALTER TABLE vehicles ADD COLUMN tare_weight_kg REAL DEFAULT 12000.0")
        except: pass
        
        conn.execute('''CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, contact TEXT, address TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, contact TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS recipes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, bunker_1 REAL, bunker_2 REAL, bunker_3 REAL, bunker_4 REAL, silo_1 REAL, silo_2 REAL, silo_3 REAL, silo_4 REAL, water REAL, qatki_percent REAL)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, client_id INTEGER, vehicle_id INTEGER, recipe_id INTEGER, volume_m3 REAL, price_per_m3 REAL DEFAULT 110.0, operator_id INTEGER, status TEXT DEFAULT 'Hazır')''')
        
        # Обновленная таблица stock с новыми полями
        conn.execute('''CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY AUTOINCREMENT, material_type TEXT, code_name TEXT, current_kg REAL, max_capacity_kg REAL, added_by TEXT, supplier_id INTEGER, vehicle_id INTEGER)''')
        try: conn.execute("ALTER TABLE stock ADD COLUMN added_by TEXT DEFAULT 'Admin'")
        except: pass
        try: conn.execute("ALTER TABLE stock ADD COLUMN supplier_id INTEGER")
        except: pass
        try: conn.execute("ALTER TABLE stock ADD COLUMN vehicle_id INTEGER")
        except: pass

        conn.execute('''CREATE TABLE IF NOT EXISTS stock_income (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, supplier_id INTEGER, material_code TEXT, quantity_kg REAL, note TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS stock_movements (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, operation_type TEXT, material_name TEXT, quantity_kg REAL, partner_name TEXT, note TEXT)''')

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM company_info")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO company_info (name, address, phone, tax_number) VALUES (?, ?, ?, ?)", ("Industrial Automation", "Sanqaçal 70 il oktyar küç. 17/15", "+994 55 856 55 06", "9900123456"))
            cursor.execute("INSERT INTO factory_settings (mixer_capacity_m3, mixing_time_sec, gate_open_time_sec, gate_pulse_period_sec, discharge_time_sec, transporter_stop_delay_sec, inter_hopper_open_sec, cement_delay_sec, water_delay_sec, additive_delay_sec) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (2.0, 45.0, 5.0, 1.0, 30.0, 3.5, 4.0, 2.0, 1.0, 1.5))
            cursor.executemany("INSERT INTO operators (name, phone) VALUES (?, ?)", [("Mürad İbrahimov", "+994558565506"), ("Elşən Məmmədov", "+994502223344")])
            cursor.executemany("INSERT INTO drivers (name, phone, license_number) VALUES (?, ?, ?)", [("Məmməd Məmmədov", "+994501112233", "AZ-99-123"), ("Elçin Qasımov", "+994552223344", "AZ-10-456")])
            cursor.executemany("INSERT INTO vehicles (plate_number, capacity_m3, driver_id, tare_weight_kg) VALUES (?, ?, ?, ?)", [("10-AA-201", 10.0, 1, 12500.0), ("90-BX-555", 12.0, 2, 13200.0)])
            cursor.executemany("INSERT INTO clients (name, contact, address) VALUES (?, ?, ?)", [("Aqrar Tikinti MMC", "+994125554433", "Bakı"), ("Crystal Absheron", "+994124443322", "Xırdalan")])
            cursor.executemany("INSERT INTO suppliers (name, contact) VALUES (?, ?)", [("Holcim Azərbaycan", "+994126990000"), ("Norm Sement", "+994124250000")])
            
            # 10 ингредиентов
            stock_data = [
                ('AGGREGATE', 'Bunker 1', 85000.0, 100000.0, 'Admin', 1, 1), ('AGGREGATE', 'Bunker 2', 72000.0, 100000.0, 'Admin', 1, 1),
                ('AGGREGATE', 'Bunker 3', 94000.0, 120000.0, 'Admin', 1, 1), ('AGGREGATE', 'Bunker 4', 88000.0, 120000.0, 'Admin', 1, 1),
                ('CEMENT', 'Silo 1', 45000.0, 60000.0, 'Admin', 2, 1), ('CEMENT', 'Silo 2', 32000.0, 60000.0, 'Admin', 2, 1),
                ('CEMENT', 'Silo 3', 15000.0, 40000.0, 'Admin', 2, 1), ('CEMENT', 'Silo 4', 20000.0, 50000.0, 'Admin', 2, 1),
                ('WATER', 'Su', 50000.0, 50000.0, 'Admin', None, None), ('ADDITIVE', 'Qatqı', 5000.0, 10000.0, 'Admin', 1, 1)
            ]
            cursor.executemany("INSERT INTO stock (material_type, code_name, current_kg, max_capacity_kg, added_by, supplier_id, vehicle_id) VALUES (?, ?, ?, ?, ?, ?, ?)", stock_data)

            cursor.executemany("INSERT INTO recipes (name, bunker_1, bunker_2, bunker_3, bunker_4, silo_1, silo_2, silo_3, silo_4, water, qatki_percent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [("M-200 (B15)", 450, 320, 210, 160, 200, 50, 0, 0, 180, 1.0), ("M-300 (B22.5)", 450, 350, 250, 150, 300, 100, 0, 0, 165, 2.0)])
            
            now = datetime.now()
            orders_data = [((now - timedelta(days=1)).isoformat(), 1, 1, 1, 10.0, 110.0, 1), (now.isoformat(), 2, 2, 2, 12.0, 110.0, 2)]
            for od in orders_data:
                cursor.execute("INSERT INTO orders (date, client_id, vehicle_id, recipe_id, volume_m3, price_per_m3, operator_id) VALUES (?, ?, ?, ?, ?, ?, ?)", od)
            conn.commit()

init_db()

def get_lang():
    if 'lang' not in session: session['lang'] = 'ru'
    return session['lang']

@app.route('/set_lang/<lang_code>')
def set_lang(lang_code):
    if lang_code in TRANSLATIONS: session['lang'] = lang_code
    return redirect(request.referrer or url_for('index'))

def get_all(table):
    with sqlite3.connect(DB) as conn:
        return conn.execute(f"SELECT * FROM {table}").fetchall()

def render_page(content_html, t, current_lang, hide_nav=False):
    with sqlite3.connect(DB) as conn:
        comp = conn.execute("SELECT name FROM company_info LIMIT 1").fetchone()
        comp_name = comp[0] if comp else "Industrial Automation"

    nav_bar = ""
    if not hide_nav:
        nav_bar = f"""
        <nav class="navbar navbar-expand-xl navbar-dark bg-dark border-bottom border-secondary mb-4 shadow px-3 d-print-none">
          <div class="container-fluid">
            <a class="navbar-brand text-warning fw-bold fs-5" href="/">🏗️ {comp_name}</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"><span class="navbar-toggler-icon"></span></button>
            <div class="collapse navbar-collapse" id="navbarNav">
              <ul class="navbar-nav me-auto mb-2 mb-lg-0 align-items-xl-center">
                <li class="nav-item"><a class="nav-link" href="/">{t['home']}</a></li>
                <li class="nav-item"><a class="nav-link" href="/orders">{t['orders']}</a></li>
                <li class="nav-item"><a class="nav-link" href="/recipes">{t['recipes']}</a></li>
                <li class="nav-item"><a class="nav-link" href="/stock">{t['stock']}</a></li>
                <li class="nav-item"><a class="nav-link" href="/reports">{t['reports']}</a></li>
                <li class="nav-item"><a class="nav-link text-warning fw-bold" href="/scada">🖥️ {t['scada']}</a></li>
                <li class="nav-item dropdown ms-xl-2">
                  <a class="nav-link dropdown-toggle text-info fw-bold" href="#" role="button" data-bs-toggle="dropdown">📂 {t['directories']}</a>
                  <ul class="dropdown-menu dropdown-menu-dark shadow">
                    <li><a class="dropdown-item" href="/company">{t['company']}</a></li>
                    <li><a class="dropdown-item" href="/operators">{t['operators']}</a></li>
                    <li><a class="dropdown-item" href="/drivers">{t['drivers']}</a></li>
                    <li><a class="dropdown-item" href="/vehicles">{t['vehicles']}</a></li>
                    <li><a class="dropdown-item" href="/clients">{t['clients']}</a></li>
                    <li><a class="dropdown-item" href="/suppliers">{t['suppliers']}</a></li>
                  </ul>
                </li>
              </ul>
              <ul class="navbar-nav">
                <li class="nav-item dropdown">
                  <a class="nav-link dropdown-toggle text-warning fw-bold" href="#" role="button" data-bs-toggle="dropdown">🌐 {t['lang_name']}</a>
                  <ul class="dropdown-menu dropdown-menu-dark dropdown-menu-end shadow">
                    <li><a class="dropdown-item" href="/set_lang/az">🇦🇿 AZ</a></li>
                    <li><a class="dropdown-item" href="/set_lang/ru">🇷🇺 RU</a></li>
                  </ul>
                </li>
              </ul>
            </div>
          </div>
        </nav>"""

    layout = f"""
    <!DOCTYPE html>
    <html lang="{current_lang}">
    <head>
        <meta charset="UTF-8"><title>{t['title']}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #121619; color: #e9ecef; }}
            .card {{ background-color: #1d232a; border: 1px solid #2f363d; color: #e9ecef; }}
            .table {{ color: #e9ecef; font-size: 0.9rem; }}
            .table-striped > tbody > tr:nth-of-type(odd) {{ background-color: #181d22; }}
            .form-control, .form-select {{ background-color: #262d35; color: #fff; border: 1px solid #3d4650; }}
            .form-control:focus, .form-select:focus {{ background-color: #262d35; color: #fff; border-color: #ffc107; box-shadow: 0 0 0 0.25rem rgba(255, 193, 7, 0.25); }}
            label {{ font-size: 0.8rem; font-weight: bold; color: #ffc107; margin-bottom: 2px; }}
            @media print {{
                body {{ background-color: #fff !important; color: #000 !important; }}
                .card {{ background-color: #fff !important; color: #000 !important; border: 1px solid #000 !important; }}
                .table {{ color: #000 !important; }}
                .table-striped > tbody > tr:nth-of-type(odd) {{ background-color: #f8f9fa !important; }}
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
    return layout

@app.route('/')
def index():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        comp = conn.execute("SELECT * FROM company_info LIMIT 1").fetchone()
    comp_name, comp_addr = (comp[1], comp[2]) if comp else ('Industrial Automation', '')
    content = f'''
    <div class="p-5 mb-4 rounded-3 card border-warning shadow">
        <div class="container-fluid py-3">
            <h1 class="display-5 fw-bold text-warning">🏗️ {comp_name}</h1>
            <p class="fs-5 text-light mb-2">📍 {comp_addr}</p>
            <p class="col-md-8 fs-5 text-secondary">{t['sub_title']}</p>
            <hr class="border-secondary">
            <a href="/scada" class="btn btn-warning btn-lg fw-bold me-2 mb-2">{t['home_scada']}</a>
            <a href="/reports" class="btn btn-info btn-lg fw-bold me-2 mb-2">{t['home_reports']}</a>
            <a href="/orders" class="btn btn-outline-warning btn-lg mb-2">{t['home_orders']}</a>
        </div>
    </div>'''
    return render_page(content, t, lang)

# ==================== ЗАКАЗЫ (Ваш рабочий код) ====================
@app.route('/orders')
def orders():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        orders_list = conn.execute("SELECT o.id, o.date, c.name, v.plate_number, r.name, o.volume_m3, o.price_per_m3, (o.volume_m3 * o.price_per_m3), op.name FROM orders o JOIN clients c ON o.client_id = c.id JOIN vehicles v ON o.vehicle_id = v.id JOIN recipes r ON o.recipe_id = r.id LEFT JOIN operators op ON o.operator_id = op.id ORDER BY o.date DESC").fetchall()
        clients, vehicles, recipes, operators = get_all("clients"), get_all("vehicles"), get_all("recipes"), get_all("operators")
    
    client_opts = "".join([f"<option value='{c[0]}'>{c[1]}</option>" for c in clients])
    vehicle_opts = "".join([f"<option value='{v[0]}' data-capacity='{v[2]}'>{v[1]} ({v[2]} m³ - Tara: {v[4]} kg)</option>" for v in vehicles])
    recipe_opts = "".join([f"<option value='{r[0]}'>{r[1]}</option>" for r in recipes])
    op_opts = "".join([f"<option value='{op[0]}'>{op[1]}</option>" for op in operators])
    
    rows = ""
    for o in orders_list:
        rows += f"""<tr>
            <td>{o[0]}</td><td>{o[1][:16].replace('T', ' ')}</td><td><b>{o[2]}</b></td><td>{o[3]}</td><td>{o[4]}</td>
            <td>{o[5]} m³</td><td>{o[6]:,.2f} AZN</td><td class="text-success fw-bold">{o[7]:,.2f} AZN</td><td>{o[8] or '-'}</td>
            <td><a href='/orders/nakladnoy/{o[0]}' class='btn btn-outline-warning btn-sm' target='_blank'>📄 {t['nakladnoy']}</a></td>
        </tr>"""
    
    content = f'''
    <h2 class="text-warning mb-4">📦 {t['orders']}</h2>
    <div class="card p-4 mb-4 shadow"><form method="POST" action="/orders/add">
        <div class="row g-3">
            <div class="col-md-3"><label>{t['client']}</label><select name="client_id" class="form-select" required>{client_opts}</select></div>
            <div class="col-md-3"><label>{t['mixer']}</label><select name="vehicle_id" class="form-select" required onchange="let o=this.options[this.selectedIndex]; if(o.getAttribute('data-capacity')) document.querySelector('input[name=volume]').value=o.getAttribute('data-capacity');">{vehicle_opts}</select></div>
            <div class="col-md-2"><label>{t['recipe']}</label><select name="recipe_id" class="form-select" required>{recipe_opts}</select></div>
            <div class="col-md-2"><label>{t['volume']}</label><input type="number" step="0.5" name="volume" class="form-control" value="8.0" required></div>
            <div class="col-md-2"><label>{t['price_m3']}</label><input type="number" step="1" name="price_per_m3" class="form-control" value="110.0" required></div>
            <div class="col-md-12"><button type="submit" class="btn btn-success fw-bold w-100">{t['confirm_order']}</button></div>
        </div>
    </form></div>
    <div class="card p-3 shadow"><table class="table table-striped table-bordered align-middle text-center mb-0">
        <thead><tr><th>{t['id']}</th><th>{t['date']}</th><th>{t['client']}</th><th>{t['mixer']}</th><th>{t['recipe']}</th><th>{t['volume']}</th><th>{t['total_price']}</th><th>{t['operator']}</th><th>{t['document']}</th></tr></thead>
        <tbody>{rows}</tbody>
    </table></div>'''
    return render_page(content, t, lang)

@app.route('/orders/add', methods=['POST'])
def add_order():
    client_id = request.form.get('client_id')
    vehicle_id = request.form.get('vehicle_id')
    recipe_id = request.form.get('recipe_id')
    volume = float(request.form.get('volume') or 8.0)
    price_per_m3 = float(request.form.get('price_per_m3') or 110.0)
    operator_id = request.form.get('operator_id') or None

    with sqlite3.connect(DB) as conn:
        client_row = conn.execute("SELECT name FROM clients WHERE id=?", (client_id,)).fetchone()
        client_name = client_row[0] if client_row else "Client"
        
        cursor = conn.cursor()
        cursor.execute("INSERT INTO orders (date, client_id, vehicle_id, recipe_id, volume_m3, price_per_m3, operator_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (datetime.now().isoformat(), client_id, vehicle_id, recipe_id, volume, price_per_m3, operator_id))
        order_id = cursor.lastrowid

        recipe = conn.execute("SELECT * FROM recipes WHERE id=?", (recipe_id,)).fetchone()
        if recipe:
            consumptions = [
                ("Bunker 1", float(recipe[2] or 0) * volume), ("Bunker 2", float(recipe[3] or 0) * volume),
                ("Bunker 3", float(recipe[4] or 0) * volume), ("Bunker 4", float(recipe[5] or 0) * volume),
                ("Silo 1", float(recipe[6] or 0) * volume), ("Silo 2", float(recipe[7] or 0) * volume),
                ("Silo 3", float(recipe[8] or 0) * volume), ("Silo 4", float(recipe[9] or 0) * volume),
                ("Su", float(recipe[10] or 0) * volume)
            ]
            total_cement = (float(recipe[6] or 0) + float(recipe[7] or 0) + float(recipe[8] or 0) + float(recipe[9] or 0)) * volume
            qatki_pct = float(recipe[11]) if len(recipe) > 11 and recipe[11] is not None else 0.0
            consumptions.append(("Qatqı", (total_cement * qatki_pct) / 100.0))

            now_str = datetime.now().isoformat()
            for mat_name, qty in consumptions:
                if qty > 0:
                    conn.execute("UPDATE stock SET current_kg = MAX(0, current_kg - ?) WHERE code_name = ?", (qty, mat_name))
                    conn.execute("INSERT INTO stock_movements (date, operation_type, material_name, quantity_kg, partner_name, note) VALUES (?, 'Sərfiyyat', ?, ?, ?, ?)", (now_str, mat_name, qty, client_name, f"Order #{order_id}"))
        conn.commit()
    return redirect('/orders')

@app.route('/orders/nakladnoy/<int:id>')
def nakladnoy(id):
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        order = conn.execute("""
            SELECT o.id, o.date, c.name, c.address, v.plate_number, d.name, r.name, o.volume_m3, o.price_per_m3, (o.volume_m3 * o.price_per_m3), op.name, v.tare_weight_kg, r.bunker_1, r.bunker_2, r.bunker_3, r.bunker_4, r.silo_1, r.silo_2, r.silo_3, r.silo_4, r.water, r.qatki_percent 
            FROM orders o JOIN clients c ON o.client_id = c.id JOIN vehicles v ON o.vehicle_id = v.id LEFT JOIN drivers d ON v.driver_id = d.id JOIN recipes r ON o.recipe_id = r.id LEFT JOIN operators op ON o.operator_id = op.id WHERE o.id=?
        """, (id,)).fetchone()
        comp = conn.execute("SELECT * FROM company_info LIMIT 1").fetchone()
    
    if not order: return "Not found", 404
    comp_name, comp_addr, comp_phone, comp_tax = (comp[1], comp[2], comp[3], comp[4]) if comp else ('Industrial Automation', '', '', '')
    
    vol = float(order[7])
    tare_weight = float(order[11] or 12000.0)
    total_cement_m3 = float(order[16] or 0) + float(order[17] or 0) + float(order[18] or 0) + float(order[19] or 0)
    additive_m3 = (total_cement_m3 * float(order[21] or 1.0)) / 100.0
    weight_per_m3 = float(order[12] or 0) + float(order[13] or 0) + float(order[14] or 0) + float(order[15] or 0) + total_cement_m3 + float(order[20] or 0) + additive_m3
    concrete_total_weight = weight_per_m3 * vol
    gross_weight = tare_weight + concrete_total_weight

    qr_text = f"Plant: {comp_name} | No: {order[0]} | Date: {order[1][:10]} | Client: {order[2]} | Vol: {vol}m3 | Gross: {gross_weight:,.0f}kg"
    qr_encoded = urllib.parse.quote(qr_text)

    content = f'''
    <div class="card p-4 bg-white text-dark mx-auto my-3 shadow-sm" style="max-width: 650px; border: 2px dashed #495057 !important;">
        <div class="text-center border-bottom pb-3 mb-3">
            <h4 class="fw-bold text-dark m-0">🏗️ {comp_name}</h4>
            <small class="text-muted">📍 {comp_addr} | {t['phone_label']}: {comp_phone} | {t['tax_no']}: {comp_tax}</small>
        </div>
        <div class="d-flex justify-content-between align-items-center mb-3 bg-light p-2 rounded">
            <div><h5 class="text-primary fw-bold m-0">{t['nakladnoy']} № {order[0]}</h5><small class="text-muted">{t['date']}: {order[1][:16].replace('T', ' ')}</small></div>
            <div class="text-end"><span class="badge bg-dark fs-6">{t['mixer']}: {order[4]}</span></div>
        </div>
        <div class="mb-3 p-2 border rounded bg-white">
            <p class="mb-1"><b>{t['client']}:</b> <span class="text-dark fw-bold">{order[2]}</span></p>
            <p class="mb-0 small"><b>{t['driver_label']}:</b> {order[5] or '-'}</p>
        </div>
        <table class="table table-bordered align-middle text-center mb-3">
            <thead class="table-dark"><tr><th>{t['product_name']}</th><th>{t['volume']}</th><th>{t['price_m3']}</th><th>{t['total_price']}</th></tr></thead>
            <tbody><tr><td class="fw-bold fs-6 text-start ps-2">{order[6]}</td><td class="fw-bold fs-6 text-primary">{vol} m³</td><td>{order[8]:,.2f}</td><td class="fw-bold text-success">{order[9]:,.2f} AZN</td></tr></tbody>
        </table>
        <div class="mb-3 p-2 border rounded bg-light small">
            <div class="row text-center">
                <div class="col-4"><span>⚖️ {t['tare_weight']}:</span><br><b>{tare_weight:,.0f} kg</b></div>
                <div class="col-4"><span>📦 {t['concrete_weight']}:</span><br><b>{concrete_total_weight:,.0f} kg</b></div>
                <div class="col-4 text-success"><span>🚛 {t['gross_weight']}:</span><br><b class="fs-6">{gross_weight:,.0f} kg</b></div>
            </div>
        </div>
        <div class="text-center my-3 py-2 border-top border-bottom bg-light rounded">
            <div class="d-flex justify-content-center my-2"><img src="https://api.qrserver.com/v1/create-qr-code/?size=110x110&data={qr_encoded}" alt="QR Code"></div>
            <p class="small text-muted mt-1 mb-0 font-monospace">№ {order[0]} | {order[1][:10]}</p>
        </div>
        <div class="row mt-2 pt-2">
            <div class="col-6 text-center"><p class="mb-3 small"><b>{t['delivered_by']}</b></p><hr class="w-75 mx-auto my-1"><small class="text-muted">{order[10] or ''}</small></div>
            <div class="col-6 text-center"><p class="mb-3 small"><b>{t['received_by']}</b></p><hr class="w-75 mx-auto my-1"><small class="text-muted"></small></div>
        </div>
        <div class="text-center mt-4 d-print-none">
            <button onclick="window.print()" class="btn btn-warning btn-lg px-5 fw-bold shadow">{t['print']}</button>
            <a href="/orders" class="btn btn-secondary btn-lg px-4 ms-2">{t['back']}</a>
        </div>
    </div>'''
    return render_page(content, t, lang, hide_nav=True)

# ==================== СКЛАД (Обновлен: кто добавил, поставщик, машина) ====================
@app.route('/stock', methods=['GET', 'POST'])
def stock():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            if 'update_capacity' in request.form:
                conn.execute("UPDATE stock SET max_capacity_kg = ? WHERE id = ?", (request.form['max_capacity'], request.form['stock_id']))
            else:
                sup_id = request.form['supplier_id'] or None
                veh_id = request.form['vehicle_id'] or None
                added_by = request.form.get('added_by', 'Admin')
                mat_code = request.form['material_code']
                qty = float(request.form['quantity'])
                
                sup_name = "Unknown"
                if sup_id:
                    sup_row = conn.execute("SELECT name FROM suppliers WHERE id=?", (sup_id,)).fetchone()
                    sup_name = sup_row[0] if sup_row else "Unknown"

                conn.execute("INSERT INTO stock_income (date, supplier_id, material_code, quantity_kg, note) VALUES (?, ?, ?, ?, ?)", (datetime.now().isoformat(), sup_id, mat_code, qty, request.form.get('note', '')))
                conn.execute("UPDATE stock SET current_kg = current_kg + ?, added_by=?, supplier_id=?, vehicle_id=? WHERE code_name = ?", (qty, added_by, sup_id, veh_id, mat_code))
                conn.execute("INSERT INTO stock_movements (date, operation_type, material_name, quantity_kg, partner_name, note) VALUES (?, 'Gəliş', ?, ?, ?, ?)", (datetime.now().isoformat(), mat_code, qty, sup_name, request.form.get('note', 'Supplier In')))
            conn.commit()
            return redirect('/stock')
            
        stock_data = get_all("stock")
        suppliers = get_all("suppliers")
        vehicles = get_all("vehicles")

    sup_opts = "".join([f"<option value='{s[0]}'>{s[1]}</option>" for s in suppliers])
    veh_opts = "".join([f"<option value='{v[0]}'>{v[1]}</option>" for v in vehicles])
    mat_opts = "".join([f"<option value='{s[2]}'>{s[2]}</option>" for s in stock_data])
    
    rows = ""
    for s in stock_data:
        sup_name = ""
        veh_name = ""
        if s[6]: # supplier_id
            sr = conn.execute("SELECT name FROM suppliers WHERE id=?", (s[6],)).fetchone()
            sup_name = sr[0] if sr else "-"
        if s[7]: # vehicle_id
            vr = conn.execute("SELECT plate_number FROM vehicles WHERE id=?", (s[7],)).fetchone()
            veh_name = vr[0] if vr else "-"

        rows += f"""<tr>
            <td>{s[0]}</td><td><b>{s[1]}</b></td><td><span class='badge bg-secondary'>{s[2]}</span></td>
            <td class='text-info fw-bold'>{s[3]:,.1f} kg</td><td>{s[4]:,.1f} kg</td>
            <td>{s[5] or 'Admin'}</td><td>{sup_name}</td><td>{veh_name}</td>
            <td>
                <form method='POST' class='d-flex gap-1'>
                    <input type='hidden' name='stock_id' value='{s[0]}'><input type='hidden' name='update_capacity' value='1'>
                    <input type='number' step='100' name='max_capacity' class='form-control form-control-sm' value='{s[4]}' style='width: 110px;' required>
                    <button type='submit' class='btn btn-outline-info btn-sm'>💾</button>
                </form>
            </td>
            <td><a href='/stock/refill/{s[0]}' class='btn btn-outline-warning btn-sm'>{t['refill']}</a></td>
        </tr>"""

    content = f'''
    <h2 class="text-warning mb-4">📦 {t['stock']}</h2>
    <div class="card p-4 mb-4 shadow"><form method="POST">
        <h4 class="text-info mb-3">{t['add_stock']}</h4>
        <div class="row g-3">
            <div class="col-md-2"><label>{t['added_by']}</label><input type="text" name="added_by" class="form-control" value="Admin" required></div>
            <div class="col-md-2"><label>{t['supplier']}</label><select name="supplier_id" class="form-select"><option value="">-</option>{sup_opts}</select></div>
            <div class="col-md-2"><label>{t['vehicle']}</label><select name="vehicle_id" class="form-select"><option value="">-</option>{veh_opts}</select></div>
            <div class="col-md-2"><label>{t['material']}</label><select name="material_code" class="form-select" required>{mat_opts}</select></div>
            <div class="col-md-2"><label>{t['total_qty']} (kg)</label><input type="number" step="100" name="quantity" class="form-control" required></div>
            <div class="col-md-2"><label>{t['note']}</label><input type="text" name="note" class="form-control"></div>
        </div>
        <button type="submit" class="btn btn-success mt-3 fw-bold w-100">{t['save_stock']}</button>
    </form></div>
    <div class="card p-3 shadow"><table class="table table-striped table-bordered align-middle text-center mb-0">
        <thead><tr><th>ID</th><th>Тип</th><th>Код</th><th>{t['current_stock']}</th><th>{t['max_capacity']}</th><th>{t['added_by']}</th><th>{t['supplier']}</th><th>{t['vehicle']}</th><th>{t['action']}</th></tr></thead>
        <tbody>{rows}</tbody>
    </table></div>'''
    return render_page(content, t, lang)

@app.route('/stock/refill/<int:id>')
def refill_stock(id):
    with sqlite3.connect(DB) as conn:
        mat = conn.execute("SELECT code_name, max_capacity_kg, current_kg FROM stock WHERE id=?", (id,)).fetchone()
        diff = mat[1] - mat[2]
        if diff > 0:
            conn.execute("UPDATE stock SET current_kg = max_capacity_kg WHERE id = ?", (id,))
            conn.execute("INSERT INTO stock_movements (date, operation_type, material_name, quantity_kg, partner_name, note) VALUES (?, 'Gəliş', ?, ?, 'System', 'Full Refill')", (datetime.now().isoformat(), mat[0], diff))
            conn.commit()
    return redirect('/stock')

# ==================== РЕЦЕПТЫ И СПРАВОЧНИКИ (Ваш рабочий код) ====================
@app.route('/recipes')
def recipes():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    data = get_all("recipes")
    rows = ""
    for r in data:
        total_cement = float(r[6] or 0) + float(r[7] or 0) + float(r[8] or 0) + float(r[9] or 0)
        additive_pct = float(r[11]) if len(r) > 11 and r[11] is not None else 0.0
        additive_kg = (total_cement * additive_pct) / 100.0
        total_weight = float(r[2] or 0) + float(r[3] or 0) + float(r[4] or 0) + float(r[5] or 0) + total_cement + float(r[10] or 0) + additive_kg
        rows += f"""<tr><td>{r[0]}</td><td><b>{r[1]}</b></td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td><td>{r[6]}</td><td>{r[7]}</td><td>{r[8]}</td><td>{r[9]}</td><td>{r[10]}</td><td><span class='badge bg-info text-dark'>{additive_pct}%</span></td><td><span class='badge bg-warning text-dark'>{additive_kg:.1f} kg</span></td><td class='text-warning fw-bold'>{total_weight:,.1f} kg</td><td><a href='/recipes/edit/{r[0]}' class='btn btn-warning btn-sm me-1'>✏️</a> <a href='/recipes/delete/{r[0]}' class='btn btn-danger btn-sm'>🗑️</a></td></tr>"""
    
    content = f'''
    <h2 class="text-warning mb-4">🧪 {t['recipes']}</h2>
    <div class="card p-4 mb-4 shadow"><form method="POST" action="/recipes/add">
        <h4 class="text-info mb-3">➕ {t['add']}</h4>
        <div class="row g-3">
            <div class="col-md-4"><label>{t['recipe']}</label><input type="text" name="name" class="form-control" required></div>
            <div class="col-md-2"><label>Bunker 1</label><input type="number" step="1" name="bunker_1" class="form-control" value="0"></div>
            <div class="col-md-2"><label>Bunker 2</label><input type="number" step="1" name="bunker_2" class="form-control" value="0"></div>
            <div class="col-md-2"><label>Bunker 3</label><input type="number" step="1" name="bunker_3" class="form-control" value="0"></div>
            <div class="col-md-2"><label>Bunker 4</label><input type="number" step="1" name="bunker_4" class="form-control" value="0"></div>
            <div class="col-md-2"><label>Silo 1</label><input type="number" step="1" name="silo_1" class="form-control" value="0"></div>
            <div class="col-md-2"><label>Silo 2</label><input type="number" step="1" name="silo_2" class="form-control" value="0"></div>
            <div class="col-md-2"><label>Silo 3</label><input type="number" step="1" name="silo_3" class="form-control" value="0"></div>
            <div class="col-md-2"><label>Silo 4</label><input type="number" step="1" name="silo_4" class="form-control" value="0"></div>
            <div class="col-md-2"><label>Water</label><input type="number" step="1" name="water" class="form-control" value="0"></div>
            <div class="col-md-2"><label>Additive (%)</label><input type="number" step="0.1" name="qatki_percent" class="form-control" value="1.0"></div>
        </div>
        <button type="submit" class="btn btn-success mt-3 fw-bold w-100">{t['save']}</button>
    </form></div>
    <div class="card p-3 shadow overflow-auto"><table class="table table-striped table-bordered align-middle text-center mb-0" style="min-width: 1200px;">
        <thead><tr><th>ID</th><th>Name</th><th>B1</th><th>B2</th><th>B3</th><th>B4</th><th>S1</th><th>S2</th><th>S3</th><th>S4</th><th>W</th><th>Add(%)</th><th>Add(kg)</th><th>Total</th><th>{t['action']}</th></tr></thead>
        <tbody>{rows}</tbody>
    </table></div>'''
    return render_page(content, t, lang)

@app.route('/recipes/add', methods=['POST'])
def add_recipe():
    with sqlite3.connect(DB) as conn:
        conn.execute("INSERT INTO recipes (name, bunker_1, bunker_2, bunker_3, bunker_4, silo_1, silo_2, silo_3, silo_4, water, qatki_percent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     (request.form['name'], request.form['bunker_1'], request.form['bunker_2'], request.form['bunker_3'], request.form['bunker_4'], request.form['silo_1'], request.form['silo_2'], request.form['silo_3'], request.form['silo_4'], request.form['water'], request.form['qatki_percent']))
        conn.commit()
    return redirect('/recipes')

@app.route('/recipes/edit/<int:id>', methods=['GET', 'POST'])
def edit_recipe(id):
    lang, t = get_lang(), TRANSLATIONS[get_lang()]
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            conn.execute("UPDATE recipes SET name=?, bunker_1=?, bunker_2=?, bunker_3=?, bunker_4=?, silo_1=?, silo_2=?, silo_3=?, silo_4=?, water=?, qatki_percent=? WHERE id=?",
                         (request.form['name'], request.form['bunker_1'], request.form['bunker_2'], request.form['bunker_3'], request.form['bunker_4'], request.form['silo_1'], request.form['silo_2'], request.form['silo_3'], request.form['silo_4'], request.form['water'], request.form['qatki_percent'], id))
            conn.commit()
            return redirect('/recipes')
        r = conn.execute("SELECT * FROM recipes WHERE id=?", (id,)).fetchone()
    content = f'''<h2 class="text-warning mb-4">✏️ {t['edit']}</h2><div class="card p-4 shadow"><form method="POST"><div class="row g-3">
        <div class="col-md-4"><label>{t['recipe']}</label><input type="text" name="name" class="form-control" value="{r[1]}" required></div>
        <div class="col-md-2"><label>Bunker 1</label><input type="number" step="1" name="bunker_1" class="form-control" value="{r[2]}" required></div>
        <div class="col-md-2"><label>Bunker 2</label><input type="number" step="1" name="bunker_2" class="form-control" value="{r[3]}" required></div>
        <div class="col-md-2"><label>Bunker 3</label><input type="number" step="1" name="bunker_3" class="form-control" value="{r[4]}" required></div>
        <div class="col-md-2"><label>Bunker 4</label><input type="number" step="1" name="bunker_4" class="form-control" value="{r[5]}" required></div>
        <div class="col-md-2"><label>Silo 1</label><input type="number" step="1" name="silo_1" class="form-control" value="{r[6]}" required></div>
        <div class="col-md-2"><label>Silo 2</label><input type="number" step="1" name="silo_2" class="form-control" value="{r[7]}" required></div>
        <div class="col-md-2"><label>Silo 3</label><input type="number" step="1" name="silo_3" class="form-control" value="{r[8]}" required></div>
        <div class="col-md-2"><label>Silo 4</label><input type="number" step="1" name="silo_4" class="form-control" value="{r[9]}" required></div>
        <div class="col-md-2"><label>Water</label><input type="number" step="1" name="water" class="form-control" value="{r[10]}" required></div>
        <div class="col-md-2"><label>Additive (%)</label><input type="number" step="0.1" name="qatki_percent" class="form-control" value="{r[11] if len(r)>11 and r[11] is not None else 1.0}" required></div>
    </div><button type="submit" class="btn btn-warning mt-3 fw-bold w-100">{t['save']}</button></form></div>'''
    return render_page(content, t, lang)

@app.route('/recipes/delete/<int:id>')
def delete_recipe(id):
    with sqlite3.connect(DB) as conn:
        conn.execute("DELETE FROM recipes WHERE id = ?", (id,))
        conn.commit()
    return redirect('/recipes')

# Простые CRUD для справочников (ваш оригинальный стиль)
def crud_page(table, t_keys, t):
    lang = get_lang()
    rows = "".join([f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2] if len(r)>2 else ''}</td><td><a href='/{table}/edit/{r[0]}' class='btn btn-warning btn-sm me-1'>✏️</a> <a href='/{table}/delete/{r[0]}' class='btn btn-danger btn-sm'>🗑️</a></td></tr>" for r in get_all(table)])
    content = f'''<h2 class="text-warning mb-4">📂 {t[t_keys[0]]}</h2>
    <div class="card p-4 mb-4 shadow"><form method="POST" action="/{table}/add"><div class="row g-3">
        <div class="col-md-4"><label>Name</label><input type="text" name="name" class="form-control" required></div>
        <div class="col-md-4"><label>Contact/Phone</label><input type="text" name="contact" class="form-control" required></div>
        <div class="col-md-4"><label>Address/License</label><input type="text" name="address" class="form-control"></div>
    </div><button type="submit" class="btn btn-success mt-3">{t['add']}</button></form></div>
    <div class="card p-3 shadow"><table class="table table-striped table-bordered align-middle mb-0"><thead><tr><th>ID</th><th>Name</th><th>Info</th><th>{t['action']}</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    return render_page(content, t, lang)

@app.route('/operators')
def operators(): return crud_page("operators", ["operators"], TRANSLATIONS[get_lang()])
@app.route('/operators/add', methods=['POST'])
def add_operator():
    with sqlite3.connect(DB) as conn:
        conn.execute("INSERT INTO operators (name, phone) VALUES (?, ?)", (request.form['name'], request.form['contact']))
        conn.commit()
    return redirect('/operators')
@app.route('/operators/edit/<int:id>', methods=['GET', 'POST'])
def edit_operator(id):
    lang, t = get_lang(), TRANSLATIONS[get_lang()]
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            conn.execute("UPDATE operators SET name=?, phone=? WHERE id=?", (request.form['name'], request.form['contact'], id))
            conn.commit(); return redirect('/operators')
        op = conn.execute("SELECT * FROM operators WHERE id=?", (id,)).fetchone()
    return render_page(f'''<h2 class="text-warning mb-4">✏️ {t['edit']}</h2><div class="card p-4 col-md-6 mx-auto shadow"><form method="POST">
        <div class="mb-3"><label>Name</label><input type="text" name="name" class="form-control" value="{op[1]}" required></div>
        <div class="mb-3"><label>Phone</label><input type="text" name="contact" class="form-control" value="{op[2]}" required></div>
        <button type="submit" class="btn btn-warning w-100 fw-bold">{t['save']}</button></form></div>''', t, lang)
@app.route('/operators/delete/<int:id>')
def delete_operator(id):
    with sqlite3.connect(DB) as conn: conn.execute("DELETE FROM operators WHERE id = ?", (id,)); conn.commit()
    return redirect('/operators')

# Аналогично для clients, drivers, vehicles, suppliers (сокращено для экономии места, логика та же)
@app.route('/clients')
def clients(): return crud_page("clients", ["clients"], TRANSLATIONS[get_lang()])
@app.route('/clients/add', methods=['POST'])
def add_client():
    with sqlite3.connect(DB) as conn:
        conn.execute("INSERT INTO clients (name, contact, address) VALUES (?, ?, ?)", (request.form['name'], request.form['contact'], request.form['address']))
        conn.commit()
    return redirect('/clients')
@app.route('/clients/edit/<int:id>', methods=['GET', 'POST'])
def edit_client(id):
    lang, t = get_lang(), TRANSLATIONS[get_lang()]
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            conn.execute("UPDATE clients SET name=?, contact=?, address=? WHERE id=?", (request.form['name'], request.form['contact'], request.form['address'], id))
            conn.commit(); return redirect('/clients')
        c = conn.execute("SELECT * FROM clients WHERE id=?", (id,)).fetchone()
    return render_page(f'''<h2 class="text-warning mb-4">✏️ {t['edit']}</h2><div class="card p-4 col-md-6 mx-auto shadow"><form method="POST">
        <div class="mb-3"><label>Name</label><input type="text" name="name" class="form-control" value="{c[1]}" required></div>
        <div class="mb-3"><label>Contact</label><input type="text" name="contact" class="form-control" value="{c[2]}" required></div>
        <div class="mb-3"><label>Address</label><input type="text" name="address" class="form-control" value="{c[3]}" required></div>
        <button type="submit" class="btn btn-warning w-100 fw-bold">{t['save']}</button></form></div>''', t, lang)
@app.route('/clients/delete/<int:id>')
def delete_client(id):
    with sqlite3.connect(DB) as conn: conn.execute("DELETE FROM clients WHERE id = ?", (id,)); conn.commit()
    return redirect('/clients')

@app.route('/drivers')
def drivers(): return crud_page("drivers", ["drivers"], TRANSLATIONS[get_lang()])
@app.route('/drivers/add', methods=['POST'])
def add_driver():
    with sqlite3.connect(DB) as conn:
        conn.execute("INSERT INTO drivers (name, phone, license_number) VALUES (?, ?, ?)", (request.form['name'], request.form['contact'], request.form['address']))
        conn.commit()
    return redirect('/drivers')
@app.route('/drivers/edit/<int:id>', methods=['GET', 'POST'])
def edit_driver(id):
    lang, t = get_lang(), TRANSLATIONS[get_lang()]
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            conn.execute("UPDATE drivers SET name=?, phone=?, license_number=? WHERE id=?", (request.form['name'], request.form['contact'], request.form['address'], id))
            conn.commit(); return redirect('/drivers')
        d = conn.execute("SELECT * FROM drivers WHERE id=?", (id,)).fetchone()
    return render_page(f'''<h2 class="text-warning mb-4">✏️ {t['edit']}</h2><div class="card p-4 col-md-6 mx-auto shadow"><form method="POST">
        <div class="mb-3"><label>Name</label><input type="text" name="name" class="form-control" value="{d[1]}" required></div>
        <div class="mb-3"><label>Phone</label><input type="text" name="contact" class="form-control" value="{d[2]}" required></div>
        <div class="mb-3"><label>License</label><input type="text" name="address" class="form-control" value="{d[3]}" required></div>
        <button type="submit" class="btn btn-warning w-100 fw-bold">{t['save']}</button></form></div>''', t, lang)
@app.route('/drivers/delete/<int:id>')
def delete_driver(id):
    with sqlite3.connect(DB) as conn: conn.execute("DELETE FROM drivers WHERE id = ?", (id,)); conn.commit()
    return redirect('/drivers')

@app.route('/vehicles')
def vehicles():
    lang, t = get_lang(), TRANSLATIONS[get_lang()]
    with sqlite3.connect(DB) as conn:
        vehicles_list = conn.execute("SELECT v.id, v.plate_number, v.capacity_m3, d.name, v.tare_weight_kg FROM vehicles v LEFT JOIN drivers d ON v.driver_id = d.id").fetchall()
        drivers = get_all("drivers")
    rows = "".join([f"<tr><td>{v[0]}</td><td><b>{v[1]}</b></td><td>{v[2]} m³</td><td><span class='text-warning'>{v[4]:,.0f} kg</span></td><td>{v[3]}</td><td><a href='/vehicles/edit/{v[0]}' class='btn btn-warning btn-sm me-1'>✏️</a> <a href='/vehicles/delete/{v[0]}' class='btn btn-danger btn-sm'>🗑️</a></td></tr>" for v in vehicles_list])
    driver_opts = "".join([f"<option value='{d[0]}'>{d[1]}</option>" for d in drivers])
    content = f'''<h2 class="text-warning mb-4">🚚 {t['vehicles']}</h2>
    <div class="card p-4 mb-4 shadow"><form method="POST" action="/vehicles/add"><div class="row g-3">
        <div class="col-md-3"><label>Plate Number</label><input type="text" name="plate_number" class="form-control" required></div>
        <div class="col-md-3"><label>{t['volume']} (m³)</label><input type="number" step="0.5" name="capacity" class="form-control" required></div>
        <div class="col-md-3"><label>{t['tare_weight']} (kg)</label><input type="number" step="100" name="tare_weight" class="form-control" value="12000" required></div>
        <div class="col-md-3"><label>{t['drivers']}</label><select name="driver_id" class="form-select" required>{driver_opts}</select></div>
    </div><button type="submit" class="btn btn-success mt-3">{t['add']}</button></form></div>
    <div class="card p-3 shadow"><table class="table table-striped table-bordered align-middle text-center mb-0"><thead><tr><th>ID</th><th>Plate</th><th>Capacity</th><th>Tara</th><th>Driver</th><th>{t['action']}</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    return render_page(content, t, lang)

@app.route('/vehicles/add', methods=['POST'])
def add_vehicle():
    with sqlite3.connect(DB) as conn:
        conn.execute("INSERT INTO vehicles (plate_number, capacity_m3, driver_id, tare_weight_kg) VALUES (?, ?, ?, ?)", 
                     (request.form['plate_number'], request.form['capacity'], request.form['driver_id'], request.form.get('tare_weight', 12000.0)))
        conn.commit()
    return redirect('/vehicles')

@app.route('/vehicles/edit/<int:id>', methods=['GET', 'POST'])
def edit_vehicle(id):
    lang, t = get_lang(), TRANSLATIONS[get_lang()]
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            conn.execute("UPDATE vehicles SET plate_number=?, capacity_m3=?, driver_id=?, tare_weight_kg=? WHERE id=?", 
                         (request.form['plate_number'], request.form['capacity'], request.form['driver_id'], request.form.get('tare_weight', 12000.0), id))
            conn.commit(); return redirect('/vehicles')
        v = conn.execute("SELECT * FROM vehicles WHERE id=?", (id,)).fetchone()
        drivers = get_all("drivers")
    driver_opts = "".join([f"<option value='{d[0]}' {'selected' if d[0]==v[3] else ''}>{d[1]}</option>" for d in drivers])
    return render_page(f'''<h2 class="text-warning mb-4">✏️ {t['edit']}</h2>
    <div class="card p-4 col-md-6 mx-auto shadow"><form method="POST">
        <div class="mb-3"><label>Plate Number</label><input type="text" name="plate_number" class="form-control" value="{v[1]}" required></div>
        <div class="mb-3"><label>Capacity (m³)</label><input type="number" step="0.5" name="capacity" class="form-control" value="{v[2]}" required></div>
        <div class="mb-3"><label>Tara (kg)</label><input type="number" step="100" name="tare_weight" class="form-control" value="{v[4] if len(v)>4 and v[4] is not None else 12000}" required></div>
        <div class="mb-3"><label>Driver</label><select name="driver_id" class="form-select" required>{driver_opts}</select></div>
        <button type="submit" class="btn btn-warning w-100 fw-bold">{t['save']}</button></form></div>''', t, lang)

@app.route('/vehicles/delete/<int:id>')
def delete_vehicle(id):
    with sqlite3.connect(DB) as conn: conn.execute("DELETE FROM vehicles WHERE id = ?", (id,)); conn.commit()
    return redirect('/vehicles')

@app.route('/suppliers')
def suppliers(): return crud_page("suppliers", ["suppliers"], TRANSLATIONS[get_lang()])
@app.route('/suppliers/add', methods=['POST'])
def add_supplier():
    with sqlite3.connect(DB) as conn:
        conn.execute("INSERT INTO suppliers (name, contact) VALUES (?, ?)", (request.form['name'], request.form['contact']))
        conn.commit()
    return redirect('/suppliers')
@app.route('/suppliers/edit/<int:id>', methods=['GET', 'POST'])
def edit_supplier(id):
    lang, t = get_lang(), TRANSLATIONS[get_lang()]
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            conn.execute("UPDATE suppliers SET name=?, contact=? WHERE id=?", (request.form['name'], request.form['contact'], id))
            conn.commit(); return redirect('/suppliers')
        s = conn.execute("SELECT * FROM suppliers WHERE id=?", (id,)).fetchone()
    return render_page(f'''<h2 class="text-warning mb-4">✏️ {t['edit']}</h2><div class="card p-4 col-md-6 mx-auto shadow"><form method="POST">
        <div class="mb-3"><label>Name</label><input type="text" name="name" class="form-control" value="{s[1]}" required></div>
        <div class="mb-3"><label>Contact</label><input type="text" name="contact" class="form-control" value="{s[2]}" required></div>
        <button type="submit" class="btn btn-warning w-100 fw-bold">{t['save']}</button></form></div>''', t, lang)
@app.route('/suppliers/delete/<int:id>')
def delete_supplier(id):
    with sqlite3.connect(DB) as conn: conn.execute("DELETE FROM suppliers WHERE id = ?", (id,)); conn.commit()
    return redirect('/suppliers')

@app.route('/company', methods=['GET', 'POST'])
def company():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            conn.execute("DELETE FROM company_info")
            conn.execute("INSERT INTO company_info (name, address, phone, tax_number) VALUES (?, ?, ?, ?)", (request.form['name'], request.form['address'], request.form['phone'], request.form['tax_number']))
            conn.commit()
            return redirect('/company')
        comp = conn.execute("SELECT * FROM company_info LIMIT 1").fetchone()
    content = f'''
    <h2 class="text-warning mb-4">🏭 {t['company']}</h2>
    <div class="card p-4 col-md-6 mx-auto shadow"><form method="POST">
        <div class="mb-3"><label>{t['company_name']}</label><input type="text" name="name" class="form-control" value="{comp[1] if comp else ''}" required></div>
        <div class="mb-3"><label>{t['address']}</label><input type="text" name="address" class="form-control" value="{comp[2] if comp else ''}" required></div>
        <div class="mb-3"><label>{t['phone']}</label><input type="text" name="phone" class="form-control" value="{comp[3] if comp else ''}" required></div>
        <div class="mb-3"><label>{t['tax_no']}</label><input type="text" name="tax_number" class="form-control" value="{comp[4] if comp else ''}" required></div>
        <button type="submit" class="btn btn-warning w-100 fw-bold">{t['save']}</button>
    </form></div>'''
    return render_page(content, t, lang)

# ==================== ОТЧЕТЫ (РАЗДЕЛЕНЫ НА ОТДЕЛЬНЫЕ СТРАНИЦЫ) ====================
@app.route('/reports')
def reports():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    content = f'''
    <h2 class="text-warning mb-4">📊 {t['reports']}</h2>
    <div class="row g-4">
        <div class="col-md-6">
            <div class="card p-4 border-info h-100">
                <h4 class="text-info">🪨 {t['stock_rep']}</h4>
                <p>Приход, расход и остатки по всем материалам</p>
                <a href="/reports/stock" class="btn btn-info w-100 text-white">Открыть отчет</a>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card p-4 border-success h-100">
                <h4 class="text-success">🏗️ {t['concrete_rep']}</h4>
                <p>Производство и продажи по маркам бетона</p>
                <a href="/reports/concrete" class="btn btn-success w-100">Открыть отчет</a>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card p-4 border-primary h-100">
                <h4 class="text-primary">👥 {t['client_rep']}</h4>
                <p>Объемы и суммы отгрузок по клиентам</p>
                <a href="/reports/clients" class="btn btn-primary w-100">Открыть отчет</a>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card p-4 border-danger h-100">
                <h4 class="text-danger">🚚 {t['vehicle_rep']}</h4>
                <p>Количество рейсов и объемов по машинам и водителям</p>
                <a href="/reports/vehicles" class="btn btn-danger w-100">Открыть отчет</a>
            </div>
        </div>
    </div>'''
    return render_page(content, t, lang)

@app.route('/reports/stock')
def report_stock():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        movements = conn.execute("SELECT id, date, operation_type, material_name, quantity_kg, partner_name, note FROM stock_movements ORDER BY date DESC").fetchall()
        stock_data = conn.execute("SELECT code_name, current_kg, max_capacity_kg FROM stock").fetchall()
    
    mat_rows = "".join([f"<tr><td>{m[1][:16].replace('T', ' ')}</td><td><span class='badge {'bg-success' if m[2]=='Gəliş' or m[2]=='Приход' else 'bg-danger'}'>{m[2]}</span></td><td><b>{m[3]}</b></td><td class='fw-bold text-warning'>{m[4]:,.1f} kg</td><td>{m[5]}</td><td><small>{m[6] or '-'}</small></td></tr>" for m in movements])
    stock_rows = "".join([f"<tr><td><b>{s[0]}</b></td><td class='text-info'>{s[1]:,.1f} kg</td><td>{s[2]:,.1f} kg</td></tr>" for s in stock_data])
    
    content = f'''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="text-warning mb-0">🪨 {t['stock_rep']}</h2>
        <a href="/reports" class="btn btn-secondary">{t['back']}</a>
    </div>
    <div class="card p-4 mb-4">
        <h5 class="text-info mb-3">Текущие остатки</h5>
        <table class="table table-striped"><thead class="table-dark"><tr><th>Материал</th><th>Остаток</th><th>Макс.</th></tr></thead><tbody>{stock_rows}</tbody></table>
    </div>
    <div class="card p-4">
        <h5 class="text-warning mb-3">Движения (приход/расход)</h5>
        <table class="table table-striped"><thead class="table-dark"><tr><th>{t['date']}</th><th>Тип</th><th>Материал</th><th>Кол-во (kg)</th><th>Партнер</th><th>{t['note']}</th></tr></thead><tbody>{mat_rows if mat_rows else '<tr><td colspan="6" class="text-center">Нет данных</td></tr>'}</tbody></table>
    </div>'''
    return render_page(content, t, lang)

@app.route('/reports/concrete')
def report_concrete():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        data = conn.execute('''
            SELECT r.name, COUNT(o.id), SUM(o.volume_m3), SUM(o.volume_m3 * o.price_per_m3)
            FROM orders o LEFT JOIN recipes r ON o.recipe_id = r.id GROUP BY r.name ORDER BY SUM(o.volume_m3) DESC
        ''').fetchall()
    rows = "".join([f"<tr><td><b>{d[0] or 'Неизвестно'}</b></td><td>{d[1]}</td><td class='fw-bold text-warning'>{d[2]:,.1f} m³</td><td class='fw-bold text-success'>{d[3]:,.2f} AZN</td></tr>" for d in data])
    content = f'''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="text-warning mb-0">🏗️ {t['concrete_rep']}</h2>
        <a href="/reports" class="btn btn-secondary">{t['back']}</a>
    </div>
    <div class="card p-4">
        <table class="table table-striped"><thead class="table-dark"><tr><th>Марка бетона</th><th>Кол-во заказов</th><th>Общий объем</th><th>Общая сумма</th></tr></thead><tbody>{rows if rows else '<tr><td colspan="4" class="text-center">Нет данных</td></tr>'}</tbody></table>
    </div>'''
    return render_page(content, t, lang)

@app.route('/reports/clients')
def report_clients():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        data = conn.execute('''
            SELECT c.name, COUNT(o.id), SUM(o.volume_m3), SUM(o.volume_m3 * o.price_per_m3)
            FROM orders o LEFT JOIN clients c ON o.client_id = c.id GROUP BY c.name ORDER BY SUM(o.volume_m3 * o.price_per_m3) DESC
        ''').fetchall()
    rows = "".join([f"<tr><td><b>{d[0] or 'Неизвестно'}</b></td><td>{d[1]}</td><td class='fw-bold text-warning'>{d[2]:,.1f} m³</td><td class='fw-bold text-success'>{d[3]:,.2f} AZN</td></tr>" for d in data])
    content = f'''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="text-warning mb-0">👥 {t['client_rep']}</h2>
        <a href="/reports" class="btn btn-secondary">{t['back']}</a>
    </div>
    <div class="card p-4">
        <table class="table table-striped"><thead class="table-dark"><tr><th>Клиент</th><th>Кол-во заказов</th><th>Общий объем</th><th>Общая сумма</th></tr></thead><tbody>{rows if rows else '<tr><td colspan="4" class="text-center">Нет данных</td></tr>'}</tbody></table>
    </div>'''
    return render_page(content, t, lang)

@app.route('/reports/vehicles')
def report_vehicles():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        data = conn.execute('''
            SELECT v.plate_number, d.name, COUNT(o.id), SUM(o.volume_m3)
            FROM orders o LEFT JOIN vehicles v ON o.vehicle_id = v.id LEFT JOIN drivers d ON v.driver_id = d.id
            GROUP BY v.plate_number ORDER BY SUM(o.volume_m3) DESC
        ''').fetchall()
    rows = "".join([f"<tr><td><b>{d[0] or 'Неизвестно'}</b></td><td>{d[1] or '-'}</td><td>{d[2]}</td><td class='fw-bold text-warning'>{d[3]:,.1f} m³</td></tr>" for d in data])
    content = f'''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="text-warning mb-0">🚚 {t['vehicle_rep']}</h2>
        <a href="/reports" class="btn btn-secondary">{t['back']}</a>
    </div>
    <div class="card p-4">
        <table class="table table-striped"><thead class="table-dark"><tr><th>Машина</th><th>Водитель</th><th>Кол-во рейсов</th><th>Общий объем</th></tr></thead><tbody>{rows if rows else '<tr><td colspan="4" class="text-center">Нет данных</td></tr>'}</tbody></table>
    </div>'''
    return render_page(content, t, lang)

# ==================== SCADA (Ваш рабочий код) ====================
@app.route('/scada')
def scada():
    lang = get_lang()
    t = TRANSLATIONS[get_lang()]
    with sqlite3.connect(DB) as conn:
        recipes = conn.execute("SELECT id, name FROM recipes").fetchall()
        mixers = conn.execute("SELECT id, plate_number, capacity_m3, tare_weight_kg FROM vehicles").fetchall()
        operators = conn.execute("SELECT id, name FROM operators").fetchall()
        clients = conn.execute("SELECT id, name FROM clients").fetchall()

    recipe_opts = "".join([f"<option value='{r[0]}'>{r[1]}</option>" for r in recipes])
    mixer_opts = "".join([f"<option value='{m[0]}' data-capacity='{m[2]}'>{m[1]} ({m[2]} m³)</option>" for m in mixers])
    op_opts = "".join([f"<option value='{op[0]}'>{op[1]}</option>" for op in operators])
    client_opts = "".join([f"<option value='{c[0]}'>{c[1]}</option>" for c in clients])

    content = f'''
    <h2 class="text-warning mb-4">🖥️ {t['scada']}</h2>
    <div class="row">
        <div class="col-md-5">
            <div class="card p-4 mb-4 border-warning shadow">
                <h4 class="text-warning mb-3">⚙️ Panel</h4>
                <div class="mb-2"><label>{t['client']}</label><select id="scadaClient" class="form-select" required>{client_opts}</select></div>
                <div class="mb-2"><label>{t['recipe']}</label><select id="scadaRecipe" class="form-select">{recipe_opts}</select></div>
                <div class="mb-2"><label>{t['mixer']}</label><select id="scadaMixer" class="form-select" onchange="let o=this.options[this.selectedIndex]; if(o.getAttribute('data-capacity')) document.getElementById('scadaVolume').value=o.getAttribute('data-capacity');">{mixer_opts}</select></div>
                <div class="mb-2"><label>{t['volume']}</label><input type="number" id="scadaVolume" class="form-control" value="8.0" step="0.5"></div>
                <div class="mb-2"><label>{t['price_m3']}</label><input type="number" id="scadaPrice" class="form-control" value="110.0" step="1"></div>
                <div class="mb-3"><label>{t['operator']}</label><select id="scadaOperator" class="form-select">{op_opts}</select></div>
                <button onclick="startBatch()" class="btn btn-success btn-lg w-100 fw-bold mt-2">{t['start_prod']}</button>
                <button onclick="emergencyStop()" class="btn btn-danger btn-sm w-100 fw-bold mt-2">{t['estop']}</button>
            </div>
        </div>
        <div class="col-md-7">
            <div class="card p-4 text-center shadow">
                <h4 class="text-info mb-4">🏭 Process Status</h4>
                <div class="row mb-3">
                    <div class="col-4"><div class="p-3 border border-secondary rounded bg-dark"><small class="text-warning">{t['phase1']}</small><h6 id="phase1" class="text-secondary m-0">{t['waiting']}</h6></div></div>
                    <div class="col-4"><div class="p-3 border border-secondary rounded bg-dark"><small class="text-warning">{t['phase2']}</small><h6 id="phase2" class="text-secondary m-0">{t['waiting']}</h6></div></div>
                    <div class="col-4"><div class="p-3 border border-secondary rounded bg-dark"><small class="text-warning">{t['phase3']}</small><h6 id="phase3" class="text-secondary m-0">{t['waiting']}</h6></div></div>
                </div>
                <div class="p-4 bg-black rounded border border-secondary mb-3">
                    <h5 id="processStatus" class="text-info mb-3">{t['ready']}</h5>
                    <div class="progress" style="height: 30px;">
                        <div id="progressBar" class="progress-bar progress-bar-striped progress-bar-animated bg-warning text-dark fw-bold" style="width: 0%; font-size: 1.1rem;">0%</div>
                    </div>
                </div>
                <div id="logBox" class="p-3 bg-dark text-start border border-secondary rounded" style="height: 140px; overflow-y: auto; font-family: monospace; font-size: 0.85rem;">
                    <span class="text-muted">[00:00:00] SCADA Ready.</span><br>
                </div>
            </div>
        </div>
    </div>
    <script>
    function logMessage(msg) {{
        let box = document.getElementById("logBox");
        let time = new Date().toLocaleTimeString();
        box.innerHTML += `<span class="text-light">[${{time}}] ${{msg}}</span><br>`;
        box.scrollTop = box.scrollHeight;
    }}
    function startBatch() {{
        let client = document.getElementById("scadaClient").value;
        if (!client) {{ alert("Select client!"); return; }}
        let status = document.getElementById("processStatus");
        let bar = document.getElementById("progressBar");
        let p1 = document.getElementById("phase1");
        let p2 = document.getElementById("phase2");
        let p3 = document.getElementById("phase3");
        let volume = document.getElementById("scadaVolume").value;
        let price = document.getElementById("scadaPrice").value;
        p1.className = "text-warning fw-bold"; p1.innerText = "Dosing...";
        status.innerText = "Phase 1: Dosing materials...";
        bar.style.width = "25%"; bar.innerText = "25%";
        logMessage("Phase 1: Dosing started.");
        setTimeout(() => {{
            p1.className = "text-success fw-bold"; p1.innerText = "OK ✔️";
            p2.className = "text-warning fw-bold"; p2.innerText = "Loading...";
            status.innerText = "Phase 2: Loading to mixer...";
            bar.style.width = "55%"; bar.innerText = "55%";
            logMessage("Phase 2: Loading.");
        }}, 2000);
        setTimeout(() => {{
            p2.className = "text-success fw-bold"; p2.innerText = "OK ✔️";
            p3.className = "text-warning fw-bold"; p3.innerText = "Mixing...";
            status.innerText = "Phase 3: Mixing and discharge...";
            bar.style.width = "90%"; bar.innerText = "90%";
            logMessage("Phase 3: Mixing finished.");
        }}, 4000);
        setTimeout(() => {{
            p3.className = "text-success fw-bold"; p3.innerText = "OK ✔️";
            status.innerText = "Completed!";
            bar.style.width = "100%"; bar.innerText = "100%";
            logMessage("Order saved.");
            let formData = new FormData();
            formData.append("client_id", client);
            formData.append("vehicle_id", document.getElementById("scadaMixer").value);
            formData.append("recipe_id", document.getElementById("scadaRecipe").value);
            formData.append("volume", volume);
            formData.append("price_per_m3", price);
            formData.append("operator_id", document.getElementById("scadaOperator").value);
            fetch("/orders/add", {{ method: "POST", headers: {{ "X-Requested-With": "XMLHttpRequest" }}, body: formData }}).then(res => {{ setTimeout(() => {{ window.location.href = "/orders"; }}, 1000); }});
        }}, 6000);
    }}
    function emergencyStop() {{
        document.getElementById("processStatus").innerText = "🛑 ESTOP!";
        document.getElementById("progressBar").className = "progress-bar bg-danger fw-bold";
        document.getElementById("progressBar").innerText = "STOP";
        logMessage("🚨 E-STOP!");
    }}
    </script>'''
    return render_page(content, t, lang)

# ==================== SYSTEM TRAY (Ваш рабочий код) ====================
def create_tray_icon():
    image = Image.new('RGB', (64, 64), color="#1d232a")
    dc = ImageDraw.Draw(image)
    dc.rectangle((16, 16, 48, 48), fill="#ffc107")
    return image

def open_browser(icon, item):
    webbrowser.open("http://127.0.0.1:5050/")

def exit_app(icon, item):
    icon.stop()
    os._exit(0)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    
    # Запуск в отдельном потоке, чтобы не блокировать трей
    def run_flask():
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Даем Flask секунду на старт перед открытием браузера
    import time
    time.sleep(1.5)
    webbrowser.open(f"http://127.0.0.1:{port}/")

    icon = pystray.Icon("beton_zavod", create_tray_icon(), "Beton Zavod SCADA")
    menu = pystray.Menu(
        pystray.MenuItem("Open Dashboard", open_browser),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit", exit_app)
    )
    icon.run()
