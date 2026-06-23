import pandas as pd
from db import get_engine
import matplotlib.pyplot as plt

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
                     
    df_severidade['Severidade Média'] = (pontuaca_total / 40).round(2)
    
    colunas_sev = ['Alto', 'Médio', 'Baixo']
    df_sev_pct = df_severidade[colunas_sev].div(df_severidade['Total Ocorrências'], axis=0) * 100
    df_sev_pct = df_sev_pct.round(1)
    
    print("\nTabela Consolidada de Severidade:")
    print(df_severidade)
    
    print("\nDistribuição percentual (%) da severidade dentro de cada prompt:")
    print(df_sev_pct)

    # ------ GRÁFICOS ------
    
    df_tvp = df_tvp.sort_values(by='Total Vulnerabilidades (Vi)', ascending=True)

    bars = plt.bar(
        df_tvp['Tipo de Prompt'],
        df_tvp['Total Vulnerabilidades (Vi)'],
        color=['#4C72B0', '#55A868', '#C44E52'],
    )

    plt.bar_label(bars, padding=3)

    plt.title('Total de Vulnerabilidades por Tipo de Prompt')
    plt.xlabel('Tipo de Prompt')
    plt.ylabel('Total Vulnerabilidades')

    plt.tight_layout()

    plt.savefig('graphs/vulnerabilidades_prompt.png')

    if 'prompt_type' in df_severidade.columns:
        df_filtrado = df_severidade[['prompt_type', 'Alto', 'Médio', 'Baixo']].set_index('prompt_type')
    else:
        df_filtrado = df_severidade[['Alto', 'Médio', 'Baixo']]

    df_filtrado['Total'] = df_filtrado.sum(axis=1)
    df_filtrado = df_filtrado.sort_values(by='Total', ascending=True) # Deixa a maior barra no topo
    df_filtrado = df_filtrado.drop(columns=['Total'])

    cores = ['#D32F2F', '#F57C00', '#FBC02D'] # Vermelho, Laranja e Amarelo

    ax = df_filtrado.plot(kind='barh', stacked=True, color=cores, width=0.6)

    plt.title('Severidade das Vulnerabilidades por Tipo de Prompt')
    plt.xlabel('Total de Vulnerabilidades')
    plt.ylabel('Tipo de Prompt')
    plt.legend(title='Severidade')
    plt.tight_layout()
    plt.savefig('graphs/vulnerabilidades_severidade.png')


if __name__ == "__main__":
    prompt_severity_analysis()