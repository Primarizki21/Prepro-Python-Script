import typer
import pandas as pandas
import re
from dateutil import parser

app = typer.Typer()

# Mencari Kolom ID
def apakah_kolom_id(kolom):
    """
    Apakah Kolom ID?
    Pola kata dari kolom yang ingin dihapus
    Mencari kolom dengan pola kata "ID"
    """
    pattern = r'(id)[_A-Z]?' 
    return re.search(pattern, kolom, re.IGNORECASE)

def identifikasi_kolom_id(df, threshold = 0.7):
    """
    Identifikasi Kolom ID
    Menggunakan threshold 0.7 sebagai batas nilai Kardinalitas
    """
    kolom_id = []
    for kolom in df.columns:
        ratio = df[kolom].nunique() / len(df)
        if (ratio >= threshold) and apakah_kolom_id(kolom):
            kolom_id.append(kolom)
    return kolom_id

# Mencari Kolom Nama
def apakah_kolom_nama(kolom):
    """
    Apakah Kolom Nama?
    Pola kata dari kolom yang ingin dihapus
    Mencari kolom dengan pola kata "name" dan "nama"
    """
    pattern = r'(name|nama)[_A-Z]?'
    return re.search(pattern, kolom, re.IGNORECASE)

def identifikasi_kolom_nama(df, threshold = 0.7):
    """
    Identifikasi Kolom Nama
    Menggunakan threshold 0.7 sebagai batas nilai Kardinalitas
    """
    kolom_id = []
    for kolom in df.columns:
        ratio = df[kolom].nunique() / len(df)
        if (ratio >= threshold) and apakah_kolom_nama(kolom):
            kolom_id.append(kolom)
    return kolom_id

def format_nama(nama):
    """
    Format Nama Kapital
    """
    return nama.title()

@app.command()
def clean(input_file: str):
    try:
        df = pd.read_csv(input_file)

        # 1. Menghapus Kolom ID
        kolom_id = identifikasi_kolom_id(df)
        df = df.drop(columns = kolom_id)

        # 2. Menghilangkan Duplikasi
        df = df.drop_duplicates()

        # 3. Format Nama
        kolom_nama = identifikasi_kolom_nama(df)
        for kolom in kolom_nama:
            df[kolom] = df[kolom].apply(format_nama)
        
        # 4. Format Tanggal
        kolom_date = identifikasi_kolom_date(df)
        for kolom in kolom_date:
            df[kolom] = df[kolom].apply(parser.parse)

    except Exception as e:
        typer.secho(f"Error: {str(e)}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()