import pandas as pd


DEFAULT_COLUMNS = [
    'N Comprob', 'Fecha', 'Tipo', 'Cuenta', 'C.Costo', 'Análisis', 'RUT', 'Producto',
    'Glosa', 'Debe', 'Haber', 'Incluir Libros', 'Fecha Emis.', 'Fecha Vcto.',
    'Flujo Efect.', 'Nominal Debe', 'Nominal Haber'
]


def _cargar_template(template_path):
    try:
        import xlrd
    except ImportError:
        return DEFAULT_COLUMNS, {}

    try:
        workbook = xlrd.open_workbook(template_path, formatting_info=False)
        sheet = workbook.sheet_by_index(0)
        if sheet.nrows == 0:
            return DEFAULT_COLUMNS, {}

        columns = [str(c).strip() for c in sheet.row_values(0)]
        columns = columns if any(columns) else DEFAULT_COLUMNS

        defaults = {}
        if sheet.nrows > 1:
            row1 = sheet.row_values(1)
            defaults = {columns[i]: row1[i] if i < len(row1) else '' for i in range(len(columns))}

        return columns, defaults
    except Exception:
        return DEFAULT_COLUMNS, {}


def _format_dataframe(transactions, columns, defaults):
    if not transactions:
        return pd.DataFrame(columns=columns)

    records = []
    for item in transactions:
        row = dict(defaults)
        row.update(item)
        records.append(row)

    df = pd.DataFrame(records)
    for column in columns:
        if column not in df.columns:
            df[column] = ''

    return df[columns]


def generate_excel(transactions, file_name, template_path=None):
    """Generate an Excel file from a list of transactions."""
    columns, defaults = DEFAULT_COLUMNS, {}
    if template_path:
        columns, defaults = _cargar_template(template_path)

    df = _format_dataframe(transactions, columns, defaults)
    
    df.to_excel(file_name, index=False)
    
    print(f'Excel file {file_name} generated successfully.')


# Example usage:
# transactions = [{'date': '2021-01-01', 'amount': 100, 'description': 'Payment'}, {'date': '2021-01-02', 'amount': -50, 'description': 'Refund'}]
# generate_excel(transactions, 'transactions.xlsx')