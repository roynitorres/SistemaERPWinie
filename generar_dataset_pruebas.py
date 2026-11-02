import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def build_test_workbook():
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # Styles
    font_banner_title = Font(name='Segoe UI', size=15, bold=True, color='FFFFFF')
    font_banner_sub = Font(name='Segoe UI', size=10, italic=True, color='E0E7FF')
    font_th = Font(name='Segoe UI', size=10, bold=True, color='FFFFFF')
    font_td = Font(name='Segoe UI', size=9, color='1E293B')
    font_td_bold = Font(name='Segoe UI', size=9, bold=True, color='0F172A')
    font_td_code = Font(name='Consolas', size=9, bold=True, color='0047AB')
    font_total = Font(name='Segoe UI', size=10, bold=True, color='0047AB')

    fill_banner = PatternFill(start_color='0047AB', end_color='0047AB', fill_type='solid')
    fill_th = PatternFill(start_color='1E3A8A', end_color='1E3A8A', fill_type='solid')
    fill_zebra = PatternFill(start_color='F8FAFC', end_color='F8FAFC', fill_type='solid')
    fill_total = PatternFill(start_color='E2E8F0', end_color='E2E8F0', fill_type='solid')
    fill_green = PatternFill(start_color='DCFCE7', end_color='DCFCE7', fill_type='solid')
    fill_yellow = PatternFill(start_color='FEF3C7', end_color='FEF3C7', fill_type='solid')
    fill_info = PatternFill(start_color='EFF6FF', end_color='EFF6FF', fill_type='solid')

    border_thin = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )
    border_total = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='double', color='0047AB')
    )

    align_center = Alignment(horizontal='center', vertical='center')
    align_left = Alignment(horizontal='left', vertical='center')
    align_right = Alignment(horizontal='right', vertical='center')

    def setup_banner(ws, title, subtitle, max_col):
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max_col)
        ws.cell(row=1, column=1, value=title)
        c1 = ws.cell(row=1, column=1)
        c1.font = font_banner_title
        c1.fill = fill_banner
        c1.alignment = Alignment(horizontal='left', vertical='center', indent=1)
        ws.row_dimensions[1].height = 28

        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=max_col)
        ws.cell(row=2, column=1, value=subtitle)
        c2 = ws.cell(row=2, column=1)
        c2.font = font_banner_sub
        c2.fill = fill_banner
        c2.alignment = Alignment(horizontal='left', vertical='center', indent=1)
        ws.row_dimensions[2].height = 20
        ws.row_dimensions[3].height = 10

    def autofit(ws):
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                # ignore merged banner
                if cell.row in [1, 2]:
                    continue
                val = str(cell.value or '')
                if len(val) > max_len:
                    max_len = len(val)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    # =========================================================================
    # HOJA 0: PLAN DE PRUEBA Y AUDITORÍA
    # =========================================================================
    ws0 = wb.create_sheet(title='0. GUÍA DE PRUEBAS')
    setup_banner(ws0, 'PLAN DE PRUEBAS DEL SISTEMA ERP WINIE', 'Sigue este orden secuencial para registrar los datos y verificar que los reportes sean 100% exactos', 6)

    pasos = [
        ('Paso 1', 'Registrar Categorías', 'Ir a Catálogo > Categorías', 'Registrar las 5 categorías definidas en la pestaña 1.'),
        ('Paso 2', 'Registrar Proveedores', 'Ir a Catálogo > Proveedores', 'Registrar los 3 proveedores en la pestaña 2.'),
        ('Paso 3', 'Registrar Productos', 'Ir a Catálogo > Productos > Nuevo', 'Ingresar los 6 productos con stock, costo y margen. Comprobar que el semáforo inicial esté en verde.'),
        ('Paso 4', 'Registrar Clientes', 'Ir a Clientes > Nuevo Cliente', 'Registrar los 4 clientes de prueba con su teléfono y ciudad.'),
        ('Paso 5', 'Registrar Ventas Contado', 'Ir a Ventas / Facturar', 'Realizar las 2 ventas de contado (Venta #1 y Venta #2). Verificar que el stock disminuya y el estado sea PAGADA.'),
        ('Paso 6', 'Registrar Ventas Crédito', 'Ir a Ventas / Facturar (Crédito)', 'Registrar las 2 ventas al crédito (Venta #3 a 2 cuotas y Venta #4 a 4 cuotas). Comprobar plan de cuotas.'),
        ('Paso 7', 'Registrar Cobro / Abono', 'Ir a Cobros / Pagos', 'Registrar el pago de la Cuota 1 de Ricardo Gómez (C$ 755.00). Verificar saldo restante.'),
        ('Paso 8', 'Verificar Reportes y Tablas', 'Ir a Salpicadero / Reportes', 'Comparar los totales del sistema contra la pestaña "7. AUDITORÍA FINAL".')
    ]

    ws0.cell(row=4, column=1, value='ORDEN').font = font_th
    ws0.cell(row=4, column=1).fill = fill_th
    ws0.cell(row=4, column=1).alignment = align_center

    ws0.cell(row=4, column=2, value='FASE DE PRUEBA').font = font_th
    ws0.cell(row=4, column=2).fill = fill_th
    ws0.cell(row=4, column=2).alignment = align_left

    ws0.cell(row=4, column=3, value='MÓDULO DEL SISTEMA').font = font_th
    ws0.cell(row=4, column=3).fill = fill_th
    ws0.cell(row=4, column=3).alignment = align_left

    ws0.merge_cells('D4:F4')
    ws0.cell(row=4, column=4, value='ACCIÓN A EJECUTAR').font = font_th
    ws0.cell(row=4, column=4).fill = fill_th
    ws0.cell(row=4, column=4).alignment = align_left
    ws0.row_dimensions[4].height = 24

    for idx, (p, f, m, a) in enumerate(pasos, start=5):
        fill_r = fill_zebra if idx % 2 == 0 else PatternFill(fill_type=None)
        ws0.cell(row=idx, column=1, value=p).font = font_td_bold
        ws0.cell(row=idx, column=1).alignment = align_center
        ws0.cell(row=idx, column=1).fill = fill_r
        ws0.cell(row=idx, column=1).border = border_thin

        ws0.cell(row=idx, column=2, value=f).font = font_td_bold
        ws0.cell(row=idx, column=2).fill = fill_r
        ws0.cell(row=idx, column=2).border = border_thin

        ws0.cell(row=idx, column=3, value=m).font = font_td
        ws0.cell(row=idx, column=3).fill = fill_r
        ws0.cell(row=idx, column=3).border = border_thin

        ws0.merge_cells(start_row=idx, start_column=4, end_row=idx, end_column=6)
        ws0.cell(row=idx, column=4, value=a).font = font_td
        ws0.cell(row=idx, column=4).fill = fill_r
        for c in range(4, 7):
            ws0.cell(row=idx, column=c).border = border_thin
        ws0.row_dimensions[idx].height = 22

    autofit(ws0)

    # =========================================================================
    # HOJA 1: CATEGORÍAS
    # =========================================================================
    ws1 = wb.create_sheet(title='1. CATEGORÍAS')
    setup_banner(ws1, 'DATOS DE PRUEBA: CATEGORÍAS', 'Ingresar en: Catálogo > Categorías > Nueva Categoría', 4)

    cat_headers = ['CÓDIGO', 'NOMBRE DE CATEGORÍA', 'DESCRIPCIÓN', 'ESTADO']
    ws1.row_dimensions[4].height = 24
    for c_idx, h in enumerate(cat_headers, 1):
        cell = ws1.cell(row=4, column=c_idx, value=h)
        cell.font = font_th
        cell.fill = fill_th
        cell.alignment = align_center if c_idx in [1, 4] else align_left

    categorias_data = [
        ('CAT-001', 'CALZADO', 'Zapatos, zapatillas y sandalias deportivas o casuales', 'ACTIVO'),
        ('CAT-002', 'ROPA', 'Camisas, pantalones, blusas y prendas de vestir', 'ACTIVO'),
        ('CAT-003', 'PERFUMERIA', 'Fragancias y lociones originales para damas y caballeros', 'ACTIVO'),
        ('CAT-004', 'TECNOLOGIA', 'Accesorios móviles, audífonos, smartwatches y cargadores', 'ACTIVO'),
        ('CAT-005', 'ACCESORIOS', 'Relojes, billeteras, fajas y mochilas', 'ACTIVO')
    ]

    for r_idx, row in enumerate(categorias_data, 5):
        fill_r = fill_zebra if r_idx % 2 == 0 else PatternFill(fill_type=None)
        ws1.row_dimensions[r_idx].height = 20
        for c_idx, val in enumerate(row, 1):
            cell = ws1.cell(row=r_idx, column=c_idx, value=val)
            cell.font = font_td_code if c_idx == 1 else (font_td_bold if c_idx == 2 else font_td)
            cell.alignment = align_center if c_idx in [1, 4] else align_left
            cell.fill = fill_r
            cell.border = border_thin

    autofit(ws1)

    # =========================================================================
    # HOJA 2: PROVEEDORES
    # =========================================================================
    ws2 = wb.create_sheet(title='2. PROVEEDORES')
    setup_banner(ws2, 'DATOS DE PRUEBA: PROVEEDORES', 'Ingresar en: Catálogo > Proveedores > Nuevo Proveedor', 8)

    prv_headers = ['CÓDIGO', 'NOMBRE EMPRESA', 'CONTACTO', 'TELÉFONO', 'DEPARTAMENTO', 'MUNICIPIO', 'RUC', 'DIRECCIÓN']
    ws2.row_dimensions[4].height = 24
    for c_idx, h in enumerate(prv_headers, 1):
        cell = ws2.cell(row=4, column=c_idx, value=h)
        cell.font = font_th
        cell.fill = fill_th
        cell.alignment = align_center if c_idx in [1, 4, 7] else align_left

    proveedores_data = [
        ('PRV-001', 'DISTRIBUIDORA EL ÉXITO S.A.', 'Carlos Mendoza', '88554433', 'Managua', 'Managua', 'J0310000123456', 'Semáforos El Mayoreo 2c al Norte'),
        ('PRV-002', 'IMPORTACIONES CENTRAL S.A.', 'María Eugenia López', '77221199', 'Masaya', 'Masaya', 'J0310000654321', 'Parque Central 1c al Este'),
        ('PRV-003', 'TECNO NICARAGUA IMPORT', 'Roberto Morales', '84112233', 'Managua', 'Managua', 'J0310000789012', 'Pista Jean Paul Genie, Edificio B')
    ]

    for r_idx, row in enumerate(proveedores_data, 5):
        fill_r = fill_zebra if r_idx % 2 == 0 else PatternFill(fill_type=None)
        ws2.row_dimensions[r_idx].height = 20
        for c_idx, val in enumerate(row, 1):
            cell = ws2.cell(row=r_idx, column=c_idx, value=val)
            cell.font = font_td_code if c_idx == 1 else (font_td_bold if c_idx == 2 else font_td)
            cell.alignment = align_center if c_idx in [1, 4, 7] else align_left
            cell.fill = fill_r
            cell.border = border_thin

    autofit(ws2)

    # =========================================================================
    # HOJA 3: PRODUCTOS
    # =========================================================================
    ws3 = wb.create_sheet(title='3. PRODUCTOS')
    setup_banner(ws3, 'DATOS DE PRUEBA: CATÁLOGO DE PRODUCTOS', 'Ingresar en: Catálogo > Productos > Registrar Nuevo Producto (Comprobar cálculo automático de ganancia y stock mínimo)', 12)

    prod_headers = [
        'CÓDIGO/SKU', 'NOMBRE DEL PRODUCTO', 'MARCA', 'CATEGORÍA', 'PROVEEDOR',
        'CANT. COMPRA', 'STOCK MÍNIMO', 'COSTO UNIT. (C$)', 'MARGEN %', 'PRECIO VENTA (C$)',
        'GANANCIA UNIT.', 'INVERSIÓN TOTAL'
    ]
    ws3.row_dimensions[4].height = 24
    for c_idx, h in enumerate(prod_headers, 1):
        cell = ws3.cell(row=4, column=c_idx, value=h)
        cell.font = font_th
        cell.fill = fill_th
        cell.alignment = align_center if c_idx in [1, 6, 7, 9] else (align_right if c_idx in [8, 10, 11, 12] else align_left)

    productos_data = [
        ('PROD-001', 'ZAPATILLAS NIKE REVOLUTION 6', 'Nike', 'CALZADO', 'DISTRIBUIDORA EL ÉXITO S.A.', 10, 3, 800.00, 0.35, 1080.00, 280.00, 8000.00),
        ('PROD-002', 'CAMISA POLO CASUAL MANGA CORTA', 'Tommy Hilfiger', 'ROPA', 'IMPORTACIONES CENTRAL S.A.', 15, 4, 350.00, 0.40, 490.00, 140.00, 5250.00),
        ('PROD-003', 'PERFUME 212 VIP MEN 100ML', 'Carolina Herrera', 'PERFUMERIA', 'IMPORTACIONES CENTRAL S.A.', 6, 2, 1200.00, 0.30, 1560.00, 360.00, 7200.00),
        ('PROD-004', 'AUDÍFONOS INALÁMBRICOS BLUETOOTH', 'Lenovo', 'TECNOLOGIA', 'TECNO NICARAGUA IMPORT', 20, 5, 180.00, 0.50, 270.00, 90.00, 3600.00),
        ('PROD-005', 'RELOJ ANALÓGICO SPORT RESISTENTE', 'Casio', 'ACCESORIOS', 'TECNO NICARAGUA IMPORT', 8, 3, 500.00, 0.40, 700.00, 200.00, 4000.00),
        ('PROD-006', 'PANTALÓN JEANS CLÁSICO CABALLERO', "Levi's", 'ROPA', 'IMPORTACIONES CENTRAL S.A.', 12, 4, 600.00, 0.35, 810.00, 210.00, 7200.00)
    ]

    total_cant = 0
    total_inversion = 0

    for r_idx, row in enumerate(productos_data, 5):
        fill_r = fill_zebra if r_idx % 2 == 0 else PatternFill(fill_type=None)
        ws3.row_dimensions[r_idx].height = 20
        total_cant += row[5]
        total_inversion += row[11]

        for c_idx, val in enumerate(row, 1):
            cell = ws3.cell(row=r_idx, column=c_idx, value=val)
            cell.fill = fill_r
            cell.border = border_thin

            if c_idx == 1:
                cell.font = font_td_code
                cell.alignment = align_center
            elif c_idx == 2:
                cell.font = font_td_bold
                cell.alignment = align_left
            elif c_idx in [6, 7]:
                cell.font = font_td_bold
                cell.alignment = align_center
            elif c_idx in [8, 10, 11, 12]:
                cell.font = font_td
                cell.alignment = align_right
                cell.number_format = '"C$" #,##0.00'
            elif c_idx == 9:
                cell.font = font_td_bold
                cell.alignment = align_center
                cell.number_format = '0.0%'
            else:
                cell.font = font_td
                cell.alignment = align_left

    # Total row
    last_r = len(productos_data) + 5
    ws3.row_dimensions[last_r].height = 22
    ws3.cell(row=last_r, column=2, value='TOTALES DE INVENTARIO INICIAL').font = font_total
    ws3.cell(row=last_r, column=2).alignment = align_left

    ws3.cell(row=last_r, column=6, value=total_cant).font = font_total
    ws3.cell(row=last_r, column=6).alignment = align_center

    ws3.cell(row=last_r, column=12, value=total_inversion).font = font_total
    ws3.cell(row=last_r, column=12).alignment = align_right
    ws3.cell(row=last_r, column=12).number_format = '"C$" #,##0.00'

    for col_i in range(1, 13):
        c_tot = ws3.cell(row=last_r, column=col_i)
        c_tot.fill = fill_total
        c_tot.border = border_total

    autofit(ws3)

    # =========================================================================
    # HOJA 4: CLIENTES
    # =========================================================================
    ws4 = wb.create_sheet(title='4. CLIENTES')
    setup_banner(ws4, 'DATOS DE PRUEBA: CLIENTES', 'Ingresar en: Clientes > Nuevo Cliente (Teléfonos válidos de 8 dígitos de Nicaragua)', 6)

    cli_headers = ['CÓDIGO', 'NOMBRES Y APELLIDOS', 'TELÉFONO', 'CIUDAD / MUNICIPIO', 'ESTADO', 'PROPÓSITO DE LA PRUEBA']
    ws4.row_dimensions[4].height = 24
    for c_idx, h in enumerate(cli_headers, 1):
        cell = ws4.cell(row=4, column=c_idx, value=h)
        cell.font = font_th
        cell.fill = fill_th
        cell.alignment = align_center if c_idx in [1, 3, 5] else align_left

    clientes_data = [
        ('CLI-001', 'Juan José Pérez Valle', '88441122', 'Managua', 'ACTIVO', 'Prueba Venta de Contado #1'),
        ('CLI-002', 'Karla Vanessa Somarriba', '78996655', 'Masaya', 'ACTIVO', 'Prueba Venta de Contado #2'),
        ('CLI-003', 'Ricardo Antonio Gómez', '87123456', 'Granada', 'ACTIVO', 'Prueba Venta Crédito (2 cuotas quincenales) + Abono'),
        ('CLI-004', 'Sofía Elena Mercado', '58223344', 'Managua', 'ACTIVO', 'Prueba Venta Crédito (4 cuotas semanales)')
    ]

    for r_idx, row in enumerate(clientes_data, 5):
        fill_r = fill_zebra if r_idx % 2 == 0 else PatternFill(fill_type=None)
        ws4.row_dimensions[r_idx].height = 20
        for c_idx, val in enumerate(row, 1):
            cell = ws4.cell(row=r_idx, column=c_idx, value=val)
            cell.font = font_td_code if c_idx == 1 else (font_td_bold if c_idx == 2 else font_td)
            cell.alignment = align_center if c_idx in [1, 3, 5] else align_left
            cell.fill = fill_r
            cell.border = border_thin

    autofit(ws4)

    # =========================================================================
    # HOJA 5: VENTAS CONTADO
    # =========================================================================
    ws5 = wb.create_sheet(title='5. VENTAS CONTADO')
    setup_banner(ws5, 'DATOS DE PRUEBA: VENTAS DE CONTADO', 'Ingresar en: Ventas / Nueva Venta > Tipo: CONTADO (Efectivo inmediato)', 9)

    vta_headers = [
        'FACTURA #', 'CLIENTE', 'PRODUCTO (SKU)', 'CANTIDAD',
        'PRECIO UNIT. (C$)', 'TOTAL VENTA (C$)', 'COSTO TOTAL (C$)',
        'GANANCIA NETA (C$)', 'ESTADO'
    ]
    ws5.row_dimensions[4].height = 24
    for c_idx, h in enumerate(vta_headers, 1):
        cell = ws5.cell(row=4, column=c_idx, value=h)
        cell.font = font_th
        cell.fill = fill_th
        cell.alignment = align_center if c_idx in [1, 4, 9] else (align_right if c_idx in [5, 6, 7, 8] else align_left)

    ventas_contado_data = [
        ('FAC-001', 'Juan José Pérez Valle', 'PROD-001 (Nike Revolution)', 1, 1080.00, 1080.00, 800.00, 280.00, 'PAGADA'),
        ('FAC-001', 'Juan José Pérez Valle', 'PROD-002 (Polo Tommy)', 2, 490.00, 980.00, 700.00, 280.00, 'PAGADA'),
        ('FAC-002', 'Karla Vanessa Somarriba', 'PROD-003 (Perfume 212 VIP)', 1, 1560.00, 1560.00, 1200.00, 360.00, 'PAGADA'),
        ('FAC-002', 'Karla Vanessa Somarriba', 'PROD-004 (Audífonos Lenovo)', 3, 270.00, 810.00, 540.00, 270.00, 'PAGADA')
    ]

    tot_contado = sum(r[5] for r in ventas_contado_data)
    tot_costo_c = sum(r[6] for r in ventas_contado_data)
    tot_ganancia_c = sum(r[7] for r in ventas_contado_data)

    for r_idx, row in enumerate(ventas_contado_data, 5):
        fill_r = fill_zebra if r_idx % 2 == 0 else PatternFill(fill_type=None)
        ws5.row_dimensions[r_idx].height = 20
        for c_idx, val in enumerate(row, 1):
            cell = ws5.cell(row=r_idx, column=c_idx, value=val)
            cell.fill = fill_r
            cell.border = border_thin

            if c_idx == 1:
                cell.font = font_td_code
                cell.alignment = align_center
            elif c_idx == 4:
                cell.font = font_td_bold
                cell.alignment = align_center
            elif c_idx in [5, 6, 7, 8]:
                cell.font = font_td_bold if c_idx in [6, 8] else font_td
                cell.alignment = align_right
                cell.number_format = '"C$" #,##0.00'
            elif c_idx == 9:
                cell.font = font_td_bold
                cell.fill = fill_green
                cell.alignment = align_center
            else:
                cell.font = font_td
                cell.alignment = align_left

    # Total Contado
    last_r_c = len(ventas_contado_data) + 5
    ws5.row_dimensions[last_r_c].height = 22
    ws5.cell(row=last_r_c, column=2, value='TOTAL VENTAS DE CONTADO').font = font_total
    ws5.cell(row=last_r_c, column=6, value=tot_contado).font = font_total
    ws5.cell(row=last_r_c, column=6).number_format = '"C$" #,##0.00'
    ws5.cell(row=last_r_c, column=6).alignment = align_right

    ws5.cell(row=last_r_c, column=7, value=tot_costo_c).font = font_total
    ws5.cell(row=last_r_c, column=7).number_format = '"C$" #,##0.00'
    ws5.cell(row=last_r_c, column=7).alignment = align_right

    ws5.cell(row=last_r_c, column=8, value=tot_ganancia_c).font = font_total
    ws5.cell(row=last_r_c, column=8).number_format = '"C$" #,##0.00'
    ws5.cell(row=last_r_c, column=8).alignment = align_right

    for c_i in range(1, 10):
        cell_t = ws5.cell(row=last_r_c, column=c_i)
        cell_t.fill = fill_total
        cell_t.border = border_total

    autofit(ws5)

    # =========================================================================
    # HOJA 6: VENTAS CRÉDITO
    # =========================================================================
    ws6 = wb.create_sheet(title='6. VENTAS CRÉDITO')
    setup_banner(ws6, 'DATOS DE PRUEBA: VENTAS AL CRÉDITO Y PLAN DE CUOTAS', 'Ingresar en: Ventas / Nueva Venta > Tipo: CRÉDITO (Genera cuentas por cobrar y calendario de cobro)', 11)

    crd_headers = [
        'FACTURA #', 'CLIENTE', 'PRODUCTO (SKU)', 'CANT.', 'TOTAL VENTA (C$)',
        'FRECUENCIA', 'N° CUOTAS', 'VALOR CUOTA (C$)', 'GANANCIA (C$)', 'ESTADO INICIAL', 'PRUEBA DE PAGO / ABONO'
    ]
    ws6.row_dimensions[4].height = 24
    for c_idx, h in enumerate(crd_headers, 1):
        cell = ws6.cell(row=4, column=c_idx, value=h)
        cell.font = font_th
        cell.fill = fill_th
        cell.alignment = align_center if c_idx in [1, 4, 6, 7, 10] else (align_right if c_idx in [5, 8, 9] else align_left)

    ventas_credito_data = [
        ('FAC-003', 'Ricardo Antonio Gómez', 'PROD-005 (Reloj Casio)', 1, 700.00, 'Quincenal', 2, 755.00, 200.00, 'PENDIENTE', 'PAGAR Cuota 1 (C$ 755.00) en módulo Cobros'),
        ('FAC-003', 'Ricardo Antonio Gómez', "PROD-006 (Jeans Levi's)", 1, 810.00, 'Quincenal', 2, 755.00, 210.00, 'PENDIENTE', 'Cuota 2 queda pendiente (Saldo: C$ 755.00)'),
        ('FAC-004', 'Sofía Elena Mercado', 'PROD-001 (Nike Revolution)', 2, 2160.00, 'Semanal', 4, 607.50, 560.00, 'PENDIENTE', 'Todas las 4 cuotas quedan pendientes'),
        ('FAC-004', 'Sofía Elena Mercado', 'PROD-004 (Audífonos Lenovo)', 1, 270.00, 'Semanal', 4, 607.50, 90.00, 'PENDIENTE', 'Saldo total pendiente de Sofía: C$ 2,430.00')
    ]

    tot_credito = sum(r[4] for r in ventas_credito_data)
    tot_ganancia_cr = sum(r[8] for r in ventas_credito_data)

    for r_idx, row in enumerate(ventas_credito_data, 5):
        fill_r = fill_zebra if r_idx % 2 == 0 else PatternFill(fill_type=None)
        ws6.row_dimensions[r_idx].height = 20
        for c_idx, val in enumerate(row, 1):
            cell = ws6.cell(row=r_idx, column=c_idx, value=val)
            cell.fill = fill_r
            cell.border = border_thin

            if c_idx == 1:
                cell.font = font_td_code
                cell.alignment = align_center
            elif c_idx in [4, 6, 7]:
                cell.font = font_td_bold
                cell.alignment = align_center
            elif c_idx in [5, 8, 9]:
                cell.font = font_td_bold if c_idx in [5, 9] else font_td
                cell.alignment = align_right
                cell.number_format = '"C$" #,##0.00'
            elif c_idx == 10:
                cell.font = font_td_bold
                cell.fill = fill_yellow
                cell.alignment = align_center
            elif c_idx == 11:
                cell.font = font_td_bold
                cell.fill = fill_info
                cell.alignment = align_left
            else:
                cell.font = font_td
                cell.alignment = align_left

    last_r_cr = len(ventas_credito_data) + 5
    ws6.row_dimensions[last_r_cr].height = 22
    ws6.cell(row=last_r_cr, column=2, value='TOTAL VENTAS AL CRÉDITO').font = font_total
    ws6.cell(row=last_r_cr, column=5, value=tot_credito).font = font_total
    ws6.cell(row=last_r_cr, column=5).number_format = '"C$" #,##0.00'
    ws6.cell(row=last_r_cr, column=5).alignment = align_right

    ws6.cell(row=last_r_cr, column=9, value=tot_ganancia_cr).font = font_total
    ws6.cell(row=last_r_cr, column=9).number_format = '"C$" #,##0.00'
    ws6.cell(row=last_r_cr, column=9).alignment = align_right

    for c_i in range(1, 12):
        cell_t = ws6.cell(row=last_r_cr, column=c_i)
        cell_t.fill = fill_total
        cell_t.border = border_total

    autofit(ws6)

    # =========================================================================
    # HOJA 7: AUDITORÍA DE RESULTADOS ESPERADOS
    # =========================================================================
    ws7 = wb.create_sheet(title='7. AUDITORÍA FINAL')
    setup_banner(ws7, 'AUDITORÍA Y VERIFICACIÓN DE REPORTES DEL SISTEMA', 'Compara estas cifras exactas contra los totales mostrados en el Salpicadero, Reportes y Catálogo', 6)

    # Sub-tabla 1: Métricas Financieras Globales
    ws7.cell(row=4, column=1, value='INDICADOR / REPORTE FINANCIERO').font = font_th
    ws7.cell(row=4, column=1).fill = fill_th
    ws7.merge_cells('A4:C4')

    ws7.cell(row=4, column=4, value='VALOR ESPERADO (C$)').font = font_th
    ws7.cell(row=4, column=4).fill = fill_th
    ws7.cell(row=4, column=4).alignment = align_right

    ws7.cell(row=4, column=5, value='DÓNDE VERIFICAR EN EL SISTEMA').font = font_th
    ws7.cell(row=4, column=5).fill = fill_th
    ws7.merge_cells('E4:F4')

    metricas_auditoria = [
        ('1. Total Facturado en Ventas Contado', 4430.00, 'Reporte de Ventas > Filtro Contado'),
        ('2. Total Facturado en Ventas Crédito', 3940.00, 'Reporte de Ventas > Filtro Crédito'),
        ('3. Total General de Ventas Facturadas (Contado + Crédito)', 8370.00, 'Salpicadero > Tarjeta Ventas Totales'),
        ('4. Total Efectivo Recaudado en Caja (Contado + Abono Cuota 1)', 5185.00, 'Salpicadero > Total Cobrado / Ingresos'),
        ('5. Cartera Pendiente por Cobrar (Saldo Cuota 2 Gómez + 4 Cuotas Mercado)', 3185.00, 'Salpicadero > Cuentas por Cobrar Pendientes'),
        ('6. Ganancia Bruta Total Generada en las Ventas', 2250.00, 'Salpicadero / Reporte de Utilidad Bruta')
    ]

    for idx, (lbl, val, mod) in enumerate(metricas_auditoria, 5):
        fill_r = fill_zebra if idx % 2 == 0 else PatternFill(fill_type=None)
        ws7.row_dimensions[idx].height = 22

        ws7.merge_cells(start_row=idx, start_column=1, end_row=idx, end_column=3)
        ws7.cell(row=idx, column=1, value=lbl).font = font_td_bold
        ws7.cell(row=idx, column=1).fill = fill_r
        for ci in range(1, 4):
            ws7.cell(row=idx, column=ci).border = border_thin

        c_v = ws7.cell(row=idx, column=4, value=val)
        c_v.font = font_total
        c_v.fill = fill_r
        c_v.alignment = align_right
        c_v.number_format = '"C$" #,##0.00'
        c_v.border = border_thin

        ws7.merge_cells(start_row=idx, start_column=5, end_row=idx, end_column=6)
        c_m = ws7.cell(row=idx, column=5, value=mod)
        c_m.font = font_td
        c_m.fill = fill_r
        for ci in range(5, 7):
            ws7.cell(row=idx, column=ci).border = border_thin

    # Sub-tabla 2: Verificación de Existencias de Inventario y Semáforo
    r_inv_start = len(metricas_auditoria) + 7
    ws7.row_dimensions[r_inv_start].height = 24
    ws7.cell(row=r_inv_start, column=1, value='PRODUCTO (SKU)').font = font_th
    ws7.cell(row=r_inv_start, column=1).fill = fill_th
    ws7.cell(row=r_inv_start, column=1).alignment = align_center

    ws7.cell(row=r_inv_start, column=2, value='COMPRA INICIAL').font = font_th
    ws7.cell(row=r_inv_start, column=2).fill = fill_th
    ws7.cell(row=r_inv_start, column=2).alignment = align_center

    ws7.cell(row=r_inv_start, column=3, value='UNID. VENDIDAS').font = font_th
    ws7.cell(row=r_inv_start, column=3).fill = fill_th
    ws7.cell(row=r_inv_start, column=3).alignment = align_center

    ws7.cell(row=r_inv_start, column=4, value='STOCK ACTUAL FINAL').font = font_th
    ws7.cell(row=r_inv_start, column=4).fill = fill_th
    ws7.cell(row=r_inv_start, column=4).alignment = align_center

    ws7.cell(row=r_inv_start, column=5, value='STOCK MÍNIMO').font = font_th
    ws7.cell(row=r_inv_start, column=5).fill = fill_th
    ws7.cell(row=r_inv_start, column=5).alignment = align_center

    ws7.cell(row=r_inv_start, column=6, value='SEMÁFORO ESPERADO EN CATÁLOGO').font = font_th
    ws7.cell(row=r_inv_start, column=6).fill = fill_th
    ws7.cell(row=r_inv_start, column=6).alignment = align_center

    inv_auditoria = [
        ('PROD-001 (Nike Revolution 6)', 10, 3, 7, 3, 'SALUDABLE (Verde)', fill_green),
        ('PROD-002 (Polo Tommy)', 15, 2, 13, 4, 'SALUDABLE (Verde)', fill_green),
        ('PROD-003 (Perfume 212 VIP)', 6, 1, 5, 2, 'SALUDABLE (Verde)', fill_green),
        ('PROD-004 (Audífonos Lenovo)', 20, 4, 16, 5, 'SALUDABLE (Verde)', fill_green),
        ('PROD-005 (Reloj Casio)', 8, 1, 7, 3, 'SALUDABLE (Verde)', fill_green),
        ('PROD-006 (Jeans Levi\'s)', 12, 1, 11, 4, 'SALUDABLE (Verde)', fill_green),
    ]

    for idx, (p, comp, vend, stk, smin, sem, fill_sem) in enumerate(inv_auditoria, r_inv_start + 1):
        ws7.row_dimensions[idx].height = 20
        fill_r = fill_zebra if idx % 2 == 0 else PatternFill(fill_type=None)

        ws7.cell(row=idx, column=1, value=p).font = font_td_bold
        ws7.cell(row=idx, column=1).fill = fill_r
        ws7.cell(row=idx, column=1).border = border_thin

        ws7.cell(row=idx, column=2, value=comp).font = font_td
        ws7.cell(row=idx, column=2).fill = fill_r
        ws7.cell(row=idx, column=2).alignment = align_center
        ws7.cell(row=idx, column=2).border = border_thin

        ws7.cell(row=idx, column=3, value=vend).font = font_td
        ws7.cell(row=idx, column=3).fill = fill_r
        ws7.cell(row=idx, column=3).alignment = align_center
        ws7.cell(row=idx, column=3).border = border_thin

        ws7.cell(row=idx, column=4, value=stk).font = font_td_bold
        ws7.cell(row=idx, column=4).fill = fill_r
        ws7.cell(row=idx, column=4).alignment = align_center
        ws7.cell(row=idx, column=4).border = border_thin

        ws7.cell(row=idx, column=5, value=smin).font = font_td
        ws7.cell(row=idx, column=5).fill = fill_r
        ws7.cell(row=idx, column=5).alignment = align_center
        ws7.cell(row=idx, column=5).border = border_thin

        c_sem = ws7.cell(row=idx, column=6, value=sem)
        c_sem.font = font_td_bold
        c_sem.fill = fill_sem
        c_sem.alignment = align_center
        c_sem.border = border_thin

    autofit(ws7)

    output_path = 'GUIA_DE_PRUEBAS_SISTEMA_COBRO.xlsx'
    wb.save(output_path)
    print(f'Libro Excel generado exitosamente: {output_path}')

if __name__ == '__main__':
    build_test_workbook()
