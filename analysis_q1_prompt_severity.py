import pandas as pd
from db import get_engine

def prompt_severity_analysis():
    engine = get_engine()

    df = pd.read_sql("SELECT * FROM clean_dataset", con=engine)
    
    if df.empty:
        print("A tabela clean_dataset está vazia.")
        return

    # CALCULAR A TVP (Ocorrência)
    print("\n=======================================================")
    print("--- ANÁLISE DE OCORRÊNCIA (TVP) ---")
    print("=======================================================")
    # Contabiliza o total de vulnerabilidades (Vi) encontradas por tipo de prompt
    vulnerabilidades_por_prompt = df.groupby('prompt_type').size()
    
    N_i = {
        "zero-shot": 40, 
        "few-shot": 40,
        "detalhado": 40,
    }
    
    dados_tvp = []
    for p_type, V_i in vulnerabilidades_por_prompt.items():
        n_total = N_i.get(p_type, 1)
        tvp = V_i / n_total
        dados_tvp.append({
            "Tipo de Prompt": p_type,
            "Total Vulnerabilidades (Vi)": V_i,
            "Total Amostras (Ni)": n_total,
            "TVP (Média Falhas/Snippet)": round(tvp, 2)
        })
        
    df_tvp = pd.DataFrame(dados_tvp).sort_values(by="TVP (Média Falhas/Snippet)", ascending=False)
    print(df_tvp.to_string(index=False))

    # ANÁLISE DE SEVERIDADE CONSOLIDADA
    print("\n=======================================================")
    print("--- ANÁLISE DE SEVERIDADE POR TIPO DE PROMPT ---")
    print("=======================================================")
    
    df_original = pd.crosstab(df['prompt_type'], df['severity'])

    for col in ['Alto', 'Médio', 'Baixo']:
        if col not in df_original.columns:
            df_original[col] = 0

    df_severidade = pd.DataFrame(index=df_original.index)
    df_severidade['Alto'] = df_original['Alto']
    df_severidade['Médio'] = df_original['Médio']
    df_severidade['Baixo'] = df_original['Baixo']

    df_severidade['Total Ocorrências'] = df_original.sum(axis=1)
    
    # Cálculo da Severidade Média Ponderada
    pontuaca_total = (df_severidade['Alto'] * 3) + \
                     (df_severidade['Médio'] * 2) + \
                     (df_severidade['Baixo'] * 1)
                     
    df_severidade['Severidade Média'] = (pontuaca_total / df_severidade['Total Ocorrências']).round(2)
    
    # 4. Gera a tabela percentual apenas das colunas de severidade (para não incluir o Total e a Média no % )
    colunas_sev = ['Alto', 'Médio', 'Baixo']
    df_sev_pct = df_severidade[colunas_sev].div(df_severidade['Total Ocorrências'], axis=0) * 100
    df_sev_pct = df_sev_pct.round(1)
    
    # Exibição dos resultados
    # Pesos utilizados: Alto=3, Médio=2, Baixo=1
    # Severidade média mais perto de 3 indica um perfil mais crítico, enquanto mais perto de 1 indica um perfil mais leve.
    print("\nTabela Consolidada de Severidade:")
    print(df_severidade)
    
    print("\nDistribuição percentual (%) da severidade dentro de cada prompt:")
    print(df_sev_pct)

if __name__ == "__main__":
    prompt_severity_analysis()