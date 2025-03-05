import typer
import pandas as pd
import re
import numpy as np
import pycountry
from dateutil import parser
from functools import lru_cache
from datetime import datetime
import time
import os
from spellchecker import SpellChecker

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
    return verif1

def identifikasi_kolom_date(df):
    """
    Identifikasi Kolom Date
    """
    kolom_id = []
    for kolom in df.columns:
        if apakah_kolom_date(kolom):
            kolom_id.append(kolom)
    return kolom_id

# Format Tanggal
def safe_parse(date_str):
    date_str = str(date_str).strip()
    try:
        parsed_date = parser.parse(date_str)
        return pd.to_datetime(parsed_date, errors='coerce')
    except (ValueError, TypeError): 
        return pd.NaT 

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

def format_nomor(nomor, simbol, pemisah="-"):
    """
    Format Nomor untuk menghilangkan simbol yang tidak perlu
    """
    clean_text = re.sub(f'[{simbol}]', '', nomor)
    chunk = []
    for i in range(0, len(clean_text), 3):
        chunk.append(clean_text[i:i+3])
    hasil = pemisah.join(chunk)
    return hasil
    
# Kategorik
country_mapping = {
    'america': 'USA',
    'bharat': 'IND',
    'uk': 'United Kingdom'
}
voting_mapping = {
    'n': 'No', 
    'y': 'Yes',
    ' ': 'Unknown',
    '': 'Unknown',
    np.nan: 'Unknown',
    pd.NA  : 'Unknown'
}
marital_mapping = {
    's': 'Single',
    'belummenikah': 'Single', 
    'janda': 'Widowed',
    'duda': 'Widowed',
    'cerai': 'Divorced'
}
education_mapping = {
    'sma': 'High School',
    'hs' : 'High School',
    'phd' : 'Doctorate',
    's1': 'Bachelors',
    's2': 'Master',
    's3': 'Doctorate'
}
gender_mapping = {
    'm': 'Male',
    'f': 'Female',
    'u': 'Unknown',
}
blood_mapping = {
    'positive': '+',
    'negative': '-',
    'positif': '+',
    'negatif': '-',
}

def merge_dictionaries(*dicts):
    merged_dict = {}
    for dictionary in dicts:
        merged_dict.update(dictionary)
    return merged_dict

def apakah_bloodtype(kolom):
    kolom = kolom.astype(str)
    akhiran = kolom.str.endswith('+') | kolom.str.endswith('-')
    ada_kata = kolom.str.contains('positive|negative|positif|negatif', case=False, na=False)
    return akhiran.any() | ada_kata.any()

def format_bloodtype(blood, dictionary):
    output = blood
    bloods = blood.lower()
    bagian = bloods.split()
    if len(bagian) == 2 and (bagian[0] in ['a', 'b', 'ab', 'o'] and bagian[1] in dictionary):
        darah, tipe = bagian
        tipe = dictionary.get(tipe.lower(), tipe)
        return f"{darah.upper()}{tipe}"
    elif len(bagian) == 1 and bagian[0][-1] in ['+', '-']:
        return bagian[0].upper()
    else:
        return output

# Format Typo
spell = SpellChecker()
@lru_cache(maxsize=None)
def format_typo(typo):
    hasil = str(spell.correction(typo))
    if hasil.lower() == 'none':
        return typo
    return hasil.title()

# def replace_values_with_dict(df, dictionary):
#     kolom_darah = [col for col in df.columns if apakah_bloodtype(df[col])]
#     df = df.apply(lambda x: x.str.strip().str.lower() if x.dtype == 'object' else x)
    
#     for kolom in df.select_dtypes(include=['object']).columns:
#         df[kolom] = df[kolom].replace(dictionary)
#         df[kolom] = df[kolom].apply(format_typo)
#         if kolom in kolom_darah:
#             df[kolom] = df[kolom].apply(lambda x: format_bloodtype(x, blood_mapping))
#         else:
#             df[kolom] = df[kolom].str.title()
#     return df

def replace_values_with_dict(df, dictionary):
    kolom_darah = [col for col in df.columns if apakah_bloodtype(df[col])]
    
    for kolom in df.select_dtypes(include=['object']).columns:
        print(kolom)
        # First replace values using dictionary
        df[kolom] = df[kolom].replace(dictionary)
        
        # Only apply format_typo if value not in dictionary
        df[kolom] = df[kolom].apply(lambda x: x if str(x).lower() in [str(v).lower() for v in dictionary.values()] else format_typo(x))
        
        if kolom in kolom_darah:
            df[kolom] = df[kolom].apply(lambda x: format_bloodtype(x, blood_mapping))
        else:
            df[kolom] = df[kolom].str.title()
    return df

merged_dict = merge_dictionaries(
    country_mapping, 
    voting_mapping, 
    marital_mapping,
    education_mapping,
    gender_mapping,
    blood_mapping
    )

# Format Nama Negara
def format_country(country):
    """
    Format country menjadi nama negara, bukan code atau nomor
    """
    country = country.lower()
    if country in country_mapping:
        country = country_mapping[country]
    hasil_cari = pycountry.countries.search_fuzzy(country)[0]
    return hasil_cari.name

# Kolom Hapus
def format_kolom_hapus(df, threshold = 0.6):
    kolom_id = []
    for kolom in df.select_dtypes(include=['object']).columns:
        ratio = df[kolom].nunique() / len(df)
        jumlah = df[kolom].nunique()
        if ratio >= threshold or jumlah > 100:
            kolom_id.append(kolom)
    return kolom_id

def format_kolom_hapus_int(df):
    kolom_id = []
    for kolom in df.select_dtypes(include=['int', 'float']).columns:
        kolom_id.append(kolom)
    return kolom_id

# Main Function
@app.command()
def clean(input_file: str):
    try:
        df = pd.read_csv(input_file)

        # 1. Menghapus Kolom ID
        kolom_id = identifikasi_kolom_id(df)
        df = df.drop(columns = kolom_id)

        # 2. Menghilangkan Duplikasi
        df = df.drop_duplicates()
        
        # 4. Format Tanggal
        kolom_date = identifikasi_kolom_date(df)
        for kolom in kolom_date:
            if df[kolom].dtype != 'datetime64[ns]':
                df[kolom] = df[kolom].apply(safe_parse)
                if df[kolom].isna().sum() > 0:
                    print(f'Terdapat value NaT setelah parsing')
                    time.sleep(0.2)
                    user_response = input("Apakah anda mau menghapus baris dengan value NaT? (Y/N)").strip().upper()
                    if user_response == "Y":
                        df.dropna(subset=[kolom], inplace=True)
                        print("Baris dengan nilai NaT berhasil terhapus!")
                    elif user_response == "N":
                        print("Baris dengan nilai NaT dipertahankan")
                    else:
                        print("Input Salah, baris dengan nilai NaT dipertahankan")
            else:
                print(f"Kolom {kolom} sudah dalam format datetime64[ns]")

        # kolom hapus
        kolom_hapus = format_kolom_hapus(df)
        print(kolom_hapus)
        df = df.drop(columns = kolom_hapus)

        # int
        kolom_hapus_int = format_kolom_hapus_int(df)
        for kolom in kolom_hapus_int:
            df[kolom] = df[kolom].apply(lambda x: abs(x))

        # 5. Format Nama Negara
        kolom_negara = identifikasi_kolom_country(df)
        for kolom in kolom_negara:
            df[kolom] = df[kolom].apply(format_country)
        
        # 8. Format Kategorik
        df = replace_values_with_dict(df, merged_dict)

        # Output File
        nama_file = os.path.basename(input_file)
        new_filename = f"clean-{nama_file}"
        df.to_csv(new_filename, index=False)

        print(f"Saved as {new_filename}")
    except Exception as e:
        typer.secho(f"Error: {str(e)}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()