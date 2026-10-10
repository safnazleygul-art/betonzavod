from flask import Flask, render_template_string, request, redirect, session, url_for, jsonify, Response
import sqlite3
import urllib.parse
from datetime import datetime, timedelta
import os
import csv
import io
import codecs

app = Flask(__name__)
app.secret_key = "beton_zavod_secret_key"
DB = "batch_dosing.db"

TRANSLATIONS = {
    "az": {
        "title": "Beton Zavod SCADA",
        "home": "Əsas səhifə",
        "orders": "Sifarişlər və Qaimələr",
        "recipes": "Reseptlər",
        "stock": "Anbar və Xammal",
        "reports": "Hesabatlar və Axtarış",
        "scada": "SCADA Pult",
        "settings": "PLC Tənzimləmələri",
        "modbus": "Modbus Xritələmə",
        "directories": "Sorğular",
        "drivers": "Sürücülər",
        "vehicles": "Mikserlər",
        "clients": "Müştərilər",
        "suppliers": "Təchizatçılar",
        "operators": "Operatorlar",
        "company": "Müəssisə",
        "lang_name": "Azərbaycan dili",
        "home_scada": "🖥️ SCADA Pult & Start",
        "home_reports": "📊 Hesabatlar və Axtarış",
        "home_orders": "📦 Sifarişlər",
        "delete": "Sil", "edit": "Redaktə", "add": "Əlavə et", "save": "Yadda saxla",
        "print_version": "Çap Versiyası", "export_csv": "📥 CSV/Excel İxrac", "back": "Geri qayıt", "nakladnoy": "Nəqliyyat Qaiməsi",
        "sub_title": "SCADA və Beton Zavod İdarəetmə Sistemi (Daşınma Uçotu, Anbar, Reseptlər, Modbus)",
        "client": "Müştəri (Alıcı)",
        "mixer": "Mikser (Maşın)",
        "recipe": "Resept / Beton Markası",
        "volume": "Həcm (m³)",
        "price_m3": "1 m³ Qiyməti (AZN)",
        "total_price": "Ümumi Məbləğ",
        "operator": "Operator",
        "confirm_order": "💾 Sifarişi Təsdiq Et və Anbardan Çıx",
        "id": "ID", "date": "Tarix", "document": "Sənəd", "action": "Əməliyyat",
        "start_date": "Başlanğıc tarixi", "end_date": "Bitmə tarixi",
        "material": "Material / Silo / Su",
        "op_type": "Əməliyyat Növü",
        "all_materials": "Bütün Materiallar",
        "all_silos": "🪨 Bütün Silolar (Silo 1-4)",
        "all_recipes": "Bütün Markalar",
        "all_ops": "Bütün Əməliyyatlar",
        "all_clients": "Bütün Müştərilər",
        "all_drivers": "Bütün Sürücülər",
        "consumption": "Sərfiyyat",
        "income": "Gəliş",
        "search": "🔍 Axtar və Göstər",
        "total_volume": "Ümumi Həcm",
        "total_qty": "Ümumi Miqdar",
        "total_amount": "Ümumi Məbləğ",
        "driver_rep": "🚚 Sürücülər Üzrə Daşınma Hesabatı",
        "client_rep": "🏢 Müştərilər Üzrə Beton Paylanması",
        "trips": "Reys Sayı",
        "order_count": "Sifariş Sayı",
        "note": "Qeyd / Qaimə",
        "supplier": "Təchizatçı (Kimdən gəldi)",
        "add_stock": "📥 Yeni Xammal Girişi",
        "save_stock": "💾 Anbara Daxil Et",
        "current_stock": "Cari Qalıq",
        "max_capacity": "Max Tutum",
        "refill": "➕ Dolu",
        "start_prod": "▶️ İstehsalı Başla (START)",
        "estop": "🛑 QƏZA DAYANMASI (ESTOP)",
        "phase1": "1. Dozaj", "phase2": "2. Yükləmə", "phase3": "3. Zames & Sliv",
        "ready": "Hazırdır", "waiting": "Gözləyir",
        "phone": "Telefon", "license": "Sürücülük Vəsiqəsi", "address": "Ünvan", "tax_no": "VÖEN",
        "company_name": "Müəssisə Adı",
        "close": "Bağla", "print": "🖨️ Çap Et",
        "delivered_by": "Təhvil Verən Operator",
        "received_by": "Təhvil Alan Məhsul Yiyəsi",
        "product_name": "Məhsulun Adı və Markası",
        "phone_label": "Tel",
        "address_label": "Ünvan",
        "driver_label": "Sürücü",
        "tare_weight": "Boş Çəki (Tara)",
        "concrete_weight": "Betonun Çəkisi",
        "gross_weight": "Ümumi Dolu Çəki (Brutto)",
        "mixing_time": "Qarışdırma Müddəti (san)",
        "gate_open_time": "Qapağın Açılma Vaxtı (san)",
        "gate_pulse_period": "Qapaq İmpuls Periodu (san)",
        "discharge_time": "Boşalma Vaxtı (san)",
        "transporter_stop_delay": "Lent Dayanma Gecikməsi (san)"
    },
    "tr": {
        "title": "Beton Santrali SCADA",
        "home": "Ana Sayfa",
        "orders": "Siparişler ve İrsaliyeler",
        "recipes": "Reçeteler",
        "stock": "Stok ve Hammadde",
        "reports": "Raporlar ve Arama",
        "scada": "SCADA Kontrol",
        "settings": "PLC Ayarları",
        "modbus": "Modbus Haritalama",
        "directories": "Tanımlamalar",
        "drivers": "Şoförler",
        "vehicles": "Mikseller",
        "clients": "Müşteriler",
        "suppliers": "Tedarikçiler",
        "operators": "Operatörler",
        "company": "İşletme",
        "lang_name": "Türkçe",
        "home_scada": "🖥️ SCADA Kontrol & Başlat",
        "home_reports": "📊 Raporlar ve Arama",
        "home_orders": "📦 Siparişler",
        "delete": "Sil", "edit": "Düzenle", "add": "Ekle", "save": "Kaydet",
        "print_version": "Yazdırılabilir Sayfa",
        "export_csv": "📥 CSV/Excel İhracat",
        "back": "Geri Dön",
        "nakladnoy": "Sevk İrsaliyesi",
        "sub_title": "SCADA ve Beton Santral Yönetim Sistemi (Taşıma Takibi, Stok, Reçeteler, Modbus)",
        "client": "Müşteri (Firma)",
        "mixer": "Mikser (Araç)",
        "recipe": "Reçete / Beton Sınıfı",
        "volume": "Hacim (m³)",
        "price_m3": "1 m³ Fiyatı (AZN)",
        "total_price": "Toplam Tutar",
        "operator": "Operatör",
        "confirm_order": "💾 Siparişi Onayla ve Stoktan Düş",
        "id": "ID", "date": "Tarih", "document": "Belge", "action": "İşlem",
        "start_date": "Başlangıç Tarihi", "end_date": "Bitiş Tarihi",
        "material": "Malzeme / Silo / Su",
        "op_type": "İşlem Tipi",
        "all_materials": "Tüm Malzemeler",
        "all_silos": "🪨 Tüm Silolar (Silo 1-4)",
        "all_recipes": "Tüm Reçeteler",
        "all_ops": "Tüm İşlemler",
        "all_clients": "Tüm Müşteriler",
        "all_drivers": "Tüm Şoförler",
        "consumption": "Sarfiyat",
        "income": "Giriş",
        "search": "🔍 Ara ve Göster",
        "total_volume": "Toplam Hacim",
        "total_qty": "Toplam Miktar",
        "total_amount": "Toplam Tutar",
        "driver_rep": "🚚 Şoför Bazlı Taşıma Raporu",
        "client_rep": "🏢 Müşteri Bazlı Beton Dağılımı",
        "trips": "Sefer Sayısı",
        "order_count": "Sipariş Sayısı",
        "note": "Açıklama / İrsaliye",
        "supplier": "Tedarikçi",
        "add_stock": "📥 Yeni Hammadde Girişi",
        "save_stock": "💾 Stoga Ekle",
        "current_stock": "Mevcut Stok",
        "max_capacity": "Maks Kapasite",
        "refill": "➕ Doldur",
        "start_prod": "▶️ Üretimi Başlat (START)",
        "estop": "🛑 ACİL DURDURMA (ESTOP)",
        "phase1": "1. Dozaj", "phase2": "2. Yükleme", "phase3": "3. Karıştırma ve Deşarj",
        "ready": "Hazır", "waiting": "Bekliyor",
        "phone": "Telefon", "license": "Ehliyet No", "address": "Adres", "tax_no": "Vergi No",
        "company_name": "Firma Adı",
        "close": "Kapat",
        "print": "🖨️ Yazdır",
        "delivered_by": "Teslim Eden Operatör",
        "received_by": "Teslim Alan Müşteri",
        "product_name": "Ürün Adı ve Sınıfı",
        "phone_label": "Tel",
        "address_label": "Adres",
        "driver_label": "Şoför",
        "tare_weight": "Dara (Boş Ağırlık)",
        "concrete_weight": "Beton Ağırlığı",
        "gross_weight": "Toplam Yüklü Ağırlık (Brüt)",
        "mixing_time": "Karıştırma Süresi (sn)",
        "gate_open_time": "Kapak Açılma Süresi (sn)",
        "gate_pulse_period": "Kapak Darbe Periyodu (sn)",
        "discharge_time": "Boşaltma Süresi (sn)",
        "transporter_stop_delay": "Bant Durma Gecikmesi (sn)"
    },
    "ru": {
        "title": "Бетонный Завод SCADA",
        "home": "Главная",
        "orders": "Заказы и Накладные",
        "recipes": "Рецепты",
        "stock": "Склад и Сырье",
        "reports": "Отчеты и Поиск",
        "scada": "SCADA Пульт",
        "settings": "Настройки ПЛК",
        "modbus": "Modbus Карты",
        "directories": "Справочники",
        "drivers": "Водители",
        "vehicles": "Миксеры",
        "clients": "Клиенты",
        "suppliers": "Поставщики",
        "operators": "Операторы",
        "company": "Предприятие",
        "lang_name": "Русский",
        "home_scada": "🖥️ SCADA Пульт & Старт",
        "home_reports": "📊 Отчеты и Поиск",
        "home_orders": "📦 Заказы",
        "delete": "Удалить", "edit": "Править", "add": "Добавить", "save": "Сохранить",
        "print_version": "Версия для печати",
        "export_csv": "📥 Экспорт в CSV/Excel",
        "back": "Назад",
        "nakladnoy": "Товарно-Транспортная Накладная",
        "sub_title": "SCADA и Система Управления Бетонным Заводом (Учет Перевозок Водителей, Склад, Рецепты, Modbus)",
        "client": "Клиент (Заказчик)",
        "mixer": "Миксер (Машина)",
        "recipe": "Рецепт / Марка Бетона",
        "volume": "Объем (м³)",
        "price_m3": "Цена за 1 м³ (AZN)",
        "total_amount": "Общая Сумма",
        "operator": "Оператор",
        "confirm_order": "💾 Подтвердить Заказ и Списать со Склада",
        "id": "ID", "date": "Дата", "document": "Документ", "action": "Действие",
        "start_date": "Дата начала", "end_date": "Дата окончания",
        "material": "Материал / Силос / Вода",
        "op_type": "Тип Операции",
        "all_materials": "Все Материалы",
        "all_silos": "🪨 Все Силосы (Силос 1-4)",
        "all_recipes": "Все Марки",
        "all_ops": "Все Операции",
        "all_clients": "Все Клиенты",
        "all_drivers": "Все Водители",
        "consumption": "Расход",
        "income": "Приход",
        "search": "🔍 Найти и Показать",
        "total_volume": "Общий Объем",
        "total_qty": "Общее Количество",
        "total_amount": "Общая Сумма",
        "driver_rep": "🚚 Отчет Перевозок по Водителям",
        "client_rep": "🏢 Распределение Бетона по Клиентам",
        "trips": "Кол-во Рейсов",
        "order_count": "Кол-во Заказов",
        "note": "Примечание / Накладная",
        "supplier": "Поставщик",
        "add_stock": "📥 Поступление Нового Сырья",
        "save_stock": "💾 Внести на Склад",
        "current_stock": "Текущий Остаток",
        "max_capacity": "Макс Емкость",
        "refill": "➕ Заполнить",
        "start_prod": "▶️ Начать Производство (START)",
        "estop": "🛑 АВАРИЙНЫЙ ОСТАНОВ (ESTOP)",
        "phase1": "1. Дозирование", "phase2": "2. Загрузка", "phase3": "3. Замес и Слив",
        "ready": "Готов", "waiting": "Ожидание",
        "phone": "Телефон", "license": "Водительское Удостоверение", "address": "Адрес", "tax_no": "ИНН/VÖEN",
        "company_name": "Название Предприятия",
        "close": "Закрыть",
        "print": "🖨️ Печать",
        "delivered_by": "Сдал (Оператор)",
        "received_by": "Принял (Заказчик)",
        "product_name": "Наименование и Марка Продукции",
        "phone_label": "Тел",
        "address_label": "Адрес",
        "driver_label": "Водитель",
        "tare_weight": "Масса пустого авто (Тара)",
        "concrete_weight": "Масса бетона",
        "gross_weight": "Общая масса с грузом (Брутто)",
        "mixing_time": "Время перемешивания (сек)",
        "gate_open_time": "Время открытия затвора (сек)",
        "gate_pulse_period": "Период импульса затвора (сек)",
        "discharge_time": "Время выгрузки (сек)",
        "transporter_stop_delay": "Задержка остановки ленты (сек)"
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
        try:
            conn.execute("ALTER TABLE vehicles ADD COLUMN tare_weight_kg REAL DEFAULT 12000.0")
        except sqlite3.OperationalError:
            pass

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

        conn.execute('''CREATE TABLE IF NOT EXISTS stock_income (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, supplier_id INTEGER, 
            material_code TEXT, quantity_kg REAL, note TEXT
        )''')

        conn.execute('''CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, operation_type TEXT, material_name TEXT, 
            quantity_kg REAL, partner_name TEXT, note TEXT
        )''')

        conn.execute('''CREATE TABLE IF NOT EXISTS modbus_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plc_ip TEXT DEFAULT '192.168.1.50',
            plc_port INTEGER DEFAULT 502,
            slave_id INTEGER DEFAULT 1
        )''')

        conn.execute('''CREATE TABLE IF NOT EXISTS modbus_registers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_name TEXT,
            data_type TEXT,
            address INTEGER,
            description TEXT
        )''')

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM company_info")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO company_info (name, address, phone, tax_number) VALUES (?, ?, ?, ?)",
                           ("Industrial Automation", "Sanqaçal 70 il oktyar küç. 17/15", "+994 55 856 55 06", "9900123456"))
            
            cursor.execute("INSERT INTO factory_settings (mixer_capacity_m3, mixing_time_sec, gate_open_time_sec, gate_pulse_period_sec, discharge_time_sec, transporter_stop_delay_sec, inter_hopper_open_sec, cement_delay_sec, water_delay_sec, additive_delay_sec) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (2.0, 45.0, 5.0, 1.0, 30.0, 3.5, 4.0, 2.0, 1.0, 1.5))

            cursor.executemany("INSERT INTO operators (name, phone) VALUES (?, ?)", [
                ("Mürad İbrahimov", "+994558565506"), ("Elşən Məmmədov", "+994502223344"), ("Kamran Hüseynov", "+994553334455")
            ])
            cursor.executemany("INSERT INTO drivers (name, phone, license_number) VALUES (?, ?, ?)", [
                ("Məmməd Məmmədov", "+994501112233", "AZ-99-123"), ("Elçin Qasımov", "+994552223344", "AZ-10-456"), ("Rəşad Quliyev", "+994703335566", "AZ-50-789")
            ])
            cursor.executemany("INSERT INTO vehicles (plate_number, capacity_m3, driver_id, tare_weight_kg) VALUES (?, ?, ?, ?)", [
                ("10-AA-201", 10.0, 1, 12500.0), ("90-BX-555", 12.0, 2, 13200.0), ("77-XF-888", 8.0, 3, 11000.0)
            ])
            cursor.executemany("INSERT INTO clients (name, contact, address) VALUES (?, ?, ?)", [
                ("Aqrar Tikinti MMC", "+994125554433", "Bakı ş., Ziya Bünyadov pr."),
                ("Crystal Absheron", "+994124443322", "Xırdalan ş., Heydər Əliyev pr."),
                ("Mega City Construction", "+994127778899", "Bakı ş., Badamdar qəs.")
            ])
            cursor.executemany("INSERT INTO suppliers (name, contact) VALUES (?, ?)", [
                ("Holcim Azərbaycan", "+994126990000"), ("Norm Sement", "+994124250000"), ("Bakı Arakəsmə və Qatqı Mərkəzi", "+994123332211")
            ])
            
            stock_data = [
                ('AGGREGATE', 'Bunker 1', 85000.0, 100000.0), ('AGGREGATE', 'Bunker 2', 72000.0, 100000.0),
                ('AGGREGATE', 'Bunker 3', 94000.0, 120000.0), ('AGGREGATE', 'Bunker 4', 88000.0, 120000.0),
                ('CEMENT', 'Silo 1', 45000.0, 60000.0), ('CEMENT', 'Silo 2', 32000.0, 60000.0),
                ('CEMENT', 'Silo 3', 15000.0, 40000.0), ('CEMENT', 'Silo 4', 20000.0, 50000.0),
                ('WATER', 'Su', 50000.0, 50000.0), ('ADDITIVE', 'Qatqı', 5000.0, 10000.0)
            ]
            cursor.executemany("INSERT INTO stock (material_type, code_name, current_kg, max_capacity_kg) VALUES (?, ?, ?, ?)", stock_data)

            recipes_data = [
                ("M-200 (B15)", 450, 320, 210, 160, 200, 50, 0, 0, 180, 1.0),
                ("M-250 (B20)", 400, 300, 200, 150, 250, 50, 0, 0, 175, 1.5),
                ("M-300 (B22.5)", 450, 350, 250, 150, 300, 100, 0, 0, 165, 2.0),
                ("M-400 (B30)", 500, 400, 300, 200, 400, 100, 50, 0, 155, 2.5)
            ]
            cursor.executemany("INSERT INTO recipes (name, bunker_1, bunker_2, bunker_3, bunker_4, silo_1, silo_2, silo_3, silo_4, water, qatki_percent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", recipes_data)
            
            if os.path.exists('shabran.gpf.csv'):
                try:
                    mod_records = []
                    with codecs.open('shabran.gpf.csv', 'r', encoding='utf-16le') as f:
                        reader = csv.reader(f, delimiter='\t')
                        next(reader, None)
                        next(reader, None)
                        for row in reader:
                            if len(row) >= 6:
                                tag = row[0].strip(' "')
                                if not tag: continue
                                try:
                                    addr_type = int(row[3].strip(' "')) if row[3].strip(' "').isdigit() else 0
                                    addr = int(row[5].strip(' "')) if row[5].strip(' "').isdigit() else 0
                                except ValueError:
                                    addr_type, addr = 0, 0
                                dtype = "BIT" if addr_type == 1 else "REGISTER"
                                mod_records.append((tag, dtype, addr, f"Shabran GPF Tag (Type: {addr_type})"))
                    if mod_records:
                        cursor.executemany("INSERT INTO modbus_registers (tag_name, data_type, address, description) VALUES (?, ?, ?, ?)", mod_records)
                except Exception as e:
                    print("Error loading shabran.gpf.csv:", e)

            cursor.execute("INSERT INTO modbus_settings (plc_ip, plc_port, slave_id) VALUES ('192.168.1.50', 502, 1)")

            now = datetime.now()
            orders_data = [
                ((now - timedelta(days=3)).isoformat(), 1, 1, 1, 10.0, 110.0, 1),
                ((now - timedelta(days=2)).isoformat(), 2, 2, 2, 12.0, 110.0, 2),
                ((now - timedelta(days=1)).isoformat(), 3, 3, 3, 8.0, 120.0, 1),
                (now.isoformat(), 1, 2, 4, 16.0, 120.0, 3)
            ]
            for od in orders_data:
                cursor.execute("INSERT INTO orders (date, client_id, vehicle_id, recipe_id, volume_m3, price_per_m3, operator_id) VALUES (?, ?, ?, ?, ?, ?, ?)", od)
            conn.commit()

init_db()

def get_lang():
    if 'lang' not in session: session['lang'] = 'az'
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
        <nav class="navbar navbar-expand-md navbar-dark bg-dark border-bottom border-secondary mb-4 shadow px-3 d-print-none">
          <div class="container-fluid">
            <a class="navbar-brand text-warning fw-bold fs-5" href="/">🏗️ {comp_name}</a>
            <button class="navbar-toggler border-secondary" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
              <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
              <ul class="navbar-nav me-auto mb-2 mb-md-0 align-items-md-center">
                <li class="nav-item"><a class="nav-link" href="/">{t['home']}</a></li>
                <li class="nav-item"><a class="nav-link" href="/orders">{t['orders']}</a></li>
                <li class="nav-item"><a class="nav-link" href="/recipes">{t['recipes']}</a></li>
                <li class="nav-item"><a class="nav-link" href="/stock">{t['stock']}</a></li>
                <li class="nav-item"><a class="nav-link" href="/reports">{t['reports']}</a></li>
                <li class="nav-item"><a class="nav-link text-warning fw-bold" href="/scada">🖥️ {t['scada']}</a></li>
                <li class="nav-item"><a class="nav-link text-info fw-bold" href="/settings">⚙️ {t['settings']}</a></li>
                <li class="nav-item"><a class="nav-link text-danger fw-bold" href="/modbus">🔌 {t['modbus']}</a></li>
                <li class="nav-item dropdown ms-md-2">
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
                    <li><a class="dropdown-item" href="/set_lang/az">🇦🇿 Azərbaycan dili</a></li>
                    <li><a class="dropdown-item" href="/set_lang/tr">🇹🇷 Türkçe</a></li>
                    <li><a class="dropdown-item" href="/set_lang/ru">🇷🇺 Русский</a></li>
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
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{t['title']}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #121619; color: #e9ecef; }}
            .card {{ background-color: #1d232a; border: 1px solid #2f363d; color: #e9ecef; }}
            .table {{ color: #e9ecef; font-size: 0.9rem; }}
            .table-striped > tbody > tr:nth-of-type(odd) {{ color: #e9ecef; background-color: #181d22; }}
            .form-control, .form-select {{ background-color: #262d35; color: #fff; border: 1px solid #3d4650; }}
            .form-control:focus, .form-select:focus {{ background-color: #262d35; color: #fff; border-color: #ffc107; box-shadow: 0 0 0 0.25rem rgba(255, 193, 7, 0.25); }}
            label {{ font-size: 0.8rem; font-weight: bold; color: #ffc107; margin-bottom: 2px; }}
            @media print {{
                body {{ background-color: #fff !important; color: #000 !important; }}
                .card {{ background-color: #fff !important; color: #000 !important; border: 1px solid #000 !important; box-shadow: none !important; }}
                .table {{ color: #000 !important; }}
                .table-striped > tbody > tr:nth-of-type(odd) {{ background-color: #f8f9fa !important; color: #000 !important; }}
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
                conn.execute("INSERT INTO modbus_registers (tag_name, data_type, address, description) VALUES (?, ?, ?, ?)",
                           (request.form['tag_name'], request.form['data_type'], request.form['address'], request.form['description']))
            elif 'upload_csv' in request.files or 'upload_csv' in request.form:
                file = request.files.get('upload_csv')
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
                            if len(row) >= 6:
                                tag = row[0].strip(' "')
                                if not tag: continue
                                try:
                                    addr_type = int(row[3].strip(' "')) if row[3].strip(' "').isdigit() else 0
                                    addr = int(row[5].strip(' "')) if row[5].strip(' "').isdigit() else 0
                                except ValueError:
                                    addr_type, addr = 0, 0
                                dtype = "BIT" if addr_type == 1 else "REGISTER"
                                conn.execute("INSERT INTO modbus_registers (tag_name, data_type, address, description) VALUES (?, ?, ?, ?)",
                                           (tag, dtype, addr, f"Imported CSV Tag (Type: {addr_type})"))
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
        type_badge = "<span class='badge bg-warning text-dark'>REGISTER</span>" if r[2] == "REGISTER" else "<span class='badge bg-info text-dark'>BIT (Coil)</span>"
        rows += f"""<tr>
            <td>{r[0]}</td>
            <td><b>{r[1]}</b></td>
            <td>{type_badge}</td>
            <td class='font-monospace text-warning fw-bold'>{r[3]}</td>
            <td>{r[4]}</td>
            <td>
                <a href='/modbus/edit/{r[0]}' class='btn btn-warning btn-sm me-1'>✏️ {t['edit']}</a>
                <a href='/modbus/delete/{r[0]}' class='btn btn-danger btn-sm' onclick="return confirm('Silmek istediyinizden əminsiniz?')">🗑️ {t['delete']}</a>
            </td>
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
                <h4 class="text-success mb-3">📁 CSV Faylı Yüklə</h4>
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="upload_csv" value="1">
                    <div class="mb-3">
                        <label class="form-label text-success">Shabran GPF CSV Faylı (.csv)</label>
                        <input type="file" name="upload_csv" class="form-control" accept=".csv" required>
                    </div>
                    <button type="submit" class="btn btn-success w-100 fw-bold">📥 Faylı Seç və Yüklə</button>
                </form>
            </div>
        </div>
        
        <div class="col-md-8">
            <div class="card p-4 shadow border-warning">
                <h4 class="text-warning mb-3">➕ Add Tag / Address</h4>
                <form method="POST">
                    <input type="hidden" name="add_tag" value="1">
                    <div class="row">
                        <div class="col-md-6 mb-2">
                            <label>Tag Name</label>
                            <input type="text" name="tag_name" class="form-control" placeholder="e.g. Bunker1_Weight" required>
                        </div>
                        <div class="col-md-6 mb-2">
                            <label>Type</label>
                            <select name="data_type" class="form-select">
                                <option value="REGISTER">REGISTER (Holding / 16-bit)</option>
                                <option value="BIT">BIT (Coil / 1-bit)</option>
                            </select>
                        </div>
                        <div class="col-md-6 mb-2">
                            <label>Address Offset</label>
                            <input type="number" name="address" class="form-control" placeholder="e.g. 40001 or 0" required>
                        </div>
                        <div class="col-md-6 mb-2">
                            <label>Description</label>
                            <input type="text" name="description" class="form-control" placeholder="e.g. Bunker 1 Load Cell Value">
                        </div>
                    </div>
                    <button type="submit" class="btn btn-warning w-100 fw-bold mt-2">{t['add']}</button>
                </form>
            </div>
        </div>
    </div>

    <div class="card p-4 shadow border-secondary">
        <h4 class="text-light mb-3">📋 Registered Modbus Tags</h4>
        <div class="table-responsive">
            <table class="table table-striped table-hover align-middle">
                <thead>
                    <tr class="table-dark">
                        <th>ID</th>
                        <th>Tag Name</th>
                        <th>Type</th>
                        <th>Address</th>
                        <th>Description</th>
                        <th>{t['action']}</th>
                    </tr>
                </thead>
                <tbody>
                    {rows if rows else "<tr><td colspan='6' class='text-center text-muted'>Heç bir registr tapılmadı.</td></tr>"}
                </tbody>
            </table>
        </div>
    </div>
    '''
    return render_page(content, t, lang)

@app.route('/orders')
def orders():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        orders_list = conn.execute('''
            SELECT o.id, o.date, c.name, v.plate_number, r.name, o.volume_m3, o.price_per_m3, (o.volume_m3 * o.price_per_m3), op.name, o.status
            FROM orders o
            LEFT JOIN clients c ON o.client_id = c.id
            LEFT JOIN vehicles v ON o.vehicle_id = v.id
            LEFT JOIN recipes r ON o.recipe_id = r.id
            LEFT JOIN operators op ON o.operator_id = op.id
            ORDER BY o.date DESC
        ''').fetchall()
    
    rows = ""
    for o in orders_list:
        rows += f"""<tr>
            <td>{o[0]}</td>
            <td>{o[1][:16]}</td>
            <td><b>{o[2]}</b></td>
            <td>{o[3]}</td>
            <td>{o[4]}</td>
            <td>{o[5]} m³</td>
            <td>{o[6]} AZN</td>
            <td class='text-warning fw-bold'>{o[7]} AZN</td>
            <td>{o[8]}</td>
            <td><span class='badge bg-success'>{o[9]}</span></td>
        </tr>"""

    content = f'''
    <h2 class="text-warning mb-4">📦 {t['orders']}</h2>
    <div class="card p-4 shadow">
        <div class="table-responsive">
            <table class="table table-striped table-hover align-middle">
                <thead>
                    <tr class="table-dark">
                        <th>{t['id']}</th>
                        <th>{t['date']}</th>
                        <th>{t['client']}</th>
                        <th>{t['mixer']}</th>
                        <th>{t['recipe']}</th>
                        <th>{t['volume']}</th>
                        <th>{t['price_m3']}</th>
                        <th>{t['total_price']}</th>
                        <th>{t['operator']}</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows if rows else "<tr><td colspan='10' class='text-center text-muted'>Sifariş yoxdur.</td></tr>"}
                </tbody>
            </table>
        </div>
    </div>
    '''
    return render_page(content, t, lang)

@app.route('/recipes')
def recipes():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    recipes_list = get_all('recipes')
    rows = ""
    for r in recipes_list:
        rows += f"""<tr>
            <td>{r[0]}</td>
            <td><b>{r[1]}</b></td>
            <td>{r[2]} kq</td>
            <td>{r[3]} kq</td>
            <td>{r[4]} kq</td>
            <td>{r[5]} kq</td>
            <td>{r[6]} kq</td>
            <td>{r[7]} kq</td>
            <td>{r[8]} kq</td>
            <td>{r[9]} kq</td>
            <td>{r[10]} lt</td>
            <td>{r[11]} %</td>
        </tr>"""
    content = f'''
    <h2 class="text-warning mb-4">🧪 {t['recipes']}</h2>
    <div class="card p-4 shadow">
        <div class="table-responsive">
            <table class="table table-striped table-hover align-middle">
                <thead>
                    <tr class="table-dark">
                        <th>ID</th>
                        <th>Marka / Ad</th>
                        <th>Bunker 1</th>
                        <th>Bunker 2</th>
                        <th>Bunker 3</th>
                        <th>Bunker 4</th>
                        <th>Silo 1</th>
                        <th>Silo 2</th>
                        <th>Silo 3</th>
                        <th>Silo 4</th>
                        <th>Su</th>
                        <th>Qatqı</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>'''
    return render_page(content, t, lang)

@app.route('/stock')
def stock():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    stock_list = get_all('stock')
    rows = ""
    for s in stock_list:
        pct = min(100, max(0, int((s[3] / s[4]) * 100))) if s[4] > 0 else 0
        color = "bg-success" if pct > 30 else "bg-warning" if pct > 15 else "bg-danger"
        rows += f"""<tr>
            <td>{s[0]}</td>
            <td><span class='badge bg-secondary'>{s[1]}</span></td>
            <td><b>{s[2]}</b></td>
            <td class='text-warning fw-bold'>{s[3]:,.1f} kq</td>
            <td>{s[4]:,.1f} kq</td>
            <td style='width: 250px;'>
                <div class='progress bg-dark' style='height: 20px;'>
                    <div class='progress-bar {color}' role='progressbar' style='width: {pct}%;'>{pct}%</div>
                </div>
            </td>
        </tr>"""
    content = f'''
    <h2 class="text-warning mb-4">🪨 {t['stock']}</h2>
    <div class="card p-4 shadow">
        <div class="table-responsive">
            <table class="table table-striped table-hover align-middle">
                <thead>
                    <tr class="table-dark">
                        <th>ID</th>
                        <th>Material Növü</th>
                        <th>Silo / Bunker</th>
                        <th>{t['current_stock']}</th>
                        <th>{t['max_capacity']}</th>
                        <th>Doluluk</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>'''
    return render_page(content, t, lang)

@app.route('/reports')
def reports():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    content = f'''
    <h2 class="text-warning mb-4">📊 {t['reports']}</h2>
    <div class="card p-4 shadow">
        <p class="text-secondary">Hesabatlar və tarixçə modulu aktivdir.</p>
        <a href="/orders" class="btn btn-outline-warning">Sifariş Hesabatlarına Bax</a>
    </div>'''
    return render_page(content, t, lang)

@app.route('/scada')
def scada():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    content = f'''
    <h2 class="text-warning mb-4">🖥️ {t['scada']}</h2>
    <div class="row">
        <div class="col-md-8">
            <div class="card p-4 shadow mb-4 bg-black border-warning text-center">
                <h3 class="text-warning">Beton Batching Plant SCADA Mimik Diaqramı</h3>
                <p class="text-muted">PLC IP: 192.168.1.50 | Modbus TCP Online</p>
                <div class="py-5">
                    <a href="#" class="btn btn-success btn-lg fw-bold px-5 me-3">{t['start_prod']}</a>
                    <a href="#" class="btn btn-danger btn-lg fw-bold px-5">{t['estop']}</a>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-4 shadow border-info">
                <h4 class="text-info mb-3">Rejim / Fazalar</h4>
                <ul class="list-group list-group-flush bg-transparent">
                    <li class="list-group-item bg-transparent text-light">1. Dozaj (Bunkerlər & Silolar): <span class="badge bg-success">{t['ready']}</span></li>
                    <li class="list-group-item bg-transparent text-light">2. Konveyyər və Mikser Yükləmə: <span class="badge bg-secondary">{t['waiting']}</span></li>
                    <li class="list-group-item bg-transparent text-light">3. Zames və Boşalma (Sliv): <span class="badge bg-secondary">{t['waiting']}</span></li>
                </ul>
            </div>
        </div>
    </div>'''
    return render_page(content, t, lang)

@app.route('/settings')
def settings():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        f_set = conn.execute("SELECT * FROM factory_settings LIMIT 1").fetchone()
    content = f'''
    <h2 class="text-warning mb-4">⚙️ {t['settings']} (Factory Parameters)</h2>
    <div class="card p-4 shadow">
        <form method="POST">
            <div class="row">
                <div class="col-md-4 mb-3"><label>Mikser Həcmi (m³)</label><input type="text" class="form-control" value="{f_set[1] if f_set else 2.0}" readonly></div>
                <div class="col-md-4 mb-3"><label>{t['mixing_time']}</label><input type="text" class="form-control" value="{f_set[2] if f_set else 45.0}" readonly></div>
                <div class="col-md-4 mb-3"><label>{t['gate_open_time']}</label><input type="text" class="form-control" value="{f_set[3] if f_set else 5.0}" readonly></div>
            </div>
            <a href="/" class="btn btn-secondary">{t['back']}</a>
        </form>
    </div>'''
    return render_page(content, t, lang)

@app.route('/company')
def company():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        c = conn.execute("SELECT * FROM company_info LIMIT 1").fetchone()
    content = f'''
    <h2 class="text-warning mb-4">🏢 {t['company']}</h2>
    <div class="card p-4 shadow col-md-6">
        <p><b>{t['company_name']}:</b> {c[1] if c else ''}</p>
        <p><b>{t['address']}:</b> {c[2] if c else ''}</p>
        <p><b>{t['phone']}:</b> {c[3] if c else ''}</p>
        <p><b>{t['tax_no']}:</b> {c[4] if c else ''}</p>
    </div>'''
    return render_page(content, t, lang)

@app.route('/operators')
def operators():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    ops = get_all('operators')
    rows = "".join([f"<tr><td>{o[0]}</td><td><b>{o[1]}</b></td><td>{o[2]}</td></tr>" for o in ops])
    content = f'''<h2 class="text-warning mb-4">👷 {t['operators']}</h2><div class="card p-4 shadow"><table class="table table-striped"><thead><tr class="table-dark"><th>ID</th><th>Ad Soyad</th><th>Tel</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    return render_page(content, t, lang)

@app.route('/drivers')
def drivers():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    drv = get_all('drivers')
    rows = "".join([f"<tr><td>{d[0]}</td><td><b>{d[1]}</b></td><td>{d[2]}</td><td>{d[3]}</td></tr>" for d in drv])
    content = f'''<h2 class="text-warning mb-4">🚚 {t['drivers']}</h2><div class="card p-4 shadow"><table class="table table-striped"><thead><tr class="table-dark"><th>ID</th><th>Ad Soyad</th><th>Tel</th><th>{t['license']}</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    return render_page(content, t, lang)

@app.route('/vehicles')
def vehicles():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    veh = get_all('vehicles')
    rows = "".join([f"<tr><td>{v[0]}</td><td><b>{v[1]}</b></td><td>{v[2]} m³</td><td>{v[3]} kg</td></tr>" for v in veh])
    content = f'''<h2 class="text-warning mb-4">🚛 {t['vehicles']}</h2><div class="card p-4 shadow"><table class="table table-striped"><thead><tr class="table-dark"><th>ID</th><th>Dövlət Nömrəsi</th><th>Həcm</th><th>Tara (Boş Çəki)</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    return render_page(content, t, lang)

@app.route('/clients')
def clients():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    cl = get_all('clients')
    rows = "".join([f"<tr><td>{c[0]}</td><td><b>{c[1]}</b></td><td>{c[2]}</td><td>{c[3]}</td></tr>" for c in cl])
    content = f'''<h2 class="text-warning mb-4">🏢 {t['clients']}</h2><div class="card p-4 shadow"><table class="table table-striped"><thead><tr class="table-dark"><th>ID</th><th>{t['client']}</th><th>Tel</th><th>{t['address']}</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    return render_page(content, t, lang)

@app.route('/suppliers')
def suppliers():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    sup = get_all('suppliers')
    rows = "".join([f"<tr><td>{s[0]}</td><td><b>{s[1]}</b></td><td>{s[2]}</td></tr>" for s in sup])
    content = f'''<h2 class="text-warning mb-4">🏭 {t['suppliers']}</h2><div class="card p-4 shadow"><table class="table table-striped"><thead><tr class="table-dark"><th>ID</th><th>Təchizatçı</th><th>Tel</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    return render_page(content, t, lang)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
