import typer
import pandas as pandas

app = typer.Typer()

def apakah_kolom_id(kolom):
    """
    Apakah Kolom ID?
    Pola kata dari kolom yang ingin dihapus
    Mencari kolom dengan pola kata "ID", "customer", dan "tax"
    """
    pattern = r'(id|customer|tax)[_A-Z]?' 
    return re.search(pattern, kolom, re.IGNORECASE)

def identifikasi_kolom_id(df, threshold = 0.85):
    """
    Identifikasi Kolom ID
    Menggunakan threshold 0.85 sebagai batas nilai Kardinalitas
    """
    kolom_id = []
    for kolom in df.columns:
        ratio = df[kolom].nunique() / len(df)
        if (ratio >= threshold) and apakah_kolom_id(kolom):
            kolom_id.append(kolom)
    return kolom_id
    
@app.command()
def clean():
    pass


if __name__ == "__main__":
    app()