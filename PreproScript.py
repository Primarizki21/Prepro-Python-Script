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
import pkg_resources
from symspellpy import SymSpell, Verbosity

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
        if apakah_kolom_country(kolom):
            kolom_id.append(kolom)
    return kolom_id

# Kategorik
country_mapping = {
    'america': 'USA',
    'bharat': 'IND',
    'uk': 'United Kingdom'
}
voting_mapping = {
    'no': 'No',
    'yes': 'Yes',
    'n': 'No', 
    'y': 'Yes',
    ' ': 'Unknown',
    '': 'Unknown',
}
marital_mapping = {
    's': 'Single',
    'belummenikah': 'Single', 
    'janda': 'Widowed',
    'duda': 'Widowed',
    'cerai': 'Divorced'
}
education_mapping = {
    'high school': 'High School',
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
medics_mapping = {
    "ortho": 'Orthopedics',
    "neuro": 'Neurology',
    "gastro": 'Gastroenterology',
    "cardio": 'Cardiology',
    "onco": 'Oncology',
    "endo": 'Endocrinology',
    "uro": 'Urology',
    "nephro": 'Nephrology',
    "pulmo": 'Pulmonology',
    "derma": 'Dermatology',
    "pedi": 'Pediatrics',
    "psych": 'Psychiatry',
    "radi": 'Radiology',
    "patho": 'Pathology',
    "anest": 'Anesthesiology',
    "gen": 'General',
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
sym_spell = SymSpell(max_dictionary_edit_distance=4, prefix_length=12)
dictionary_path = pkg_resources.resource_filename(
    "symspellpy", "frequency_dictionary_en_82_765.txt")
sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)

cache_kata = {}
@lru_cache(maxsize=None)
def combine_format_typo(typo):
    if typo in cache_kata:
        return cache_kata[typo]
    typo_lower = str(typo).lower()
    result = spell.correction(typo_lower)
    if not result or result == typo_lower:
        suggestions = sym_spell.lookup(typo_lower, Verbosity.CLOSEST, max_edit_distance=4)
        if suggestions:
            result = suggestions[0].term
        else:
            result = typo_lower
    result = result.title()
    cache_kata[typo] = result
    return result

def replace_values_with_dict(df, dictionary):
    kolom_darah = [col for col in df.columns if apakah_bloodtype(df[col])]
    kolom_negara = [col for col in df.columns if apakah_kolom_country(col)]
    
    for kolom in df.select_dtypes(include=['object']).columns:
        df[kolom] = df[kolom].fillna('Unknown').apply(lambda x: str(x).lower())
        if kolom not in [*kolom_negara, *kolom_darah]:
            if ~df[kolom].isin(dictionary).any():
                print(f"Processing {kolom} as typo")
                df[kolom] = df[kolom].apply(combine_format_typo)
            else:      
                print(f"Processing {kolom} with dictionary")
                df[kolom] = df[kolom].apply(lambda x: dictionary.get(x, x))
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
    blood_mapping,
    medics_mapping
    )

# Format Nama Negara
@lru_cache(maxsize=None)
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

def format_kolom_int(df):
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
        
        # 3. Format Tanggal
        kolom_date = identifikasi_kolom_date(df)
        for kolom in kolom_date:
            if df[kolom].dtype != 'datetime64[ns]':
                df[kolom] = df[kolom].apply(safe_parse)
                if df[kolom].isna().sum() > 0:
                    print(f'Terdapat value NaT setelah parsing')
                    time.sleep(0.2)
                    print('Menghapus baris dengan value NaT')
                    df.dropna(subset=[kolom], inplace=True)
            else:
                print(f"Kolom {kolom} sudah dalam format datetime64[ns]")

        # Kolom yang akan dihapus
        kolom_hapus = format_kolom_hapus(df)
        print(f'Ini adalah kolom yang akan dihapus: {kolom_hapus}')
        df = df.drop(columns = kolom_hapus)

        # Kolom Int
        kolom_int = format_kolom_int(df)
        print(f'Ini adalah kolom angka: {kolom_int}')
        for kolom in kolom_int:
            df[kolom] = df[kolom].apply(lambda x: abs(x))

        # 4. Format Nama Negara
        kolom_negara = identifikasi_kolom_country(df)
        for kolom in kolom_negara:
            df[kolom] = df[kolom].apply(format_country)
        
        # 5. Format Kategorik
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