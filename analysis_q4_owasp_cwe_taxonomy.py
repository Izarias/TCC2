import pandas as pd
from db import get_engine

def owasp_cwe_taxonomy_analysis():
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM clean_dataset", con=engine)
    
    if df.empty:
        print("A tabela clean_dataset está vazia.")
        return

    print("\n=======================================================")
    # =========================================================================
    # PREPARAÇÃO E TRATAMENTO DA TAXONOMIA OWASP / CWE
    # =========================================================================
    # 1. Tratamento e Explosão do OWASP
    df['owasp_list'] = df['owasp_detected'].fillna('N/A').astype(str).str.split(',\s*')
    df_owasp_exploded = df.explode('owasp_list').reset_index(drop=True)
    df_owasp_exploded['owasp_list'] = df_owasp_exploded['owasp_list'].str.strip()
    
    # Filtra dados inválidos para OWASP
    df_owasp_validos = df_owasp_exploded[~df_owasp_exploded['owasp_list'].isin(['N/A', '', 'None', 'Unknown'])]

    # 2. Tratamento e Explosão do CWE (Necessário para responder a Q4 por completo)
    df['cwe_list'] = df['cwe_detected'].fillna('N/A').astype(str).str.split(',\s*')
    df_cwe_exploded = df.explode('cwe_list').reset_index(drop=True)
    df_cwe_exploded['cwe_list'] = df_cwe_exploded['cwe_list'].str.strip()
    
    # Filtra dados inválidos para CWE
    df_cwe_validas = df_cwe_exploded[~df_cwe_exploded['cwe_list'].isin(['N/A', '', 'None', 'Unknown'])]

    print("\n=======================================================")
    print("1. TOP-10 CATEGORIAS OWASP MAIS RECORRENTES (COM ANO)")
    print("=======================================================")
    
    top_10_owasp = df_owasp_validos.groupby('owasp_list').size().reset_index(name='Frequência')
    top_10_owasp['Percentual (%)'] = (top_10_owasp['Frequência'] / top_10_owasp['Frequência'].sum()) * 100
    top_10_owasp = top_10_owasp.sort_values(by='Frequência', ascending=False).head(10)
    top_10_owasp['Percentual (%)'] = top_10_owasp['Percentual (%)'].round(2)
    
    print(top_10_owasp.to_string(index=False, header=['Categoria OWASP', 'Frequência', 'Percentual (%)']))


    print("\n=======================================================")
    print("2. TOP-10 CATEGORIAS CWE MAIS RECORRENTES")
    print("=======================================================")
    
    top_10_cwe = df_cwe_validas.groupby('cwe_list').size().reset_index(name='Frequência')
    top_10_cwe['Percentual (%)'] = (top_10_cwe['Frequência'] / top_10_cwe['Frequência'].sum()) * 100
    top_10_cwe = top_10_cwe.sort_values(by='Frequência', ascending=False).head(10)
    top_10_cwe['Percentual (%)'] = top_10_cwe['Percentual (%)'].round(2)
    
    print(top_10_cwe.to_string(index=False, header=['Categoria CWE', 'Frequência', 'Percentual (%)']))


    print("\n=======================================================")
    print("3. ÍNDICE DE COBERTURA OWASP TOP 10 (ICO)")
    print("=======================================================")
    
    # Função robusta para extrair a macro-categoria (ex: de 'A03:2021' extrai 'A03')
    def extrair_categoria_base(owasp_str):
        if ':' in owasp_str:
            owasp_str = owasp_str.split(':')[0]
        if '-' in owasp_str:
            owasp_str = owasp_str.split('-')[0]
        return owasp_str.strip().upper()

    # Obtém as macro-categorias únicas (A01, A02, etc.) ignorando a duplicação por ano
    categorias_base = df_owasp_validos['owasp_list'].apply(extrair_categoria_base).unique()
    categorias_owasp_reais = sorted([c for c in categorias_base if c.startswith('A') and len(c) <= 4])
    
    qtd_categorias = len(categorias_owasp_reais)
    ico = (qtd_categorias / 10) * 100
    
    print(f"Macro-categorias do OWASP Top 10 identificadas: {categorias_owasp_reais}")
    print(f"Total de macro-categorias atingidas: {qtd_categorias} de 10")
    print(f"--> Índice de Cobertura OWASP (ICO): {ico:.2f}%")

if __name__ == "__main__":
    owasp_cwe_taxonomy_analysis()