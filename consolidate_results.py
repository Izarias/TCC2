import pandas as pd
from db import get_engine, get_connection

def save_to_db(df, table_name):
    if df.empty:
        return

    conn = get_connection()
    cursor = conn.cursor()

    columns = df.columns.tolist()
    col_names = ", ".join(f"`{c}`" for c in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    updates = ", ".join(f"`{c}` = VALUES(`{c}`)" for c in columns)

    sql = f"""
        INSERT INTO `{table_name}` ({col_names})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {updates}
    """

    data = [tuple(row) for row in df.itertuples(index=False, name=None)]

    cursor.executemany(sql, data)
    conn.commit()

    print(f"[{table_name}] {cursor.rowcount} linhas afetadas.")
    cursor.close()
    conn.close()

def unify_and_consolidate_results():
    engine = get_engine()
    
    print("Carregando tabelas do MySQL...")
    df_sonar = pd.read_sql("SELECT * FROM sonarqube_results", con=engine)
    df_semgrep = pd.read_sql("SELECT * FROM semgrep_results", con=engine)
    
    if df_sonar.empty and df_semgrep.empty:
        print("Ambas as tabelas estão vazias. Encerrando processo.")
        return
        
    print(f"Registros encontrados -> SonarQube: {len(df_sonar)} | Semgrep: {len(df_semgrep)}")

    df_merged = pd.merge(
        df_sonar, 
        df_semgrep, 
        on=['id_snippet', 'line', 'cwe_detected'], 
        how='outer', 
        suffixes=('_sonar', '_semgrep')
    )

    rows_unificadas = []
    
    severity_weights = {
        "BLOCKER": 3, "CRITICAL": 2, "MAJOR": 1, "MINOR": 0, 
        "ERROR": 3, "INFO": 1, "WARNING": 2
    }

    for _, row in df_merged.iterrows():
        has_sonar = pd.notna(row.get('category_sonar'))
        has_semgrep = pd.notna(row.get('category_semgrep'))
        
        p_type = row['prompt_type_sonar'] if has_sonar else row['prompt_type_semgrep']
        p_lang = row['prompt_language_sonar'] if has_sonar else row['prompt_language_semgrep']
        c_lang = row['code_language_sonar'] if has_sonar else row['code_language_semgrep']
        llm_model = row['llm_model_sonar'] if has_sonar else row['llm_model_semgrep']
        owasp_aim = row['owasp_aim_sonar'] if has_sonar else row['owasp_aim_semgrep']
        
        if has_sonar and has_semgrep:
            tools = "SonarQube, Semgrep"
            
            # 1. Escolhe a maior severidade entre as duas
            sev_sonar = str(row['severity_sonar']).upper()
            sev_semgrep = str(row['severity_semgrep']).upper()
            severity = row['severity_sonar'] if severity_weights.get(sev_sonar, 0) >= severity_weights.get(sev_semgrep, 0) else row['severity_semgrep']
            
            # 2. Prioriza o OWASP do Semgrep se o do Sonar for N/A ou vazio
            owasp_sonar = str(row['owasp_detected_sonar']).strip()
            owasp_semgrep = str(row['owasp_detected_semgrep']).strip()
            
            if pd.notna(row['owasp_detected_semgrep']) and owasp_semgrep not in ["N/A", "", "None"]:
                owasp_detected = row['owasp_detected_semgrep']
            else:
                owasp_detected = owasp_sonar
                
            category = row['category_sonar']
            
        elif has_sonar:
            tools = "SonarQube"
            severity = row['severity_sonar']
            owasp_detected = row['owasp_detected_sonar']
            category = row['category_sonar']
            
        else: # Só tem no Semgrep
            tools = "Semgrep"
            severity = row['severity_semgrep']
            owasp_detected = row['owasp_detected_semgrep']
            category = row['category_semgrep']

        rows_unificadas.append({
            "id_snippet": row['id_snippet'],
            "prompt_type": p_type,
            "prompt_language": p_lang,
            "code_language": c_lang,
            "llm_model": llm_model,
            "owasp_aim": owasp_aim,
            "severity": severity,
            "category": category,  
            "line": row['line'],
            "cwe_detected": row['cwe_detected'],
            "owasp_detected": owasp_detected,
            # "ferramentas_origem": tools
        })

    # 3. Transforma a lista de volta em um DataFrame limpo
    df_final = pd.DataFrame(rows_unificadas)
    
    print(f"Consolidação concluída! Total de vulnerabilidades únicas: {len(df_final)}")

    if not df_final.empty:
        save_to_db(df_final, table_name="unified_results")
        print(f"\nSucesso! {len(df_final)} linhas individuais salvas.")
    else:
        print("\nNenhuma issue foi encontrada ou processada.")

    return df_final

if __name__ == "__main__":
    unify_and_consolidate_results()