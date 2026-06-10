import pandas as pd
from db import get_engine

def code_language_analysis():
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM clean_dataset", con=engine)
    
    if df.empty:
        print("A tabela clean_dataset está vazia.")
        return

    # Base Explodida: Apenas para a taxonomia de CWEs
    df['cwe_list'] = df['cwe_detected'].fillna('N/A').astype(str).str.split(',\s*')
    df_exploded = df.explode('cwe_list').reset_index(drop=True)
    df_exploded['cwe_list'] = df_exploded['cwe_list'].str.strip()

    # DENSIDADE DE VULNERABILIDADES REAL & SEVERIDADE PONDERADA
    print("\n=======================================================")
    print("1. DENSIDADE E SEVERIDADE DE VULNERABILIDADES POR LINGUAGEM")
    print("=======================================================")
    
    # Cria a tabela cruzada original de Linguagem vs Severidade
    df_orig_lang = pd.crosstab(df['code_language'], df['severity'])
    
    for col in ['Alto', 'Médio', 'Baixo']:
        if col not in df_orig_lang.columns:
            df_orig_lang[col] = 0

    # Consolida nos 3 níveis de peso definidos na metodologia (IGUAL Q1 e Q2)
    df_lang_sev = pd.DataFrame(index=df_orig_lang.index)
    df_lang_sev['Alto'] = df_orig_lang['Alto']
    df_lang_sev['Médio'] = df_orig_lang['Médio']
    df_lang_sev['Baixo'] = df_orig_lang['Baixo']
    df_lang_sev['Total Falhas Real'] = df_orig_lang.sum(axis=1)

    N_lang = {
        "Python": 60,
        "C#": 60 
    }
    
    # Mapeia as amostras e calcula a Densidade Real (Falhas Reais / Total Amostras)
    df_lang_sev['Total Amostras (Ni)'] = df_lang_sev.index.map(N_lang).fillna(1)
    df_lang_sev['Densidade (Falhas/Snippet)'] = (df_lang_sev['Total Falhas Real'] / df_lang_sev['Total Amostras (Ni)']).round(2)

    # Calcula a Severidade Média Ponderada da Linguagem
    pontuacao_lang = (df_lang_sev['Alto'] * 3) + \
                     (df_lang_sev['Médio'] * 2) + \
                     (df_lang_sev['Baixo'] * 1)
    df_lang_sev['Severidade Média'] = (pontuacao_lang / df_lang_sev['Total Falhas Real']).round(2)

    print("\nTabela de Densidade e Severidade por Linguagem (Base Real):")
    print(df_lang_sev[['Alto', 'Médio', 'Baixo', 'Total Falhas Real', 'Densidade (Falhas/Snippet)', 'Severidade Média']])


    # PERFIL DE VULNERABILIDADE POR LINGUAGEM (TAXONOMIA CWE)
    print("\n=======================================================")
    print("2. PERFIL DE VULNERABILIDADE (% POR CATEGORIA CWE COBERTA)")
    print("=======================================================")
    
    perfil_absoluto = pd.crosstab(df_exploded['cwe_list'], df_exploded['code_language'])
    
    # Garante que as colunas existam no crosstab para evitar KeyError
    for lang in ['Python', 'C#']:
        if lang not in perfil_absoluto.columns:
            perfil_absoluto[lang] = 0

    perfil_percentual = perfil_absoluto.div(perfil_absoluto.sum(axis=0), axis=1) * 100
    
    resultado_comparativo = pd.DataFrame({
        'Python (Qtd)': perfil_absoluto['Python'],
        'Python (%)': perfil_percentual['Python'].round(2),
        'C# (Qtd)': perfil_absoluto['C#'],
        'C# (%)': perfil_percentual['C#'].round(2)
    }).fillna(0)
    
    resultado_comparativo['Total_Geral'] = resultado_comparativo['Python (Qtd)'] + resultado_comparativo['C# (Qtd)']
    resultado_comparativo = resultado_comparativo.sort_values(by='Total_Geral', ascending=False).drop(columns=['Total_Geral'])
    
    print(resultado_comparativo)

if __name__ == "__main__":
    code_language_analysis()