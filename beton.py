from flask import Flask, render_template_string, request, redirect, session, url_for, jsonify, Response
import sqlite3
import urllib.parse
from datetime import datetime, timedelta
import os
import csv
import io

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
        "print_version": "Yazdırılabilir Sayfa", "export_csv": "📥 CSV/Excel İhracat", "back": "Geri Dön", "nakladnoy": "Sevk İrsaliyesi",
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
        "close": "Kapat", "print": "🖨️ Yazdır",
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
        "print_version": "Версия для печати", "export_csv": "📥 Экспорт в CSV/Excel", "back": "Назад", "nakladnoy": "Товарно-Транспортная Накладная",
        "sub_title": "SCADA и Система Управления Бетонным Заводом (Учет Перевозок Водителей, Склад, Рецепты, Modbus)",
        "client": "Клиент (Заказчик)",
        "mixer": "Миксер (Машина)",
        "recipe": "Рецепт / Марка Бетона",
        "volume": "Объем (м³)",
        "price_m3": "Цена за 1 м³ (AZN)",
        "total_price": "Общая Стоимость",
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
            
            # Populate Modbus registers from shabran.gpf.csv dataset
            import pandas as pd
            try:
                mod_df = pd.read_csv('shabran.gpf.csv', encoding='utf-16le', sep='\t')
                mod_records = []
                for _, row in mod_df.iterrows():
                    tag = str(row.iloc[0]).strip()
                    addr_type = int(row.iloc[3]) if pd.notnull(row.iloc[3]) else 0
                    addr = int(row.iloc[5]) if pd.notnull(row.iloc[5]) else 0
                    dtype = "BIT" if addr_type == 1 else "REGISTER"
                    mod_records.append((tag, dtype, addr, f"Shabran GPF Tag (Type: {addr_type})"))
                
                cursor.execute("SELECT COUNT(*) FROM modbus_registers")
                if cursor.fetchone()[0] == 0:
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
            <td><a href='/modbus/delete/{r[0]}' class='btn btn-danger btn-sm'>🗑️ {t['delete']}</a></td>
        </tr>"""

    content = f'''
    <h2 class="text-warning mb-4">🔌 Modbus TCP Configuration & Register Mapping (Shabran GPF Dataset: {len(registers)} Tags)</h2>
    
    <div class="row mb-4">
        <div class="col-md-5">
            <div class="card p-4 shadow mb-3 border-info">
                <h4 class="text-info mb-3">🌐 Connection Settings</h4>
                <form method="POST">
                    <input type="hidden" name="save_config" value="1">
                    <div class="mb-2"><label>PLC IP Address</label><input type="text" name="plc_ip" class="form-control" value="{cfg[0]}" required></div>
                    <div class="mb-2"><label>Modbus Port</label><input type="number" name="plc_port" class="form-control" value="{cfg[1]}" required></div>
                    <div class="mb-3"><label>Slave / Unit ID</label><input type="number" name="slave_id" class="form-control" value="{cfg[2]}" required></div>
                    <button type="submit" class="btn btn-info w-100 fw-bold">{t['save']}</button>
                </form>
            </div>
        </div>
        
        <div class="col-md-7">
            <div class="card p-4 shadow mb-3 border-warning">
                <h4 class="text-warning mb-3">➕ Add Tag / Address</h4>
                <form method="POST">
                    <input type="hidden" name="add_tag" value="1">
                    <div class="row g-2 mb-2">
                        <div class="col-md-6"><label>Tag Name</label><input type="text" name="tag_name" class="form-control" placeholder="e.g. Bunker1_Weight" required></div>
                        <div class="col-md-6"><label>Type</label>
                            <select name="data_type" class="form-select">
                                <option value="REGISTER">REGISTER (Holding / 16-bit)</option>
                                <option value="BIT">BIT (Coil / Discrete)</option>
                            </select>
                        </div>
                    </div>
                    <div class="row g-2 mb-3">
                        <div class="col-md-4"><label>Address Offset</label><input type="number" name="address" class="form-control" placeholder="e.g. 40001 or 0" required></div>
                        <div class="col-md-8"><label>Description</label><input type="text" name="description" class="form-control" placeholder="e.g. Bunker 1 Load Cell Value"></div>
                    </div>
                    <button type="submit" class="btn btn-success w-100 fw-bold">{t['add']}</button>
                </form>
            </div>
        </div>
    </div>

    <div class="card p-3 shadow">
        <h4 class="text-white mb-3">📑 Mapped Registers & Bits</h4>
        <div style="max-height: 500px; overflow-y: auto;">
            <table class="table table-striped table-bordered align-middle text-center mb-0">
                <thead class="table-dark sticky-top">
                    <tr><th>ID</th><th>Tag Name</th><th>Type</th><th>Address</th><th>Description</th><th>{t['action']}</th></tr>
                </thead>
                <tbody>{rows if rows else "<tr><td colspan='6' class='text-muted py-3'>No registers defined yet</td></tr>"}</tbody>
            </table>
        </div>
    </div>
    '''
    return render_page(content, t, lang)

@app.route('/modbus/delete/<int:id>')
def delete_modbus_tag(id):
    with sqlite3.connect(DB) as conn:
        conn.execute("DELETE FROM modbus_registers WHERE id = ?", (id,))
        conn.commit()
    return redirect('/modbus')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            conn.execute("UPDATE factory_settings SET mixer_capacity_m3=?, mixing_time_sec=?, gate_open_time_sec=?, gate_pulse_period_sec=?, discharge_time_sec=?, transporter_stop_delay_sec=?, inter_hopper_open_sec=?, cement_delay_sec=?, water_delay_sec=?, additive_delay_sec=? WHERE id=1",
                         (request.form['mixer_capacity_m3'], request.form['mixing_time_sec'], request.form['gate_open_time_sec'], request.form['gate_pulse_period_sec'], request.form['discharge_time_sec'], request.form['transporter_stop_delay_sec'], request.form['inter_hopper_open_sec'], request.form['cement_delay_sec'], request.form['water_delay_sec'], request.form['additive_delay_sec']))
            conn.commit()
            return redirect('/settings')
        s = conn.execute("SELECT * FROM factory_settings LIMIT 1").fetchone()
    content = f'''
    <h2 class="text-warning mb-4">⚙️ {t['settings']}</h2>
    <div class="card p-4 shadow"><form method="POST">
    <div class="row g-3 mb-4">
        <div class="col-md-6"><label>{t['volume']} (m³)</label><input type="number" step="0.1" name="mixer_capacity_m3" class="form-control" value="{s[1]}" required></div>
        <div class="col-md-6"><label>{t['mixing_time']}</label><input type="number" step="1" name="mixing_time_sec" class="form-control" value="{s[2]}" required></div>
        <div class="col-md-6"><label>{t['gate_open_time']}</label><input type="number" step="0.5" name="gate_open_time_sec" class="form-control" value="{s[3]}" required></div>
        <div class="col-md-6"><label>{t['gate_pulse_period']}</label><input type="number" step="0.1" name="gate_pulse_period_sec" class="form-control" value="{s[4]}" required></div>
    </div>
    <div class="row g-3 mb-4">
        <div class="col-md-6"><label>{t['discharge_time']}</label><input type="number" step="1" name="discharge_time_sec" class="form-control" value="{s[5]}" required></div>
        <div class="col-md-6"><label>{t['transporter_stop_delay']}</label><input type="number" step="0.5" name="transporter_stop_delay_sec" class="form-control" value="{s[6]}" required></div>
    </div>
    <button type="submit" class="btn btn-warning btn-lg w-100 fw-bold">{t['save']}</button>
    </form></div>'''
    return render_page(content, t, lang)

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
            <td>{o[0]}</td>
            <td>{o[1][:16].replace('T', ' ')}</td>
            <td><b>{o[2]}</b></td>
            <td>{o[3]}</td>
            <td>{o[4]}</td>
            <td>{o[5]} m³</td>
            <td>{o[6]:,.2f} AZN</td>
            <td class="text-success fw-bold">{o[7]:,.2f} AZN</td>
            <td>{o[8] or '-'}</td>
            <td><a href='/orders/nakladnoy/{o[0]}' class='btn btn-outline-warning btn-sm' target='_blank'>📄 {t['nakladnoy']}</a></td>
        </tr>"""
    
    content = f'''
    <h2 class="text-warning mb-4">📦 {t['orders']}</h2>
    <div class="card p-4 mb-4 shadow"><form method="POST" action="/orders/add">
        <div class="row g-3">
            <div class="col-md-3"><label>{t['client']}</label><select name="client_id" class="form-select" required><option value="">...</option>{client_opts}</select></div>
            <div class="col-md-3"><label>{t['mixer']}</label><select name="vehicle_id" class="form-select" required onchange="updateOrderVolume(this)"><option value="">...</option>{vehicle_opts}</select></div>
            <div class="col-md-3"><label>{t['recipe']}</label><select name="recipe_id" class="form-select" required><option value="">...</option>{recipe_opts}</select></div>
            <div class="col-md-3"><label>{t['volume']}</label><input type="number" step="0.5" name="volume" class="form-control" value="8.0" required></div>
            <div class="col-md-3"><label>{t['price_m3']}</label><input type="number" step="1" name="price_per_m3" class="form-control" value="110.0" required></div>
            <div class="col-md-4"><label>{t['operator']}</label><select name="operator_id" class="form-select"><option value="">...</option>{op_opts}</select></div>
        </div>
        <button type="submit" class="btn btn-success mt-3 fw-bold">{t['confirm_order']}</button>
    </form></div>
    <div class="card p-3 shadow"><table class="table table-striped table-bordered align-middle text-center mb-0">
        <thead><tr><th>{t['id']}</th><th>{t['date']}</th><th>{t['client']}</th><th>{t['mixer']}</th><th>{t['recipe']}</th><th>{t['volume']}</th><th>{t['price_m3']}</th><th>{t['total_price']}</th><th>{t['operator']}</th><th>{t['document']}</th></tr></thead>
        <tbody>{rows}</tbody>
    </table></div>
    <script>
    function updateOrderVolume(selectEl) {{
        let opt = selectEl.options[selectEl.selectedIndex];
        let cap = opt.getAttribute("data-capacity");
        let volInput = document.querySelector("input[name='volume']");
        if (cap && volInput) {{
            volInput.value = cap;
        }}
    }}
    </script>'''
    return render_page(content, t, lang)

@app.route('/orders/add', methods=['POST'])
def add_order():
    client_id = request.form.get('client_id')
    vehicle_id = request.form.get('vehicle_id')
    recipe_id = request.form.get('recipe_id')
    
    vol_input = request.form.get('volume') or request.form.get('volume_m3') or 8.0
    volume = float(vol_input)
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
            b1 = float(recipe[2] or 0)
            b2 = float(recipe[3] or 0)
            b3 = float(recipe[4] or 0)
            b4 = float(recipe[5] or 0)
            s1 = float(recipe[6] or 0)
            s2 = float(recipe[7] or 0)
            s3 = float(recipe[8] or 0)
            s4 = float(recipe[9] or 0)
            wat = float(recipe[10] or 0)
            
            qatki_pct = float(recipe[11]) if len(recipe) > 11 and recipe[11] is not None else 0.0
            total_cement_per_m3 = s1 + s2 + s3 + s4
            additive_kg_per_m3 = (total_cement_per_m3 * qatki_pct) / 100.0

            consumptions = [
                ("Bunker 1", b1 * volume), ("Bunker 2", b2 * volume),
                ("Bunker 3", b3 * volume), ("Bunker 4", b4 * volume),
                ("Silo 1", s1 * volume), ("Silo 2", s2 * volume),
                ("Silo 3", s3 * volume), ("Silo 4", s4 * volume),
                ("Su", wat * volume), ("Qatqı", additive_kg_per_m3 * volume)
            ]

            now_str = datetime.now().isoformat()
            for mat_name, qty in consumptions:
                if qty > 0:
                    conn.execute("UPDATE stock SET current_kg = MAX(0, current_kg - ?) WHERE code_name = ?", (qty, mat_name))
                    conn.execute("INSERT INTO stock_movements (date, operation_type, material_name, quantity_kg, partner_name, note) VALUES (?, 'Sərfiyyat', ?, ?, ?, ?)",
                                 (now_str, mat_name, qty, client_name, f"Order #{order_id} ({recipe[1]} - {volume} m3)"))
        conn.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({"status": "success", "order_id": order_id})
    
    return redirect('/orders')

@app.route('/orders/nakladnoy/<int:id>')
def nakladnoy(id):
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        order = conn.execute("""
            SELECT o.id, o.date, c.name, c.address, v.plate_number, d.name, r.name, 
                   o.volume_m3, o.price_per_m3, (o.volume_m3 * o.price_per_m3), op.name, 
                   v.tare_weight_kg, r.bunker_1, r.bunker_2, r.bunker_3, r.bunker_4, 
                   r.silo_1, r.silo_2, r.silo_3, r.silo_4, r.water, r.qatki_percent 
            FROM orders o 
            JOIN clients c ON o.client_id = c.id 
            JOIN vehicles v ON o.vehicle_id = v.id 
            LEFT JOIN drivers d ON v.driver_id = d.id 
            JOIN recipes r ON o.recipe_id = r.id 
            LEFT JOIN operators op ON o.operator_id = op.id 
            WHERE o.id=?
        """, (id,)).fetchone()
        comp = conn.execute("SELECT * FROM company_info LIMIT 1").fetchone()
    
    if not order:
        return "Not found", 404

    comp_name, comp_addr, comp_phone, comp_tax = (comp[1], comp[2], comp[3], comp[4]) if comp else ('Industrial Automation', '', '', '')
    
    vol = float(order[7])
    tare_weight = float(order[11] or 12000.0)
    r_b1, r_b2, r_b3, r_b4 = float(order[12] or 0), float(order[13] or 0), float(order[14] or 0), float(order[15] or 0)
    r_s1, r_s2, r_s3, r_s4 = float(order[16] or 0), float(order[17] or 0), float(order[18] or 0), float(order[19] or 0)
    r_wat = float(order[20] or 0)
    r_qatki_pct = float(order[21] if order[21] is not None else 1.0)
    
    total_cement_m3 = r_s1 + r_s2 + r_s3 + r_s4
    additive_m3 = (total_cement_m3 * r_qatki_pct) / 100.0
    weight_per_m3 = r_b1 + r_b2 + r_b3 + r_b4 + total_cement_m3 + r_wat + additive_m3
    concrete_total_weight = weight_per_m3 * vol
    gross_weight = tare_weight + concrete_total_weight

    qr_text = f"Plant: {comp_name} | No: {order[0]} | Date: {order[1][:10]} | Client: {order[2]} | Vol: {vol} m3 | Gross: {gross_weight:,.0f} kg"
    qr_encoded = urllib.parse.quote(qr_text)

    content = f'''
    <div class="card p-4 bg-white text-dark mx-auto my-3 shadow-sm" style="max-width: 650px; border: 2px dashed #495057 !important;">
        <div class="text-center border-bottom pb-3 mb-3">
            <h4 class="fw-bold text-dark m-0">🏗️ {comp_name}</h4>
            <small class="text-muted">📍 {comp_addr} | {t['phone_label']}: {comp_phone} | {t['tax_no']}: {comp_tax}</small>
        </div>
        
        <div class="d-flex justify-content-between align-items-center mb-3 bg-light p-2 rounded">
            <div>
                <h5 class="text-primary fw-bold m-0">{t['nakladnoy']} № {order[0]}</h5>
                <small class="text-muted">{t['date']}: {order[1][:16].replace('T', ' ')}</small>
            </div>
            <div class="text-end">
                <span class="badge bg-dark fs-6">{t['mixer']}: {order[4]}</span>
            </div>
        </div>
        
        <div class="mb-3 p-2 border rounded bg-white">
            <p class="mb-1"><b>{t['client']}:</b> <span class="text-dark fw-bold">{order[2]}</span></p>
            <p class="mb-1 small"><b>{t['address_label']}:</b> {order[3]}</p>
            <p class="mb-0 small"><b>{t['driver_label']}:</b> {order[5] or '-'}</p>
        </div>
        
        <table class="table table-bordered align-middle text-center mb-3">
            <thead class="table-dark">
                <tr><th>{t['product_name']}</th><th>{t['volume']}</th><th>{t['price_m3']}</th><th>{t['total_price']}</th></tr>
            </thead>
            <tbody>
                <tr>
                    <td class="fw-bold fs-6 text-start ps-2">{order[6]}</td>
                    <td class="fw-bold fs-6 text-primary">{vol} m³</td>
                    <td>{order[8]:,.2f}</td>
                    <td class="fw-bold text-success">{order[9]:,.2f} AZN</td>
                </tr>
            </tbody>
        </table>

        <div class="mb-3 p-2 border rounded bg-light small">
            <div class="row text-center">
                <div class="col-4"><span>⚖️ {t['tare_weight']}:</span><br><b>{tare_weight:,.0f} kg</b></div>
                <div class="col-4"><span>📦 {t['concrete_weight']}:</span><br><b>{concrete_total_weight:,.0f} kg</b></div>
                <div class="col-4 text-success"><span>🚛 {t['gross_weight']}:</span><br><b class="fs-6">{gross_weight:,.0f} kg</b></div>
            </div>
        </div>

        <div class="text-center my-3 py-2 border-top border-bottom bg-light rounded">
            <div class="d-flex justify-content-center my-2">
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=110x110&data={qr_encoded}" alt="QR Code">
            </div>
            <p class="small text-muted mt-1 mb-0 font-monospace">№ {order[0]} | {order[1][:10]}</p>
        </div>
        
        <div class="row mt-2 pt-2">
            <div class="col-6 text-center">
                <p class="mb-3 small"><b>{t['delivered_by']}</b></p>
                <hr class="w-75 mx-auto my-1">
                <small class="text-muted">{order[10] or ''}</small>
            </div>
            <div class="col-6 text-center">
                <p class="mb-3 small"><b>{t['received_by']}</b></p>
                <hr class="w-75 mx-auto my-1">
                <small class="text-muted"></small>
            </div>
        </div>
        
        <div class="text-center mt-4 d-print-none">
            <button onclick="window.print()" class="btn btn-warning btn-lg px-5 fw-bold shadow">{t['print']}</button>
            <a href="/orders" class="btn btn-secondary btn-lg px-4 ms-2">{t['back']}</a>
        </div>
    </div>
    '''
    return render_page(content, t, lang, hide_nav=True)

@app.route('/stock', methods=['GET', 'POST'])
def stock():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            if 'update_capacity' in request.form:
                conn.execute("UPDATE stock SET max_capacity_kg = ? WHERE id = ?", (request.form['max_capacity'], request.form['stock_id']))
            else:
                sup_id = request.form['supplier_id']
                mat_code = request.form['material_code']
                qty = float(request.form['quantity'])
                sup_name = conn.execute("SELECT name FROM suppliers WHERE id=?", (sup_id,)).fetchone()[0]
                
                conn.execute("INSERT INTO stock_income (date, supplier_id, material_code, quantity_kg, note) VALUES (?, ?, ?, ?, ?)",
                             (datetime.now().isoformat(), sup_id, mat_code, qty, request.form.get('note', '')))
                conn.execute("UPDATE stock SET current_kg = current_kg + ? WHERE code_name = ?", (qty, mat_code))
                
                conn.execute("INSERT INTO stock_movements (date, operation_type, material_name, quantity_kg, partner_name, note) VALUES (?, 'Gəliş', ?, ?, ?, ?)",
                             (datetime.now().isoformat(), mat_code, qty, sup_name, request.form.get('note', 'Supplier In')))
            conn.commit()
            return redirect('/stock')
        stock_data = get_all("stock")
        suppliers = get_all("suppliers")

    sup_opts = "".join([f"<option value='{s[0]}'>{s[1]}</option>" for s in suppliers])
    mat_opts = "".join([f"<option value='{s[2]}'>{s[2]} ({s[1]})</option>" for s in stock_data])
    
    rows = ""
    for s in stock_data:
        rows += f"""<tr>
            <td>{s[0]}</td>
            <td><b>{s[1]}</b></td>
            <td><span class='badge bg-secondary'>{s[2]}</span></td>
            <td class='text-info fw-bold'>{s[3]:,.1f} kg</td>
            <td>
                <form method='POST' class='d-flex justify-content-center align-items-center gap-1'>
                    <input type='hidden' name='stock_id' value='{s[0]}'>
                    <input type='hidden' name='update_capacity' value='1'>
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
            <div class="col-md-3"><label>{t['supplier']}</label><select name="supplier_id" class="form-select" required><option value="">...</option>{sup_opts}</select></div>
            <div class="col-md-3"><label>{t['material']}</label><select name="material_code" class="form-select" required><option value="">...</option>{mat_opts}</select></div>
            <div class="col-md-3"><label>{t['total_qty']} (kg)</label><input type="number" step="100" name="quantity" class="form-control" required></div>
            <div class="col-md-3"><label>{t['note']}</label><input type="text" name="note" class="form-control"></div>
        </div>
        <button type="submit" class="btn btn-success mt-3 fw-bold">{t['save_stock']}</button>
    </form></div>
    <div class="card p-3 shadow"><table class="table table-striped table-bordered align-middle text-center mb-0">
        <thead><tr><th>{t['id']}</th><th>Component</th><th>Code</th><th>{t['current_stock']}</th><th>{t['max_capacity']}</th><th>{t['action']}</th></tr></thead>
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
            conn.execute("INSERT INTO stock_movements (date, operation_type, material_name, quantity_kg, partner_name, note) VALUES (?, 'Gəliş', ?, ?, 'System', 'Full Refill')",
                         (datetime.now().isoformat(), mat[0], diff))
            conn.commit()
    return redirect('/stock')

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

        rows += f"""<tr>
            <td>{r[0]}</td>
            <td><b>{r[1]}</b></td>
            <td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td>
            <td>{r[6]}</td><td>{r[7]}</td><td>{r[8]}</td><td>{r[9]}</td>
            <td>{r[10]}</td>
            <td><span class='badge bg-info text-dark fs-6'>{additive_pct}%</span></td>
            <td><span class='badge bg-warning text-dark fs-6'>{additive_kg:.1f} kg</span></td>
            <td class='text-warning fw-bold'>{total_weight:,.1f} kg</td>
            <td><a href='/recipes/edit/{r[0]}' class='btn btn-warning btn-sm me-1'>✏️ {t['edit']}</a> <a href='/recipes/delete/{r[0]}' class='btn btn-danger btn-sm'>🗑️ {t['delete']}</a></td>
        </tr>"""
    
    content = f'''
    <h2 class="text-warning mb-4">🧪 {t['recipes']}</h2>
    <div class="card p-4 mb-4 shadow"><form method="POST" action="/recipes/add">
        <h4 class="text-info mb-3">➕ {t['add']}</h4>
        <div class="row g-3">
            <div class="col-md-4"><label>{t['recipe']}</label><input type="text" name="name" class="form-control" required></div>
            <div class="col-md-2"><label>Bunker 1 (kg)</label><input type="number" step="1" name="bunker_1" class="form-control" value="0" required></div>
            <div class="col-md-2"><label>Bunker 2 (kg)</label><input type="number" step="1" name="bunker_2" class="form-control" value="0" required></div>
            <div class="col-md-2"><label>Bunker 3 (kg)</label><input type="number" step="1" name="bunker_3" class="form-control" value="0" required></div>
            <div class="col-md-2"><label>Bunker 4 (kg)</label><input type="number" step="1" name="bunker_4" class="form-control" value="0" required></div>
            <div class="col-md-2"><label>Silo 1 (kg)</label><input type="number" step="1" name="silo_1" class="form-control" value="0" required></div>
            <div class="col-md-2"><label>Silo 2 (kg)</label><input type="number" step="1" name="silo_2" class="form-control" value="0" required></div>
            <div class="col-md-2"><label>Silo 3 (kg)</label><input type="number" step="1" name="silo_3" class="form-control" value="0" required></div>
            <div class="col-md-2"><label>Silo 4 (kg)</label><input type="number" step="1" name="silo_4" class="form-control" value="0" required></div>
            <div class="col-md-2"><label>Water (kg)</label><input type="number" step="1" name="water" class="form-control" value="0" required></div>
            <div class="col-md-3"><label>Additive (%)</label><input type="number" step="0.1" name="qatki_percent" class="form-control" value="1.0" required></div>
        </div>
        <button type="submit" class="btn btn-success mt-3 fw-bold">{t['save']}</button>
    </form></div>
    <div class="card p-3 shadow"><table class="table table-striped table-bordered align-middle text-center mb-0">
        <thead><tr><th>{t['id']}</th><th>Name</th><th>B1</th><th>B2</th><th>B3</th><th>B4</th><th>S1</th><th>S2</th><th>S3</th><th>S4</th><th>Water</th><th>Additive (%)</th><th>Additive (kg)</th><th>Total Weight</th><th>{t['action']}</th></tr></thead>
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
    lang = get_lang()
    t = TRANSLATIONS[lang]
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            conn.execute("UPDATE recipes SET name=?, bunker_1=?, bunker_2=?, bunker_3=?, bunker_4=?, silo_1=?, silo_2=?, silo_3=?, silo_4=?, water=?, qatki_percent=? WHERE id=?",
                         (request.form['name'], request.form['bunker_1'], request.form['bunker_2'], request.form['bunker_3'], request.form['bunker_4'], request.form['silo_1'], request.form['silo_2'], request.form['silo_3'], request.form['silo_4'], request.form['water'], request.form['qatki_percent'], id))
            conn.commit()
            return redirect('/recipes')
        r = conn.execute("SELECT * FROM recipes WHERE id=?", (id,)).fetchone()

    content = f'''
    <h2 class="text-warning mb-4">✏️ {t['edit']}</h2>
    <div class="card p-4 shadow"><form method="POST">
        <div class="row g-3">
            <div class="col-md-4"><label>{t['recipe']}</label><input type="text" name="name" class="form-control" value="{r[1]}" required></div>
            <div class="col-md-2"><label>Bunker 1 (kg)</label><input type="number" step="1" name="bunker_1" class="form-control" value="{r[2]}" required></div>
            <div class="col-md-2"><label>Bunker 2 (kg)</label><input type="number" step="1" name="bunker_2" class="form-control" value="{r[3]}" required></div>
            <div class="col-md-2"><label>Bunker 3 (kg)</label><input type="number" step="1" name="bunker_3" class="form-control" value="{r[4]}" required></div>
            <div class="col-md-2"><label>Bunker 4 (kg)</label><input type="number" step="1" name="bunker_4" class="form-control" value="{r[5]}" required></div>
            <div class="col-md-2"><label>Silo 1 (kg)</label><input type="number" step="1" name="silo_1" class="form-control" value="{r[6]}" required></div>
            <div class="col-md-2"><label>Silo 2 (kg)</label><input type="number" step="1" name="silo_2" class="form-control" value="{r[7]}" required></div>
            <div class="col-md-2"><label>Silo 3 (kg)</label><input type="number" step="1" name="silo_3" class="form-control" value="{r[8]}" required></div>
            <div class="col-md-2"><label>Silo 4 (kg)</label><input type="number" step="1" name="silo_4" class="form-control" value="{r[9]}" required></div>
            <div class="col-md-2"><label>Water (kg)</label><input type="number" step="1" name="water" class="form-control" value="{r[10]}" required></div>
            <div class="col-md-3"><label>Additive (%)</label><input type="number" step="0.1" name="qatki_percent" class="form-control" value="{r[11] if len(r)>11 and r[11] is not None else 1.0}" required></div>
        </div>
        <button type="submit" class="btn btn-warning mt-3 fw-bold w-100">{t['save']}</button>
    </form></div>'''
    return render_page(content, t, lang)

@app.route('/recipes/delete/<int:id>')
def delete_recipe(id):
    with sqlite3.connect(DB) as conn:
        conn.execute("DELETE FROM recipes WHERE id = ?", (id,))
        conn.commit()
    return redirect('/recipes')

@app.route('/operators')
def operators():
    lang, t = get_lang(), TRANSLATIONS[get_lang()]
    rows = "".join([f"<tr><td>{o[0]}</td><td><b>{o[1]}</b></td><td>{o[2]}</td><td><a href='/operators/edit/{o[0]}' class='btn btn-warning btn-sm me-1'>✏️ {t['edit']}</a> <a href='/operators/delete/{o[0]}' class='btn btn-danger btn-sm'>🗑️ {t['delete']}</a></td></tr>" for o in get_all("operators")])
    content = f'''<h2 class="text-warning mb-4">👨‍💻 {t['operators']}</h2>
    <div class="card p-4 mb-4 shadow"><form method="POST" action="/operators/add"><div class="row g-3">
        <div class="col-md-6"><label>Name</label><input type="text" name="name" class="form-control" required></div>
        <div class="col-md-6"><label>{t['phone']}</label><input type="text" name="phone" class="form-control" required></div>
    </div><button type="submit" class="btn btn-success mt-3">{t['add']}</button></form></div>
    <div class="card p-3 shadow"><table class="table table-striped table-bordered align-middle mb-0"><thead><tr><th>{t['id']}</th><th>Name</th><th>{t['phone']}</th><th>{t['action']}</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    return render_page(content, t, lang)

@app.route('/operators/add', methods=['POST'])
def add_operator():
    with sqlite3.connect(DB) as conn:
        conn.execute("INSERT INTO operators (name, phone) VALUES (?, ?)", (request.form['name'], request.form['phone']))
        conn.commit()
    return redirect('/operators')

@app.route('/operators/edit/<int:id>', methods=['GET', 'POST'])
def edit_operator(id):
    lang, t = get_lang(), TRANSLATIONS[get_lang()]
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            conn.execute("UPDATE operators SET name=?, phone=? WHERE id=?", (request.form['name'], request.form['phone'], id))
            conn.commit()
            return redirect('/operators')
        op = conn.execute("SELECT * FROM operators WHERE id=?", (id,)).fetchone()
    content = f'''<h2 class="text-warning mb-4">✏️ {t['edit']}</h2>
    <div class="card p-4 col-md-6 mx-auto shadow"><form method="POST">
        <div class="mb-3"><label>Name</label><input type="text" name="name" class="form-control" value="{op[1]}" required></div>
        <div class="mb-3"><label>{t['phone']}</label><input type="text" name="phone" class="form-control" value="{op[2]}" required></div>
        <button type="submit" class="btn btn-warning w-100 fw-bold">{t['save']}</button>
    </form></div>'''
    return render_page(content, t, lang)

@app.route('/operators/delete/<int:id>')
def delete_operator(id):
    with sqlite3.connect(DB) as conn:
        conn.execute("DELETE FROM operators WHERE id = ?", (id,))
        conn.commit()
    return redirect('/operators')

@app.route('/clients')
def clients():
    lang, t = get_lang(), TRANSLATIONS[get_lang()]
    rows = "".join([f"<tr><td>{c[0]}</td><td>{c[1]}</td><td>{c[2]}</td><td>{c[3]}</td><td><a href='/clients/edit/{c[0]}' class='btn btn-warning btn-sm me-1'>✏️ {t['edit']}</a> <a href='/clients/delete/{c[0]}' class='btn btn-danger btn-sm'>🗑️ {t['delete']}</a></td></tr>" for c in get_all("clients")])
    content = f'''<h2 class="text-warning mb-4">🏢 {t['clients']}</h2>
    <div class="card p-4 mb-4 shadow"><form method="POST" action="/clients/add"><div class="row g-3">
        <div class="col-md-4"><label>Company</label><input type="text" name="name" class="form-control" required></div>
        <div class="col-md-4"><label>Contact</label><input type="text" name="contact" class="form-control" required></div>
        <div class="col-md-4"><label>{t['address']}</label><input type="text" name="address" class="form-control" required></div>
    </div><button type="submit" class="btn btn-success mt-3">{t['add']}</button></form></div>
    <div class="card p-3 shadow"><table class="table table-striped table-bordered align-middle mb-0"><thead><tr><th>{t['id']}</th><th>Company</th><th>Contact</th><th>{t['address']}</th><th>{t['action']}</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    return render_page(content, t, lang)

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
            conn.commit()
            return redirect('/clients')
        c = conn.execute("SELECT * FROM clients WHERE id=?", (id,)).fetchone()
    content = f'''<h2 class="text-warning mb-4">✏️ {t['edit']}</h2>
    <div class="card p-4 col-md-6 mx-auto shadow"><form method="POST">
        <div class="mb-3"><label>Company</label><input type="text" name="name" class="form-control" value="{c[1]}" required></div>
        <div class="mb-3"><label>Contact</label><input type="text" name="contact" class="form-control" value="{c[2]}" required></div>
        <div class="mb-3"><label>{t['address']}</label><input type="text" name="address" class="form-control" value="{c[3]}" required></div>
        <button type="submit" class="btn btn-warning w-100 fw-bold">{t['save']}</button>
    </form></div>'''
    return render_page(content, t, lang)

@app.route('/clients/delete/<int:id>')
def delete_client(id):
    with sqlite3.connect(DB) as conn:
        conn.execute("DELETE FROM clients WHERE id = ?", (id,))
        conn.commit()
    return redirect('/clients')

@app.route('/vehicles')
def vehicles():
    lang, t = get_lang(), TRANSLATIONS[get_lang()]
    with sqlite3.connect(DB) as conn:
        vehicles_list = conn.execute("SELECT v.id, v.plate_number, v.capacity_m3, d.name, v.tare_weight_kg FROM vehicles v LEFT JOIN drivers d ON v.driver_id = d.id").fetchall()
        drivers = get_all("drivers")
    rows = "".join([f"<tr><td>{v[0]}</td><td><b>{v[1]}</b></td><td>{v[2]} m³</td><td><span class='text-warning'>{v[4]:,.0f} kg</span></td><td>{v[3]}</td><td><a href='/vehicles/edit/{v[0]}' class='btn btn-warning btn-sm me-1'>✏️ {t['edit']}</a> <a href='/vehicles/delete/{v[0]}' class='btn btn-danger btn-sm'>🗑️ {t['delete']}</a></td></tr>" for v in vehicles_list])
    driver_opts = "".join([f"<option value='{d[0]}'>{d[1]}</option>" for d in drivers])
    content = f'''<h2 class="text-warning mb-4">🚚 {t['vehicles']}</h2>
    <div class="card p-4 mb-4 shadow"><form method="POST" action="/vehicles/add"><div class="row g-3">
        <div class="col-md-3"><label>Plate Number</label><input type="text" name="plate_number" class="form-control" required></div>
        <div class="col-md-3"><label>{t['volume']} (m³)</label><input type="number" step="0.5" name="capacity" class="form-control" required></div>
        <div class="col-md-3"><label>{t['tare_weight']} (kg)</label><input type="number" step="100" name="tare_weight" class="form-control" value="12000" required></div>
        <div class="col-md-3"><label>{t['drivers']}</label><select name="driver_id" class="form-select" required><option value="">...</option>{driver_opts}</select></div>
    </div><button type="submit" class="btn btn-success mt-3">{t['add']}</button></form></div>
    <div class="card p-3 shadow"><table class="table table-striped table-bordered align-middle text-center mb-0"><thead><tr><th>{t['id']}</th><th>Plate</th><th>Capacity</th><th>{t['tare_weight']}</th><th>{t['drivers']}</th><th>{t['action']}</th></tr></thead><tbody>{rows}</tbody></table></div>'''
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
            conn.commit()
            return redirect('/vehicles')
        v = conn.execute("SELECT * FROM vehicles WHERE id=?", (id,)).fetchone()
        drivers = get_all("drivers")
    driver_opts = "".join([f"<option value='{d[0]}' {'selected' if d[0]==v[3] else ''}>{d[1]}</option>" for d in drivers])
    content = f'''<h2 class="text-warning mb-4">✏️ {t['edit']}</h2>
    <div class="card p-4 col-md-6 mx-auto shadow"><form method="POST">
        <div class="mb-3"><label>Plate Number</label><input type="text" name="plate_number" class="form-control" value="{v[1]}" required></div>
        <div class="mb-3"><label>{t['volume']} (m³)</label><input type="number" step="0.5" name="capacity" class="form-control" value="{v[2]}" required></div>
        <div class="mb-3"><label>{t['tare_weight']} (kg)</label><input type="number" step="100" name="tare_weight" class="form-control" value="{v[4] if len(v)>4 and v[4] is not None else 12000}" required></div>
        <div class="mb-3"><label>{t['drivers']}</label><select name="driver_id" class="form-select" required>{driver_opts}</select></div>
        <button type="submit" class="btn btn-warning w-100 fw-bold">{t['save']}</button>
    </form></div>'''
    return render_page(content, t, lang)

@app.route('/vehicles/delete/<int:id>')
def delete_vehicle(id):
    with sqlite3.connect(DB) as conn:
        conn.execute("DELETE FROM vehicles WHERE id = ?", (id,))
        conn.commit()
    return redirect('/vehicles')

@app.route('/drivers')
def drivers():
    lang, t = get_lang(), TRANSLATIONS[get_lang()]
    rows = "".join([f"<tr><td>{d[0]}</td><td>{d[1]}</td><td>{d[2]}</td><td>{d[3]}</td><td><a href='/drivers/edit/{d[0]}' class='btn btn-warning btn-sm me-1'>✏️ {t['edit']}</a> <a href='/drivers/delete/{d[0]}' class='btn btn-danger btn-sm'>🗑️ {t['delete']}</a></td></tr>" for d in get_all("drivers")])
    content = f'''<h2 class="text-warning mb-4">👨‍✈️ {t['drivers']}</h2>
    <div class="card p-4 mb-4 shadow"><form method="POST" action="/drivers/add"><div class="row g-3">
        <div class="col-md-4"><label>Name</label><input type="text" name="name" class="form-control" required></div>
        <div class="col-md-4"><label>{t['phone']}</label><input type="text" name="phone" class="form-control" required></div>
        <div class="col-md-4"><label>{t['license']}</label><input type="text" name="license" class="form-control" required></div>
    </div><button type="submit" class="btn btn-success mt-3">{t['add']}</button></form></div>
    <div class="card p-3 shadow"><table class="table table-striped table-bordered align-middle mb-0"><thead><tr><th>{t['id']}</th><th>Name</th><th>{t['phone']}</th><th>{t['license']}</th><th>{t['action']}</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    return render_page(content, t, lang)

@app.route('/drivers/add', methods=['POST'])
def add_driver():
    with sqlite3.connect(DB) as conn:
        conn.execute("INSERT INTO drivers (name, phone, license_number) VALUES (?, ?, ?)", (request.form['name'], request.form['phone'], request.form['license']))
        conn.commit()
    return redirect('/drivers')

@app.route('/drivers/edit/<int:id>', methods=['GET', 'POST'])
def edit_driver(id):
    lang, t = get_lang(), TRANSLATIONS[get_lang()]
    with sqlite3.connect(DB) as conn:
        if request.method == 'POST':
            conn.execute("UPDATE drivers SET name=?, phone=?, license_number=? WHERE id=?", (request.form['name'], request.form['phone'], request.form['license'], id))
            conn.commit()
            return redirect('/drivers')
        d = conn.execute("SELECT * FROM drivers WHERE id=?", (id,)).fetchone()
    content = f'''<h2 class="text-warning mb-4">✏️ {t['edit']}</h2>
    <div class="card p-4 col-md-6 mx-auto shadow"><form method="POST">
        <div class="mb-3"><label>Name</label><input type="text" name="name" class="form-control" value="{d[1]}" required></div>
        <div class="mb-3"><label>{t['phone']}</label><input type="text" name="phone" class="form-control" value="{d[2]}" required></div>
        <div class="mb-3"><label>{t['license']}</label><input type="text" name="license" class="form-control" value="{d[3]}" required></div>
        <button type="submit" class="btn btn-warning w-100 fw-bold">{t['save']}</button>
    </form></div>'''
    return render_page(content, t, lang)

@app.route('/drivers/delete/<int:id>')
def delete_driver(id):
    with sqlite3.connect(DB) as conn:
        conn.execute("DELETE FROM drivers WHERE id = ?", (id,))
        conn.commit()
    return redirect('/drivers')

@app.route('/suppliers')
def suppliers():
    lang, t = get_lang(), TRANSLATIONS[get_lang()]
    rows = "".join([f"<tr><td>{s[0]}</td><td>{s[1]}</td><td>{s[2]}</td><td><a href='/suppliers/edit/{s[0]}' class='btn btn-warning btn-sm me-1'>✏️ {t['edit']}</a> <a href='/suppliers/delete/{s[0]}' class='btn btn-danger btn-sm'>🗑️ {t['delete']}</a></td></tr>" for s in get_all("suppliers")])
    content = f'''<h2 class="text-warning mb-4">🏭 {t['suppliers']}</h2>
    <div class="card p-4 mb-4 shadow"><form method="POST" action="/suppliers/add"><div class="row g-3">
        <div class="col-md-6"><label>{t['supplier']}</label><input type="text" name="name" class="form-control" required></div>
        <div class="col-md-6"><label>{t['phone']}</label><input type="text" name="contact" class="form-control" required></div>
    </div><button type="submit" class="btn btn-success mt-3">{t['add']}</button></form></div>
    <div class="card p-3 shadow"><table class="table table-striped table-bordered align-middle mb-0"><thead><tr><th>{t['id']}</th><th>{t['supplier']}</th><th>Contact</th><th>{t['action']}</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    return render_page(content, t, lang)

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
            conn.commit()
            return redirect('/suppliers')
        s = conn.execute("SELECT * FROM suppliers WHERE id=?", (id,)).fetchone()
    content = f'''<h2 class="text-warning mb-4">✏️ {t['edit']}</h2>
    <div class="card p-4 col-md-6 mx-auto shadow"><form method="POST">
        <div class="mb-3"><label>{t['supplier']}</label><input type="text" name="name" class="form-control" value="{s[1]}" required></div>
        <div class="mb-3"><label>Contact</label><input type="text" name="contact" class="form-control" value="{s[2]}" required></div>
        <button type="submit" class="btn btn-warning w-100 fw-bold">{t['save']}</button>
    </form></div>'''
    return render_page(content, t, lang)

@app.route('/suppliers/delete/<int:id>')
def delete_supplier(id):
    with sqlite3.connect(DB) as conn:
        conn.execute("DELETE FROM suppliers WHERE id = ?", (id,))
        conn.commit()
    return redirect('/suppliers')

@app.route('/reports', methods=['GET', 'POST'])
def reports():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    
    today = datetime.now()
    default_start = today.replace(day=1).strftime('%Y-%m-%d')
    default_end = today.strftime('%Y-%m-%d')

    start_date = request.form.get('start_date') or request.args.get('start_date') or default_start
    end_date = request.form.get('end_date') or request.args.get('end_date') or default_end
    op_type = request.form.get('op_type') or request.args.get('op_type') or ''
    filter_material = request.form.get('filter_material') or request.args.get('filter_material') or ''
    filter_client = request.form.get('filter_client') or request.args.get('filter_client') or ''
    filter_driver = request.form.get('filter_driver') or request.args.get('filter_driver') or ''
    filter_recipe = request.form.get('filter_recipe') or request.args.get('filter_recipe') or ''

    with sqlite3.connect(DB) as conn:
        materials = conn.execute("SELECT DISTINCT code_name FROM stock").fetchall()
        clients = conn.execute("SELECT id, name FROM clients").fetchall()
        drivers = conn.execute("SELECT id, name FROM drivers").fetchall()
        recipes = conn.execute("SELECT id, name FROM recipes").fetchall()

        has_order_filter = bool(filter_driver or filter_client or filter_recipe)

        orders_report_data = []
        total_orders_vol = 0
        total_orders_amount = 0
        total_orders_count = 0

        if has_order_filter:
            sql = """
                SELECT o.id, o.date, c.name, c.address, v.plate_number, d.name, r.name, o.volume_m3, o.price_per_m3, (o.volume_m3 * o.price_per_m3), op.name 
                FROM orders o 
                JOIN clients c ON o.client_id = c.id 
                JOIN vehicles v ON o.vehicle_id = v.id 
                LEFT JOIN drivers d ON v.driver_id = d.id 
                JOIN recipes r ON o.recipe_id = r.id 
                LEFT JOIN operators op ON o.operator_id = op.id 
                WHERE date(o.date) BETWEEN date(?) AND date(?)
            """
            params = [start_date, end_date]

            if filter_driver:
                sql += " AND v.driver_id = ?"
                params.append(filter_driver)
            if filter_client:
                sql += " AND o.client_id = ?"
                params.append(filter_client)
            if filter_recipe:
                sql += " AND o.recipe_id = ?"
                params.append(filter_recipe)

            sql += " ORDER BY datetime(o.date) DESC"
            orders_report_data = conn.execute(sql, params).fetchall()
            total_orders_vol = sum([row[7] for row in orders_report_data])
            total_orders_amount = sum([row[9] for row in orders_report_data])
            total_orders_count = len(orders_report_data)

        material_report_data = []
        total_material_qty = 0
        if filter_material:
            mov_query = """
                SELECT id, date, operation_type, material_name, quantity_kg, partner_name, note 
                FROM stock_movements 
                WHERE date(date) BETWEEN date(?) AND date(?)
            """
            mov_params = [start_date, end_date]
            
            if filter_material == '__ALL_SILOS__':
                mov_query += " AND material_name IN ('Silo 1', 'Silo 2', 'Silo 3', 'Silo 4')"
            else:
                mov_query += " AND material_name = ?"
                mov_params.append(filter_material)

            if op_type:
                mov_query += " AND operation_type = ?"
                mov_params.append(op_type)
            mov_query += " ORDER BY datetime(date) DESC"
            material_report_data = conn.execute(mov_query, mov_params).fetchall()
            total_material_qty = sum([row[4] for row in material_report_data])

        driver_stats = []
        client_stats = []
        if not has_order_filter and not filter_material:
            driver_stats = conn.execute("""
                SELECT d.name, v.plate_number, COUNT(o.id), SUM(o.volume_m3), SUM(o.volume_m3 * o.price_per_m3)
                FROM orders o JOIN vehicles v ON o.vehicle_id = v.id JOIN drivers d ON v.driver_id = d.id
                WHERE date(o.date) BETWEEN date(?) AND date(?) GROUP BY d.id, v.id ORDER BY SUM(o.volume_m3) DESC
            """, [start_date, end_date]).fetchall()

            client_stats = conn.execute("""
                SELECT c.name, COUNT(o.id), SUM(o.volume_m3), SUM(o.volume_m3 * o.price_per_m3)
                FROM orders o JOIN clients c ON o.client_id = c.id
                WHERE date(o.date) BETWEEN date(?) AND date(?) GROUP BY c.id ORDER BY SUM(o.volume_m3 * o.price_per_m3) DESC
            """, [start_date, end_date]).fetchall()

    mat_opts = f"<option value='__ALL_SILOS__' {'selected' if filter_material=='__ALL_SILOS__' else ''}>{t['all_silos']}</option>"
    mat_opts += "".join([f"<option value='{m[0]}' {'selected' if filter_material==m[0] else ''}>{m[0]}</option>" for m in materials])
    
    client_opts = "".join([f"<option value='{c[0]}' {'selected' if filter_client==str(c[0]) else ''}>{c[1]}</option>" for c in clients])
    driver_opts = "".join([f"<option value='{d[0]}' {'selected' if filter_driver==str(d[0]) else ''}>{d[1]}</option>" for d in drivers])
    recipe_opts = "".join([f"<option value='{r[0]}' {'selected' if filter_recipe==str(r[0]) else ''}>{r[1]}</option>" for r in recipes])

    result_content = ""

    if has_order_filter:
        order_rows = ""
        for r in orders_report_data:
            order_rows += f"""<tr>
                <td><b>№ {r[0]}</b></td>
                <td>{r[1][:16].replace('T', ' ')}</td>
                <td class='text-start ps-3'><b>{r[2]}</b><br><small class='text-muted'>📍 {r[3] or '-'}</small></td>
                <td><span class='badge bg-dark fs-6'>{r[4]}</span><br><small class='text-info'>{r[5] or '-'}</small></td>
                <td><b>{r[6]}</b></td>
                <td class='fw-bold text-warning fs-6'>{r[7]} m³</td>
                <td class='fw-bold text-success'>{r[9]:,.2f} AZN</td>
                <td><small>{r[10] or '-'}</small></td>
                <td><a href='/orders/nakladnoy/{r[0]}' target='_blank' class='btn btn-outline-warning btn-sm'>📄 {t['nakladnoy']}</a></td>
            </tr>"""
        
        result_content = f'''
        <div class="card p-4 shadow mb-4 border-warning">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4 class="text-warning m-0">🎯 {t['reports']}</h4>
                <span class="badge bg-secondary fs-6">{t['start_date']}: {start_date} / {t['end_date']}: {end_date}</span>
            </div>
            <div class="row text-center mb-3 g-2">
                <div class="col-md-4"><div class="p-2 border rounded bg-dark"><small class="text-muted">{t['order_count']}</small><h5 class="text-info m-0">{total_orders_count}</h5></div></div>
                <div class="col-md-4"><div class="p-2 border rounded bg-dark"><small class="text-muted">{t['total_volume']}</small><h5 class="text-warning m-0">{total_orders_vol:,.1f} m³</h5></div></div>
                <div class="col-md-4"><div class="p-2 border rounded bg-dark"><small class="text-muted">{t['total_amount']}</small><h5 class="text-success m-0">{total_orders_amount:,.2f} AZN</h5></div></div>
            </div>
            <table class="table table-striped table-bordered align-middle text-center mb-0">
                <thead class="table-dark">
                    <tr><th>Qaimə №</th><th>{t['date']}</th><th>{t['client']} və Ünvan</th><th>{t['mixer']} / Sürücü</th><th>{t['recipe']}</th><th>{t['volume']}</th><th>{t['total_price']}</th><th>{t['operator']}</th><th>Sənəd</th></tr>
                </thead>
                <tbody>{order_rows if order_rows else f"<tr><td colspan='9' class='text-muted py-3'>Məlumat tapılmadı</td></tr>"}</tbody>
            </table>
        </div>'''

    elif filter_material:
        mat_rows = ""
        for m in material_report_data:
            badge_cls = "bg-success" if m[2] == "Gəliş" or m[2] == "Income" else "bg-danger"
            mat_rows += f"<tr><td>{m[0]}</td><td>{m[1][:16].replace('T', ' ')}</td><td><span class='badge {badge_cls}'>{m[2]}</span></td><td><b>{m[3]}</b></td><td class='fw-bold text-warning'>{m[4]:,.1f} kg</td><td>{m[5]}</td><td><small>{m[6] or '-'}</small></td></tr>"
        
        result_content = f'''
        <div class="card p-4 shadow mb-4 border-info">
            <h4 class="text-info mb-3">🎯 {t['material']}: <span class="text-white">{"Bütün Silolar" if filter_material=="__ALL_SILOS__" else filter_material}</span></h4>
            <p class="text-muted mb-2">{t['start_date']}: <b>{start_date}</b> / {t['end_date']}: <b>{end_date}</b> | {t['total_qty']}: <b class="text-warning fs-5">{total_material_qty:,.1f} kg</b></p>
            <table class="table table-striped table-bordered align-middle text-center mb-0">
                <thead class="table-dark">
                    <tr><th>{t['id']}</th><th>{t['date']}</th><th>{t['op_type']}</th><th>{t['material']}</th><th>{t['total_qty']} (kg)</th><th>Partner</th><th>{t['note']}</th></tr>
                </thead>
                <tbody>{mat_rows if mat_rows else f"<tr><td colspan='7' class='text-muted py-3'>Məlumat tapılmadı</td></tr>"}</tbody>
            </table>
        </div>'''

    else:
        driver_rows = "".join([f"<tr><td><b>{ds[0]}</b></td><td><span class='badge bg-dark'>{ds[1]}</span></td><td>{ds[2]}</td><td class='fw-bold text-warning'>{ds[3]:,.1f} m³</td><td class='fw-bold text-success'>{ds[4]:,.2f} AZN</td></tr>" for ds in driver_stats])
        client_rows = "".join([f"<tr><td><b>{cs[0]}</b></td><td>{cs[1]}</td><td class='fw-bold text-warning'>{cs[2]:,.1f} m³</td><td class='fw-bold text-success'>{cs[3]:,.2f} AZN</td></tr>" for cs in client_stats])
        
        result_content = f'''
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card p-3 shadow h-100">
                    <h5 class="text-success mb-3">{t['driver_rep']}</h5>
                    <table class="table table-striped table-bordered align-middle text-center mb-0">
                        <thead class="table-dark"><tr><th>{t['drivers']}</th><th>{t['mixer']}</th><th>{t['trips']}</th><th>{t['volume']}</th><th>{t['total_price']}</th></tr></thead>
                        <tbody>{driver_rows if driver_rows else f"<tr><td colspan='5' class='text-muted py-3'>Məlumat tapılmadı</td></tr>"}</tbody>
                    </table>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card p-3 shadow h-100">
                    <h5 class="text-info mb-3">{t['client_rep']}</h5>
                    <table class="table table-striped table-bordered align-middle text-center mb-0">
                        <thead class="table-dark"><tr><th>{t['client']}</th><th>{t['order_count']}</th><th>{t['volume']}</th><th>{t['total_price']}</th></tr></thead>
                        <tbody>{client_rows if client_rows else f"<tr><td colspan='4' class='text-muted py-3'>Məlumat tapılmadı</td></tr>"}</tbody>
                    </table>
                </div>
            </div>
        </div>'''

    content = f'''
    <h2 class="text-warning mb-4">📊 {t['reports']}</h2>
    
    <div class="card p-4 mb-4 shadow d-print-none"><form method="POST">
        <div class="row g-3 align-items-end">
            <div class="col-md-3"><label>{t['start_date']}</label><input type="date" name="start_date" class="form-control" value="{start_date}"></div>
            <div class="col-md-3"><label>{t['end_date']}</label><input type="date" name="end_date" class="form-control" value="{end_date}"></div>
            
            <div class="col-md-3">
                <label>{t['drivers']}</label>
                <select name="filter_driver" class="form-select">
                    <option value="">{t['all_drivers']}</option>
                    {driver_opts}
                </select>
            </div>
            <div class="col-md-3">
                <label>{t['client']}</label>
                <select name="filter_client" class="form-select">
                    <option value="">{t['all_clients']}</option>
                    {client_opts}
                </select>
            </div>

            <div class="col-md-3">
                <label>{t['recipe']}</label>
                <select name="filter_recipe" class="form-select">
                    <option value="">{t['all_recipes']}</option>
                    {recipe_opts}
                </select>
            </div>
            <div class="col-md-3">
                <label>{t['material']}</label>
                <select name="filter_material" class="form-select">
                    <option value="">{t['all_materials']}</option>
                    {mat_opts}
                </select>
            </div>
            <div class="col-md-3">
                <label>{t['op_type']}</label>
                <select name="op_type" class="form-select">
                    <option value="">{t['all_ops']}</option>
                    <option value="Sərfiyyat" {"selected" if op_type=="Sərfiyyat" else ""}>📤 {t['consumption']}</option>
                    <option value="Gəliş" {"selected" if op_type=="Gəliş" else ""}>📥 {t['income']}</option>
                </select>
            </div>

            <div class="col-md-3 text-end">
                <button type="submit" class="btn btn-warning w-100 fw-bold">{t['search']}</button>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-md-12 text-end">
                <a href="/reports/export?start_date={start_date}&end_date={end_date}&filter_driver={filter_driver}&filter_client={filter_client}&filter_recipe={filter_recipe}&filter_material={filter_material}" class="btn btn-success px-4 fw-bold me-2">{t['export_csv']}</a>
                <a href="/reports/print?start_date={start_date}&end_date={end_date}&filter_driver={filter_driver}&filter_client={filter_client}&filter_recipe={filter_recipe}&filter_material={filter_material}&op_type={op_type}" target="_blank" class="btn btn-info px-4 fw-bold">{t['print_version']}</a>
            </div>
        </div>
    </form></div>
    
    {result_content}
    '''
    return render_page(content, t, lang)

@app.route('/reports/export')
def reports_export():
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    filter_driver = request.args.get('filter_driver', '')
    filter_client = request.args.get('filter_client', '')
    filter_recipe = request.args.get('filter_recipe', '')
    filter_material = request.args.get('filter_material', '')

    si = io.StringIO()
    cw = csv.writer(si)

    with sqlite3.connect(DB) as conn:
        if filter_driver or filter_client or filter_recipe:
            cw.writerow(['Nakladnoy_ID', 'Date', 'Client', 'Address', 'Plate_Number', 'Driver', 'Recipe', 'Volume_m3', 'Price_AZN', 'Total_AZN', 'Operator'])
            sql = """
                SELECT o.id, o.date, c.name, c.address, v.plate_number, d.name, r.name, o.volume_m3, o.price_per_m3, (o.volume_m3 * o.price_per_m3), op.name 
                FROM orders o JOIN clients c ON o.client_id = c.id JOIN vehicles v ON o.vehicle_id = v.id LEFT JOIN drivers d ON v.driver_id = d.id JOIN recipes r ON o.recipe_id = r.id LEFT JOIN operators op ON o.operator_id = op.id 
                WHERE date(o.date) BETWEEN date(?) AND date(?)
            """
            params = [start_date, end_date]
            if filter_driver:
                sql += " AND v.driver_id = ?"; params.append(filter_driver)
            if filter_client:
                sql += " AND o.client_id = ?"; params.append(filter_client)
            if filter_recipe:
                sql += " AND o.recipe_id = ?"; params.append(filter_recipe)
            
            rows = conn.execute(sql, params).fetchall()
            for r in rows:
                cw.writerow(r)
        elif filter_material:
            cw.writerow(['ID', 'Date', 'Operation', 'Material', 'Quantity_kg', 'Partner', 'Note'])
            if filter_material == '__ALL_SILOS__':
                rows = conn.execute("""
                    SELECT id, date, operation_type, material_name, quantity_kg, partner_name, note 
                    FROM stock_movements WHERE date(date) BETWEEN date(?) AND date(?) AND material_name IN ('Silo 1', 'Silo 2', 'Silo 3', 'Silo 4')
                """, [start_date, end_date]).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, date, operation_type, material_name, quantity_kg, partner_name, note 
                    FROM stock_movements WHERE date(date) BETWEEN date(?) AND date(?) AND material_name = ?
                """, [start_date, end_date, filter_material]).fetchall()
            for r in rows:
                cw.writerow(r)
        else:
            cw.writerow(['Driver', 'Plate', 'Trips', 'Total_Volume_m3', 'Total_Amount_AZN'])
            rows = conn.execute("""
                SELECT d.name, v.plate_number, COUNT(o.id), SUM(o.volume_m3), SUM(o.volume_m3 * o.price_per_m3)
                FROM orders o JOIN vehicles v ON o.vehicle_id = v.id JOIN drivers d ON v.driver_id = d.id
                WHERE date(o.date) BETWEEN date(?) AND date(?) GROUP BY d.id, v.id
            """, [start_date, end_date]).fetchall()
            for r in rows:
                cw.writerow(r)

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=report_{start_date}_to_{end_date}.csv"}
    )

@app.route('/reports/print')
def reports_print():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    filter_driver = request.args.get('filter_driver', '')
    filter_client = request.args.get('filter_client', '')
    filter_recipe = request.args.get('filter_recipe', '')
    filter_material = request.args.get('filter_material', '')

    with sqlite3.connect(DB) as conn:
        comp = conn.execute("SELECT * FROM company_info LIMIT 1").fetchone()
        report_title = t['reports']
        table_html = ""
        summary_text = ""

        if filter_driver or filter_client or filter_recipe:
            sql = """
                SELECT o.id, o.date, c.name, c.address, v.plate_number, d.name, r.name, o.volume_m3, (o.volume_m3 * o.price_per_m3), op.name 
                FROM orders o JOIN clients c ON o.client_id = c.id JOIN vehicles v ON o.vehicle_id = v.id LEFT JOIN drivers d ON v.driver_id = d.id JOIN recipes r ON o.recipe_id = r.id LEFT JOIN operators op ON o.operator_id = op.id 
                WHERE date(o.date) BETWEEN date(?) AND date(?)
            """
            params = [start_date, end_date]
            if filter_driver: sql += " AND v.driver_id = ?"; params.append(filter_driver)
            if filter_client: sql += " AND o.client_id = ?"; params.append(filter_client)
            if filter_recipe: sql += " AND o.recipe_id = ?"; params.append(filter_recipe)

            data = conn.execute(sql, params).fetchall()
            total_vol = sum([row[7] for row in data])
            total_amt = sum([row[8] for row in data])
            summary_text = f"{t['order_count']}: <b>{len(data)}</b> | {t['total_volume']}: <b>{total_vol:,.1f} m³</b> | {t['total_amount']}: <b>{total_amt:,.2f} AZN</b>"

            rows = "".join([f"<tr><td>№ {r[0]}</td><td>{r[1][:16].replace('T', ' ')}</td><td>{r[2]} ({r[3] or '-'})</td><td>{r[4]} / {r[5] or '-'}</td><td>{r[6]}</td><td><b>{r[7]} m³</b></td><td>{r[8]:,.2f} AZN</td><td>{r[9] or '-'}</td></tr>" for r in data])
            table_html = f'''<table class="table table-bordered align-middle text-center mb-4"><thead class="table-dark"><tr><th>№ Qaimə</th><th>{t['date']}</th><th>{t['client']} və Ünvan</th><th>{t['mixer']} / Sürücü</th><th>{t['recipe']}</th><th>{t['volume']}</th><th>{t['total_price']}</th><th>{t['operator']}</th></tr></thead><tbody>{rows if rows else f"<tr><td colspan='8'>Məlumat tapılmadı</td></tr>"}</tbody></table>'''

        else:
            driver_stats = conn.execute("SELECT d.name, v.plate_number, COUNT(o.id), SUM(o.volume_m3), SUM(o.volume_m3 * o.price_per_m3) FROM orders o JOIN vehicles v ON o.vehicle_id = v.id JOIN drivers d ON v.driver_id = d.id WHERE date(o.date) BETWEEN date(?) AND date(?) GROUP BY d.id, v.id", [start_date, end_date]).fetchall()
            driver_rows = "".join([f"<tr><td>{ds[0]}</td><td>{ds[1]}</td><td>{ds[2]}</td><td><b>{ds[3]:,.1f} m³</b></td><td><b>{ds[4]:,.2f} AZN</b></td></tr>" for ds in driver_stats])
            table_html = f'''<h5 class="fw-bold text-dark mt-3">{t['driver_rep']}</h5><table class="table table-bordered align-middle text-center mb-4"><thead class="table-dark"><tr><th>{t['drivers']}</th><th>{t['mixer']}</th><th>{t['trips']}</th><th>{t['total_volume']}</th><th>{t['total_price']}</th></tr></thead><tbody>{driver_rows if driver_rows else f"<tr><td colspan='5'>Məlumat tapılmadı</td></tr>"}</tbody></table>'''

    comp_name, comp_addr = (comp[1], comp[2]) if comp else ('Industrial Automation', '', '')

    content = f'''
    <div class="card p-4 bg-white text-dark mx-auto my-4 shadow-sm" style="max-width: 950px;">
        <div class="text-center border-bottom pb-3 mb-4">
            <h2 class="fw-bold text-dark m-0">🏗️ {comp_name}</h2>
            <p class="text-muted m-0">📍 {comp_addr}</p>
            <h4 class="text-uppercase fw-bold mt-3">{report_title}</h4>
            <p class="text-muted small">{t['start_date']}: <b>{start_date}</b> / {t['end_date']}: <b>{end_date}</b></p>
        </div>
        
        {table_html}
        
        <div class="d-flex justify-content-between align-items-center mt-4 pt-3 border-top">
            <p class="fs-5 m-0">{summary_text}</p>
            <p class="m-0">İmza: _______________</p>
        </div>
        
        <div class="text-center mt-4 d-print-none">
            <button onclick="window.print()" class="btn btn-warning btn-lg px-5 fw-bold">{t['print']}</button>
            <button onclick="window.close()" class="btn btn-secondary btn-lg px-4 ms-2">{t['close']}</button>
        </div>
    </div>
    '''
    return render_page(content, t, lang, hide_nav=True)

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
                <div class="mb-2"><label>{t['client']}</label><select id="scadaClient" class="form-select" required><option value="">...</option>{client_opts}</select></div>
                <div class="mb-2"><label>{t['recipe']}</label><select id="scadaRecipe" class="form-select">{recipe_opts}</select></div>
                <div class="mb-2"><label>{t['mixer']}</label><select id="scadaMixer" class="form-select" onchange="updateVolumeFromMixer(this)"><option value="">...</option>{mixer_opts}</select></div>
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
    function updateVolumeFromMixer(selectEl) {{
        let opt = selectEl.options[selectEl.selectedIndex];
        let cap = opt.getAttribute("data-capacity");
        if (cap) {{
            document.getElementById("scadaVolume").value = cap;
        }}
    }}
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
            
            fetch("/orders/add", {{ 
                method: "POST", 
                headers: {{ "X-Requested-With": "XMLHttpRequest" }},
                body: formData 
            }}).then(res => res.json()).then(data => {{
                setTimeout(() => {{ window.location.href = "/orders"; }}, 1000);
            }});
        }}, 6000);
    }}
    function emergencyStop() {{
        document.getElementById("processStatus").innerText = "🛑 ESTOP!";
        document.getElementById("progressBar").className = "progress-bg bg-danger fw-bold";
        document.getElementById("progressBar").innerText = "STOP";
        logMessage("🚨 E-STOP!");
    }}
    </script>'''
    return render_page(content, t, lang)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)
