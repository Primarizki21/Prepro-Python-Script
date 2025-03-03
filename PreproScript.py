import typer
import pandas as pandas
import re
import numpy as np
import pycountry
from dateutil import parser
from functools import lru_cache

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

# Mencari Kolom Tanggal
def apakah_kolom_date(kolom):
    """
    Apakah Kolom Tanggal?
    Pola kata dari kolom yang ingin dihapus
    Mencari kolom dengan pola kata "date" dll
    """
    pattern1 = r'(date|tanggal|tgl|dt)\b|_(date|tanggal|tgl|dt)[_A-Z]?'
    verif1 = re.search(pattern1, kolom, re.IGNORECASE)
    # verif2 = re.search(pattern2, kolom, re.IGNORECASE)
    return verif1
    # return re.search(pattern, kolom, re.IGNORECASE)

def identifikasi_kolom_date(df):
    """
    Identifikasi Kolom Date
    """
    kolom_id = []
    for kolom in df.columns:
        if apakah_kolom_date(kolom):
            kolom_id.append(kolom)
    return kolom_id

# Mencari Kolom Country
def apakah_kolom_country(kolom):
    pattern = r'(origin|citizenship|country|nationality)\b|_(origin|citizenship|country|nationality)[_A-Z]?'
    return re.search(pattern, kolom, re.IGNORECASE)

def identifikasi_kolom_country(df):
    """
    Identifikasi Kolom Country
    """
    kolom_id = []
    for kolom in df.columns:
        ratio = df[kolom].nunique() / len(df)
        if apakah_kolom_country(kolom):
            kolom_id.append(kolom)
    return kolom_id

# Mencari Kolom Nomor Telepon
def apakah_kolom_telp(kolom):
    pattern = r'\b(phone|telp|telephone)|(phone|telp|telephone)\b|_(phone|telp|telephone)[_A-Z]?'
    return re.search(pattern, kolom, re.IGNORECASE)

def identifikasi_kolom_telp(df, threshold = 0.7):
    """
    Identifikasi Kolom Nomor Telepon
    """
    kolom_id = []
    for kolom in df.columns:
        ratio = df[kolom].nunique() / len(df)
        if (ratio >= threshold) and apakah_kolom_telp(kolom):
            kolom_id.append(kolom)
    return kolom_id

# Format Nama Negara
@lru_cache(maxsize=None)
def format_country(country):
    """
    Format country menjadi nama negara, bukan code atau nomor
    """
    country = country.lower()
    if country in special_mapping:
        country = special_mapping[country]
    hasil_cari = pycountry.countries.search_fuzzy(country)[0]
    return hasil_cari.name

# Format Nomor Telepon
angka = [str(i) for i in range(0,10)]
def ekstrak_simbol(baris):
    """
    Ekstrak Simbol agar bisa digunakan disemua situasi
    """
    simbol = set()
    for nomor in baris:
        for x in nomor:
            if x not in angka and x not in simbol:
                simbol.add(x)
    return re.escape(''.join(simbol))

def format_nomor(nomor, simbol):
    """
    Format Nomor untuk menghilangkan simbol yang tidak perlu
    """
    clean_text = re.sub(f'[{simbol}]', '', nomor)
    return clean_text
    
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

        # 5. Format Nama Negara
        kolom_negara = identifikasi_kolom_country(df)
        for kolom in kolom_negara:
            df[kolom] = df[kolom].apply(format_country)
        
        # 6. Format Nomor Telepon
        kolom_telp = identifikasi_kolom_telp(df)
        for kolom in kolom_telp:
            simbol = ekstrak_simbol(df[kolom])
            df[kolom] = df[kolom].apply(lambda x: format_nomor(x, simbol))

    except Exception as e:
        typer.secho(f"Error: {str(e)}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()