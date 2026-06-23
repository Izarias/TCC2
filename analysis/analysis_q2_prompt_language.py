import pandas as pd
from db import get_engine

def prompt_language_analysis():
    engine = get_engine()

    df = pd.read_sql("SELECT * FROM clean_dataset", con=engine)
    
    if df.empty:
        print("A tabela clean_dataset está vazia.")
        return

    # TAXA COMPARATIVA DE VULNERABILIDADES POR IDIOMA (TCVI)
    print("\n=======================================================")
    print("1. ANÁLISE COMPARATIVA DE VOLUME (TCVI)")
    print("=======================================================")

    df['prompt_language'] = df['prompt_language'].str.capitalize()
    
    falhas_por_idioma = df['prompt_language'].value_counts()
    v_pt = falhas_por_idioma.get('Portuguese', 0)
    v_en = falhas_por_idioma.get('English', 0)
    
    n_pt = 60  
    n_en = 60  
    
    media_pt = v_pt / n_pt
    media_en = v_en / n_en
    
    # TCVI estrita (Razão direta do número de vulnerabilidades encontradas)
    tcvi_absoluta = v_pt / v_en if v_en > 0 else 0
    
    print(f"Total absoluto de falhas -> PT: {v_pt} | EN: {v_en}")
    print(f"Média de falhas por snippet -> PT: {media_pt:.2f} | EN: {media_en:.2f}")
    print(f"--> TCVI (Razão Absoluta PT/EN): {tcvi_absoluta:.2f}")
    print(f"Nota explicativa: Proporcionalmente, prompts em PT geram {tcvi_absoluta:.2f}x a quantidade de falhas de EN.")

    # TAXA DE VULNERABILIDADES CRÍTICAS POR IDIOMA (TVCI)
    print("\n=======================================================")
    print("2. ANÁLISE DE SEVERIDADE CRÍTICA (TVCI)")
    print("=======================================================")
    
    labels_criticos = ['ALTO']  
    
    df['is_critical'] = df['severity'].str.upper().isin(labels_criticos)
    
    # Agrupa por idioma e calcula as métricas
    analise_critica = df.groupby('prompt_language').agg(
        Total_Vulnerabilidades=('is_critical', 'count'),
        Qtd_Criticas=('is_critical', 'sum')
    )
    
    analise_critica['TVCI (%)'] = (analise_critica['Qtd_Criticas'] / analise_critica['Total_Vulnerabilidades']) * 100
    analise_critica['TVCI (%)'] = analise_critica['TVCI (%)'].round(2)
    
    print(analise_critica.to_string())

if __name__ == "__main__":
    prompt_language_analysis()