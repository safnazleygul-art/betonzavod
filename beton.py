@app.route('/orders', methods=['GET', 'POST'])
def orders():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    
    with get_db() as conn:
        if request.method == 'POST' and 'add_order' in request.form:
            try:
                rec_id = request.form['recipe_id']
                vol = float(request.form['volume_m3'])
                
                r = conn.execute("SELECT * FROM recipes WHERE id=?", (rec_id,)).fetchone()
                if r:
                    req = {
                        'bunker_1': r[2]*vol, 'bunker_2': r[3]*vol, 'bunker_3': r[4]*vol, 'bunker_4': r[5]*vol,
                        'silo_1': r[6]*vol, 'silo_2': r[7]*vol, 'silo_3': r[8]*vol, 'silo_4': r[9]*vol,
                        'water': r[10]*vol
                    }
                    cement_total = (r[6]+r[7]+r[8]+r[9])*vol
                    req['additive'] = cement_total * (r[11]/100.0)

                    insufficient = []
                    for code, needed in req.items():
                        stock_row = conn.execute("SELECT current_kg, code_name FROM stock WHERE code_name=?", (code,)).fetchone()
                        if stock_row and stock_row[0] < needed:
                            mat_name = get_labels().get(code, code)
                            insufficient.append(f"{mat_name}: нужно {needed:.1f} кг, есть {stock_row[0]:.1f} кг")
                    
                    if insufficient:
                        flash(f"{t['insufficient_stock']} <br> " + "<br>".join(insufficient), "error")
                        return redirect('/orders')

                    for code, needed in req.items():
                        conn.execute("UPDATE stock SET current_kg = current_kg - ? WHERE code_name=?", (needed, code))

                conn.execute("""
                    INSERT INTO orders (date, client_id, vehicle_id, recipe_id, volume_m3, price_per_m3, operator_id, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'Tamamlandı')
                """, (datetime.now().isoformat(), request.form['client_id'], request.form['vehicle_id'], rec_id, vol, float(request.form['price_per_m3']), request.form['operator_id']))
                conn.commit()
                flash("Sifariş uğurla təsdiqləndi!", "success")
            except Exception as e:
                flash(f"Error: {str(e)}", "error")
            return redirect('/orders')

        # GET запрос
        try:
            orders_list = conn.execute('''
                SELECT o.id, o.date, c.name, v.plate_number, v.tare_weight_kg, r.name, o.volume_m3, o.price_per_m3, (o.volume_m3 * o.price_per_m3), op.name, o.status,
                       r.bunker_1, r.bunker_2, r.bunker_3, r.bunker_4, r.silo_1, r.silo_2, r.silo_3, r.silo_4, r.water, r.qatki_percent
                FROM orders o
                LEFT JOIN clients c ON o.client_id = c.id
                LEFT JOIN vehicles v ON o.vehicle_id = v.id
                LEFT JOIN recipes r ON o.recipe_id = r.id
                LEFT JOIN operators op ON o.operator_id = op.id
                ORDER BY o.date DESC
            ''').fetchall()
            
            clients = conn.execute("SELECT id, name FROM clients").fetchall()
            vehicles = conn.execute("SELECT id, plate_number, tare_weight_kg FROM vehicles").fetchall()
            recipes = conn.execute("SELECT id, name FROM recipes").fetchall()
            operators = conn.execute("SELECT id, name FROM operators").fetchall()
        except Exception as e:
            flash(f"Error loading data: {str(e)}", "error")
            orders_list, clients, vehicles, recipes, operators = [], [], [], [], []

    rows = ""
    for o in orders_list:
        try:
            vol = o[6]
            cement_total = (o[15]+o[16]+o[17]+o[18]) * vol if o[15] else 0
            additive_kg = cement_total * (o[20]/100.0) if o[20] else 0
            c_weight = (o[11]+o[12]+o[13]+o[14] + cement_total + o[19] + additive_kg) if o[11] else 0
            
            tare = o[4] if o[4] else 12000.0
            gross = tare + c_weight

            rows += f"""<tr>
                <td>{o[0]}</td>
                <td>{o[1][:16] if o[1] else ''}</td>
                <td><b>{o[2] or ''}</b></td>
                <td>{o[3] or ''} <br><small class='text-muted'>Tara: {tare:,.0f} kq</small></td>
                <td>{o[5] or ''}</td>
                <td><b>{o[6]} m³</b><br><small class='text-info'>Net: {c_weight:,.0f} kq</small></td>
                <td class='text-warning fw-bold'>{gross:,.0f} kq</td>
                <td class='text-success fw-bold'>{o[8]:.2f} AZN</td>
                <td>{o[9] or ''}</td>
                <td><span class='badge bg-success'>{o[10] or ''}</span></td>
                <td>
                    <a href='/orders/waybill/{o[0]}' class='btn btn-info btn-sm me-1' target='_blank'>📄 {t['waybill']}</a>
                    <a href='/orders/delete/{o[0]}' class='btn btn-danger btn-sm' onclick="return confirm('Silmək?')">🗑️</a>
                </td>
            </tr>"""
        except:
            continue

    client_opts = "".join([f"<option value='{c[0]}'>{c[1]}</option>" for c in clients])
    veh_opts = "".join([f"<option value='{v[0]}'>{v[1]} (Tara: {v[2]} kq)</option>" for v in vehicles])
    rec_opts = "".join([f"<option value='{r[0]}'>{r[1]}</option>" for r in recipes])
    op_opts = "".join([f"<option value='{op[0]}'>{op[1]}</option>" for op in operators])

    content = f'''
    <h2 class="text-warning mb-4">📦 {t['orders']}</h2>
    <div class="card p-4 shadow mb-4 border-warning">
        <h5 class="text-warning mb-3">➕ {t['add']} {t['orders'].lower()}</h5>
        <form method="POST">
            <input type="hidden" name="add_order" value="1">
            <div class="row g-3">
                <div class="col-md-3"><label>{t['client']}</label><select name="client_id" class="form-select">{client_opts}</select></div>
                <div class="col-md-3"><label>{t['mixer']}</label><select name="vehicle_id" class="form-select">{veh_opts}</select></div>
                <div class="col-md-3"><label>{t['recipe']}</label><select name="recipe_id" class="form-select">{rec_opts}</select></div>
                <div class="col-md-3"><label>{t['operator']}</label><select name="operator_id" class="form-select">{op_opts}</select></div>
                <div class="col-md-4"><label>{t['volume']}</label><input type="number" step="0.5" name="volume_m3" class="form-control" value="10.0" required></div>
                <div class="col-md-4"><label>{t['price_m3']}</label><input type="number" step="1" name="price_per_m3" class="form-control" value="110" required></div>
                <div class="col-md-4 d-flex align-items-end">
                    <button type="submit" class="btn btn-warning w-100 fw-bold">{t['confirm_order']}</button>
                </div>
            </div>
        </form>
    </div>

    <div class="card p-4 shadow">
        <div class="table-responsive">
            <table class="table table-striped table-hover align-middle">
                <thead class="table-dark">
                    <tr><th>{t['id']}</th><th>{t['date']}</th><th>{t['client']}</th><th>{t['mixer']}</th><th>{t['recipe']}</th><th>Vol / Net</th><th>Brutto</th><th>{t['total_price']}</th><th>{t['operator']}</th><th>Status</th><th>{t['action']}</th></tr>
                </thead>
                <tbody>{rows if rows else "<tr><td colspan='11' class='text-center text-muted'>Sifariş yoxdur.</td></tr>"}</tbody>
            </table>
        </div>
    </div>
    '''
    return render_page(content, t, lang)

@app.route('/orders/waybill/<int:id>')
def waybill(id):
    lang = get_lang()
    t = TRANSLATIONS[lang]
    try:
        with get_db() as conn:
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
    except:
        return "Error", 500

    if not o:
        return "Sənəd tapılmadı", 404
    
    try:
        vol = o[8]
        cement_total = (o[14]+o[15]+o[16]+o[17]) * vol
        additive_kg = cement_total * (o[19]/100.0)
        c_weight = (o[10]+o[11]+o[12]+o[13] + cement_total + o[18] + additive_kg)
        tare = o[5] if o[5] else 12000.0
        gross = tare + c_weight
    except:
        return "Error calculating weights", 500

    comp_name = comp[1] if comp else "Beton Zavod"
    comp_addr = comp[2] if comp else ""
    comp_phone = comp[3] if comp else ""
    comp_tax = comp[4] if comp else ""

    html = f"""
    <!DOCTYPE html>
    <html lang="{lang}">
    <head>
        <meta charset="UTF-8">
        <title>{t['waybill']} #{o[0]}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background: #e9ecef; color: #000; font-family: 'Times New Roman', Times, serif; }}
            .a4-page {{ background: #fff; width: 210mm; min-height: 297mm; padding: 15mm; margin: 20px auto; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px; }}
            .header h2 {{ margin: 0; font-size: 18pt; font-weight: bold; text-transform: uppercase; }}
            .header p {{ margin: 2px 0; font-size: 10pt; }}
            .doc-title {{ text-align: center; font-size: 16pt; font-weight: bold; margin: 20px 0; text-decoration: underline; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; font-size: 11pt; }}
            .info-item {{ border-bottom: 1px dotted #000; padding-bottom: 2px; }}
            .info-label {{ font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 11pt; }}
            th, td {{ border: 1px solid #000; padding: 8px; text-align: center; }}
            th {{ background-color: #f0f0f0; font-weight: bold; }}
            .signatures {{ margin-top: 40px; display: flex; justify-content: space-between; font-size: 11pt; }}
            .sig-block {{ width: 45%; text-align: center; }}
            .sig-line {{ border-top: 1px solid #000; margin-top: 30px; padding-top: 5px; }}
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
            <button class="btn btn-primary btn-lg" onclick="window.print()">️ Çap Et / Печать</button>
            <a href="/orders" class="btn btn-secondary btn-lg">Geri / Назад</a>
        </div>
        <div class="a4-page">
            <div class="header">
                <h2>{comp_name}</h2>
                <p>{comp_addr} | Tel: {comp_phone} | VÖEN/ИНН: {comp_tax}</p>
            </div>
            
            <div class="doc-title">{t['waybill'].upper()} № {o[0]}</div>
            
            <div class="info-grid">
                <div><span class="info-label">Tarix / Дата:</span> {o[1][:16] if o[1] else ''}</div>
                <div><span class="info-label">Mikser / Авто:</span> {o[4] or ''}</div>
                <div><span class="info-label">{t['client']}:</span> {o[2] or ''}</div>
                <div><span class="info-label">Sürücü / Водитель:</span> {o[6] or ''}</div>
                <div><span class="info-label">Ünvan / Адрес:</span> {o[3] or ''}</div>
                <div><span class="info-label">Operator:</span> {o[9] or ''}</div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>{t['product_name']}</th>
                        <th>Həcm / Объем (m³)</th>
                        <th>{t['tare_weight']} (kq)</th>
                        <th>{t['concrete_weight']} (kq)</th>
                        <th>{t['gross_weight']} (kq)</th>
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
                    <div>{t['delivered_by']}:</div>
                    <div class="sig-line">{o[9] or ''}</div>
                </div>
                <div class="sig-block">
                    <div>{t['received_by']}:</div>
                    <div class="sig-line">{o[2] or ''}</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/orders/delete/<int:id>')
def delete_order(id):
    with get_db() as conn:
        conn.execute("DELETE FROM orders WHERE id=?", (id,))
        conn.commit()
    return redirect('/orders')

@app.route('/reports')
def reports():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    labels = get_labels()

    driver_filter = request.args.get('driver', '')
    vehicle_filter = request.args.get('vehicle', '')

    with get_db() as conn:
        try:
            drivers = conn.execute("SELECT id, name FROM drivers").fetchall()
            vehicles = conn.execute("SELECT id, plate_number FROM vehicles").fetchall()

            query = '''
                SELECT o.id, o.date, c.name, v.plate_number, d.name, r.name, o.volume_m3, (o.volume_m3 * o.price_per_m3), op.name
                FROM orders o
                LEFT JOIN clients c ON o.client_id = c.id
                LEFT JOIN vehicles v ON o.vehicle_id = v.id
                LEFT JOIN drivers d ON v.driver_id = d.id
                LEFT JOIN recipes r ON o.recipe_id = r.id
                LEFT JOIN operators op ON o.operator_id = op.id
                WHERE 1=1
            '''
            params = []
            if driver_filter:
                query += " AND d.id = ?"
                params.append(driver_filter)
            if vehicle_filter:
                query += " AND v.id = ?"
                params.append(vehicle_filter)
            query += " ORDER BY o.date DESC"

            filtered_orders = conn.execute(query, params).fetchall()
            stock_list = conn.execute("SELECT material_type, code_name, current_kg, max_capacity_kg FROM stock").fetchall()
        except:
            filtered_orders, stock_list, drivers, vehicles = [], [], [], []

    ord_rows = ""
    total_vol = 0
    total_amt = 0
    for ord_item in filtered_orders:
        try:
            total_vol += ord_item[6]
            total_amt += ord_item[7]
            ord_rows += f"""<tr>
                <td>{ord_item[0]}</td><td>{ord_item[1][:16] if ord_item[1] else ''}</td><td><b>{ord_item[2] or ''}</b></td>
                <td>{ord_item[3] or ''}</td><td>{ord_item[4] or ''}</td><td>{ord_item[5] or ''}</td>
                <td>{ord_item[6]} m³</td><td class='text-warning fw-bold'>{ord_item[7]:.2f} AZN</td><td>{ord_item[8] or ''}</td>
            </tr>"""
        except:
            continue

    stock_rows = ""
    for s in stock_list:
        try:
            pct = min(100, max(0, int((s[2] / s[3]) * 100))) if s[3] > 0 else 0
            color = "bg-success" if pct > 30 else "bg-warning" if pct > 15 else "bg-danger"
            stock_rows += f"""<tr>
                <td><span class='badge bg-secondary'>{s[0]}</span></td>
                <td><b>{labels.get(s[1], s[1])}</b></td>
                <td class='text-warning fw-bold'>{s[2]:,.1f} kq</td>
                <td>{s[3]:,.1f} kq</td>
                <td><div class='progress bg-dark' style='height: 15px;'><div class='progress-bar {color}' style='width: {pct}%;'>{pct}%</div></div></td>
            </tr>"""
        except:
            continue

    driver_opts = "".join([f"<option value='{d[0]}' {'selected' if driver_filter==str(d[0]) else ''}>{d[1]}</option>" for d in drivers])
    veh_opts = "".join([f"<option value='{v[0]}' {'selected' if vehicle_filter==str(v[0]) else ''}>{v[1]}</option>" for v in vehicles])

    content = f'''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="text-warning mb-0">📊 {t['reports']}</h2>
        <a href="/reports/export?driver={driver_filter}&vehicle={vehicle_filter}" class="btn btn-success fw-bold">{t['export_csv']}</a>
    </div>

    <div class="card p-4 shadow mb-4 border-info">
        <form method="GET" class="row g-3">
            <div class="col-md-4">
                <label>Sürücü / Водитель</label>
                <select name="driver" class="form-select"><option value="">Bütün / Все</option>{driver_opts}</select>
            </div>
            <div class="col-md-4">
                <label>Maşın / Авто</label>
                <select name="vehicle" class="form-select"><option value="">Bütün / Все</option>{veh_opts}</select>
            </div>
            <div class="col-md-4 d-flex align-items-end">
                <button type="submit" class="btn btn-info w-100 fw-bold text-white">🔍 Filtrlə / Фильтр</button>
            </div>
        </form>
    </div>

    <div class="row mb-4">
        <div class="col-md-5">
            <div class="card p-4 shadow border-warning h-100">
                <h5 class="text-warning mb-3">⚖️ {t['total_price']} və Həcm</h5>
                <p class="fs-5">Reyslərin Sayı: <b>{len(filtered_orders)}</b></p>
                <p class="fs-5">Ümumi Həcm: <span class="text-warning fw-bold">{total_vol:,.1f} m³</span></p>
                <p class="fs-5">Ümumi Məbləğ: <span class="text-success fw-bold">{total_amt:,.2f} AZN</span></p>
            </div>
        </div>
        <div class="col-md-7">
            <div class="card p-4 shadow border-success h-100">
                <h5 class="text-success mb-3">🪨 Anbar Qalıqları</h5>
                <div class="table-responsive" style="max-height: 200px; overflow-y: auto;">
                    <table class="table table-striped table-sm mb-0">
                        <thead class="table-dark"><tr><th>Tip</th><th>Ad</th><th>Qalıq</th><th>Maks</th><th>%</th></tr></thead>
                        <tbody>{stock_rows if stock_rows else "<tr><td colspan='5' class='text-center'>Məlumat yoxdur</td></tr>"}</tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <div class="card p-4 shadow border-secondary">
        <h5 class="text-light mb-3">📋 Reys Tarixçəsi</h5>
        <div class="table-responsive">
            <table class="table table-striped table-hover align-middle">
                <thead class="table-dark">
                    <tr><th>ID</th><th>Tarix</th><th>Müştəri</th><th>Maşın</th><th>Sürücü</th><th>Resept</th><th>Həcm</th><th>Məbləğ</th><th>Operator</th></tr>
                </thead>
                <tbody>{ord_rows if ord_rows else "<tr><td colspan='9' class='text-center text-muted'>Məlumat yoxdur</td></tr>"}</tbody>
            </table>
        </div>
    </div>
    '''
    return render_page(content, t, lang)

@app.route('/reports/export')
def export_reports():
    driver_filter = request.args.get('driver', '')
    vehicle_filter = request.args.get('vehicle', '')

    with get_db() as conn:
        query = '''
            SELECT o.date, c.name, v.plate_number, d.name, r.name, o.volume_m3, (o.volume_m3 * o.price_per_m3), op.name
            FROM orders o
            LEFT JOIN clients c ON o.client_id = c.id
            LEFT JOIN vehicles v ON o.vehicle_id = v.id
            LEFT JOIN drivers d ON v.driver_id = d.id
            LEFT JOIN recipes r ON o.recipe_id = r.id
            LEFT JOIN operators op ON o.operator_id = op.id
            WHERE 1=1
        '''
        params = []
        if driver_filter:
            query += " AND d.id = ?"
            params.append(driver_filter)
        if vehicle_filter:
            query += " AND v.id = ?"
            params.append(vehicle_filter)
        query += " ORDER BY o.date DESC"
        
        try:
            data = conn.execute(query, params).fetchall()
        except:
            data = []

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Date', 'Client', 'Vehicle', 'Driver', 'Recipe', 'Volume_m3', 'Total_Price_AZN', 'Operator'])
    for row in data:
        cw.writerow(row)

    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=reports_export.csv"})

@app.route('/recipes', methods=['GET', 'POST'])
def recipes():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    labels = get_labels()
    
    with get_db() as conn:
        if request.method == 'POST' and 'add_recipe' in request.form:
            try:
                conn.execute("""
                    INSERT INTO recipes (name, bunker_1, bunker_2, bunker_3, bunker_4, silo_1, silo_2, silo_3, silo_4, water, qatki_percent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (request.form['name'], float(request.form['b1']), float(request.form['b2']), float(request.form['b3']), 
                      float(request.form['b4']), float(request.form['s1']), float(request.form['s2']), float(request.form['s3']), 
                      float(request.form['s4']), float(request.form['water']), float(request.form['qatki'])))
                conn.commit()
            except Exception as e:
                flash(f"Error: {str(e)}", "error")
            return redirect('/recipes')

        try:
            recipes_list = conn.execute("SELECT * FROM recipes").fetchall()
        except:
            recipes_list = []

    rows = ""
    for r in recipes_list:
        try:
            total_cement = r[6] + r[7] + r[8] + r[9]
            additive_kg = total_cement * (r[11] / 100.0)
            total_weight_m3 = r[2] + r[3] + r[4] + r[5] + total_cement + r[10] + additive_kg
            
            rows += f"""<tr>
                <td>{r[0]}</td><td><b>{r[1]}</b></td>
                <td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td>
                <td>{r[6]}</td><td>{r[7]}</td><td>{r[8]}</td><td>{r[9]}</td>
                <td>{r[10]}</td>
                <td><b>{r[11]}%</b> <span class='text-info'>({additive_kg:.1f} kq)</span></td>
                <td class='text-warning fw-bold'>{total_weight_m3:,.1f} kq</td>
                <td>
                    <a href='/recipes/delete/{r[0]}' class='btn btn-danger btn-sm' onclick="return confirm('Silmək?')">️</a>
                </td>
            </tr>"""
        except:
            continue

    content = f'''
    <h2 class="text-warning mb-4">🧪 {t['recipes']}</h2>
    <div class="card p-4 shadow mb-4 border-warning">
        <h5 class="text-warning mb-3">➕ {t['add']} {t['recipes'].lower()}</h5>
        <form method="POST">
            <input type="hidden" name="add_recipe" value="1">
            <div class="row g-2">
                <div class="col-md-3"><label>Adı / Название</label><input type="text" name="name" class="form-control" placeholder="M-350" required></div>
                <div class="col-md-1"><label>{labels['bunker_1']}</label><input type="number" step="1" name="b1" class="form-control" value="450" required></div>
                <div class="col-md-1"><label>{labels['bunker_2']}</label><input type="number" step="1" name="b2" class="form-control" value="350" required></div>
                <div class="col-md-1"><label>{labels['bunker_3']}</label><input type="number" step="1" name="b3" class="form-control" value="250" required></div>
                <div class="col-md-1"><label>{labels['bunker_4']}</label><input type="number" step="1" name="b4" class="form-control" value="150" required></div>
                <div class="col-md-1"><label>{labels['silo_1']}</label><input type="number" step="1" name="s1" class="form-control" value="300" required></div>
                <div class="col-md-1"><label>{labels['silo_2']}</label><input type="number" step="1" name="s2" class="form-control" value="100" required></div>
                <div class="col-md-1"><label>{labels['silo_3']}</label><input type="number" step="1" name="s3" class="form-control" value="0"></div>
                <div class="col-md-1"><label>{labels['silo_4']}</label><input type="number" step="1" name="s4" class="form-control" value="0"></div>
                <div class="col-md-1"><label>{labels['water']}</label><input type="number" step="1" name="water" class="form-control" value="170" required></div>
                <div class="col-md-1"><label>{labels['additive']} (%)</label><input type="number" step="0.1" name="qatki" class="form-control" value="1.5" required></div>
            </div>
            <button type="submit" class="btn btn-warning w-100 fw-bold mt-3">💾 {t['save']}</button>
        </form>
    </div>
    <div class="card p-4 shadow">
        <div class="table-responsive">
            <table class="table table-striped table-hover align-middle text-center">
                <thead class="table-dark">
                    <tr><th>ID</th><th>Marka</th><th>{labels['bunker_1']}</th><th>{labels['bunker_2']}</th><th>{labels['bunker_3']}</th><th>{labels['bunker_4']}</th>
                    <th>{labels['silo_1']}</th><th>{labels['silo_2']}</th><th>{labels['silo_3']}</th><th>{labels['silo_4']}</th><th>{labels['water']}</th><th>{labels['additive']}</th><th class="text-warning">Ümumi (kq)</th><th>{t['action']}</th></tr>
                </thead>
                <tbody>{rows if rows else "<tr><td colspan='14' class='text-center text-muted'>Resept yoxdur</td></tr>"}</tbody>
            </table>
        </div>
    </div>'''
    return render_page(content, t, lang)

@app.route('/recipes/delete/<int:id>')
def delete_recipe(id):
    with get_db() as conn:
        conn.execute("DELETE FROM recipes WHERE id=?", (id,))
        conn.commit()
    return redirect('/recipes')

@app.route('/stock')
def stock():
    lang = get_lang()
    t = TRANSLATIONS[lang]
    labels = get_labels()
    with get_db() as conn:
        if request.method == 'POST' and 'update_stock' in request.form:
            conn.execute("UPDATE stock SET current_kg=? WHERE id=?", (float(request.form['current_kg']), request.form['stock_id']))
            conn.commit()
            return redirect('/stock')
        try:
            stock_list = conn.execute("SELECT * FROM stock").fetchall()
        except:
            stock_list = []

    rows = ""
    for s in stock_list:
        try:
            pct = min(100, max(0, int((s[3] / s[4]) * 100))) if s[4] > 0 else 0
            color = "bg-success" if pct > 30 else "bg-warning" if pct > 15 else "bg-danger"
            rows += f"""<tr>
                <td>{s[0]}</td><td><span class='badge bg-secondary'>{s[1]}</span></td><td><b>{labels.get(s[2], s[2])}</b></td>
                <td class='text-warning fw-bold'>{s[3]:,.1f} kq</td><td>{s[4]:,.1f} kq</td>
                <td><div class='progress bg-dark' style='height: 20px;'><div class='progress-bar {color}' style='width: {pct}%;'>{pct}%</div></div></td>
                <td>
                    <form method='POST' class='d-inline-flex gap-1'>
                        <input type='hidden' name='update_stock' value='1'><input type='hidden' name='stock_id' value='{s[0]}'>
                        <input type='number' step='100' name='current_kg' class='form-control form-control-sm' value='{s[3]}' style='width: 100px;' required>
                        <button type='submit' class='btn btn-warning btn-sm'>💾</button>
                    </form>
                </td>
            </tr>"""
        except:
            continue

    content = f'''
    <h2 class="text-warning mb-4">🪨 {t['stock']}</h2>
    <div class="card p-4 shadow">
        <div class="table-responsive">
            <table class="table table-striped table-hover align-middle">
                <thead class="table-dark"><tr><th>ID</th><th>Tip</th><th>Ad</th><th>{t['current_stock']}</th><th>{t['max_capacity']}</th><th>Doluluk</th><th>{t['action']}</th></tr></thead>
                <tbody>{rows if rows else "<tr><td colspan='7' class='text-center text-muted'>Məlumat yoxdur</td></tr>"}</tbody>
            </table>
        </div>
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
            <div class="card p-5 shadow mb-4 bg-black border-warning text-center">
                <h3 class="text-warning">Beton Batching Plant SCADA Mimik Diaqramı</h3>
                <p class="text-muted">PLC IP: 192.168.1.50 | Modbus TCP Online</p>
                <div class="py-4">
                    <a href="#" class="btn btn-success btn-lg fw-bold px-5 me-3">▶️ İstehsalı Başla (START)</a>
                    <a href="#" class="btn btn-danger btn-lg fw-bold px-5"> QƏZA DAYANMASI (ESTOP)</a>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-4 shadow border-info">
                <h5 class="text-info mb-3">Rejim / Fazalar</h5>
                <ul class="list-group list-group-flush bg-transparent">
                    <li class="list-group-item bg-transparent text-light border-secondary">1. Dozaj (Bunkerlər & Silolar): <span class="badge bg-success">Hazırdır</span></li>
                    <li class="list-group-item bg-transparent text-light border-secondary">2. Konveyyər və Mikser Yükləmə: <span class="badge bg-secondary">Gözləyir</span></li>
                    <li class="list-group-item bg-transparent text-light border-secondary">3. Zames və Boşalma: <span class="badge bg-secondary">Gözləyir</span></li>
                </ul>
            </div>
        </div>
    </div>'''
    return render_page(content, t, lang)

# Generic CRUD helpers
def render_crud(table_name, display_name, fields, t):
    lang = get_lang()
    with get_db() as conn:
        if request.method == 'POST' and 'add' in request.form:
            try:
                cols = ", ".join(fields.keys())
                vals = ", ".join(["?" for _ in fields])
                data = [request.form[k] for k in fields.keys()]
                conn.execute(f"INSERT INTO {table_name} ({cols}) VALUES ({vals})", data)
                conn.commit()
            except Exception as e:
                flash(f"Error: {str(e)}", "error")
            return redirect(f'/{table_name}')
        
        try:
            rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
        except:
            rows = []
    
    rows_html = ""
    for r in rows:
        cells = "".join([f"<td>{r[i] if r[i] is not None else ''}</td>" for i in range(1, len(r))])
        rows_html += f"<tr><td>{r[0]}</td>{cells}<td><a href='/{table_name}/delete/{r[0]}' class='btn btn-danger btn-sm' onclick='return confirm(\"Silmək?\")'>🗑️</a></td></tr>"
    
    form_fields = ""
    for key, label in fields.items():
        form_fields += f'<div class="col-md-4 mb-2"><label>{label}</label><input type="text" name="{key}" class="form-control" required></div>'

    content = f'''
    <h2 class="text-warning mb-4">📂 {display_name}</h2>
    <div class="card p-4 shadow mb-4 border-warning">
        <h5 class="text-warning mb-3">➕ {t['add']}</h5>
        <form method="POST"><input type="hidden" name="add" value="1"><div class="row">{form_fields}</div>
        <button type="submit" class="btn btn-warning w-100 fw-bold mt-2">{t['save']}</button></form>
    </div>
    <div class="card p-4 shadow"><table class="table table-striped"><thead class="table-dark"><tr><th>ID</th>
    {"".join([f"<th>{label}</th>" for label in fields.values()])}<th>{t['action']}</th></tr></thead><tbody>{rows_html if rows_html else "<tr><td colspan='" + str(len(fields) + 2) + "' class='text-center text-muted'>Məlumat yoxdur</td></tr>"}</tbody></table></div>'''
    return render_page(content, t, lang)

@app.route('/operators', methods=['GET', 'POST'])
def operators(): 
    return render_crud('operators', TRANSLATIONS[get_lang()]['operators'], {'name': 'Ad Soyad', 'phone': 'Telefon'}, TRANSLATIONS[get_lang()])

@app.route('/drivers', methods=['GET', 'POST'])
def drivers(): 
    return render_crud('drivers', TRANSLATIONS[get_lang()]['drivers'], {'name': 'Ad Soyad', 'phone': 'Telefon', 'license_number': 'Vəsiqə №'}, TRANSLATIONS[get_lang()])

@app.route('/clients', methods=['GET', 'POST'])
def clients(): 
    return render_crud('clients', TRANSLATIONS[get_lang()]['clients'], {'name': 'Firma Adı', 'contact': 'Əlaqə', 'address': 'Ünvan'}, TRANSLATIONS[get_lang()])

@app.route('/<table_name>/delete/<int:id>')
def delete_generic(table_name, id):
    with get_db() as conn:
        conn.execute(f"DELETE FROM {table_name} WHERE id=?", (id,))
        conn.commit()
    return redirect(f'/{table_name}')

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
