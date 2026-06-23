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

def preprossessamento_tcc():

    engine = get_engine()
    df = pd.read_sql("SELECT * FROM unified_results WHERE category in ('VULNERABILITY', 'vuln', 'audit')", con=engine)

    # UNIFICAÇÃO DOS NÍVEIS DE SEVERIDADE (Alto, Médio, Baixo)

    def mapear_nivel_severidade(sev_str):
        sev = str(sev_str).strip().upper()
        if sev in ['BLOCKER', 'CRITICAL', 'ERROR']:
            return 'Alto'
        elif sev in ['MAJOR', 'WARNING']:
            return 'Médio'
        elif sev in ['MINOR', 'INFO']:
            return 'Baixo'
        else:
            return 'N/A'

    if 'severity' in df.columns:
        df['severity'] = df['severity'].apply(mapear_nivel_severidade)
        print("-> Níveis de severidade unificados com sucesso em 'severity'.")

    # PARSER E PADRONIZAÇÃO DO OWASP TOP 10 PARA A VERSÃO 2025

    mapeamento_owasp_2025 = {
        'A01:2017': 'A05:2025',                         # Injection
        'A02:2017': 'A07:2025',                         # Authentication
        'A03:2017': 'A04:2025',                         # Cryptographic Failures
        'A06:2017': 'A02:2025',                         # Security Misconfiguration
        'A02:2021': 'A04:2025',                         # Cryptographic Failures (2021)
        'A03:2021': 'A05:2025',                         # Injection (2021)
        'A04:2021': 'A06:2025',                         # Insecure Design (2021)
        'A07:2021': 'A07:2025'                          # Authentication Failures (2021)
    }

    def tratar_e_converter_owasp(owasp_raw):
        if pd.isna(owasp_raw) or str(owasp_raw).strip().upper() in ['N/A', '', 'NONE', 'UNKNOWN']:
            return 'N/A'
        
        itens = str(owasp_raw).split(',')
        itens_convertidos = []
        
        for item in itens:

            token = item.strip().upper().split('-')[0].strip()
            
            if token in mapeamento_owasp_2025:
                token = mapeamento_owasp_2025[token]
                
            if token and token != 'NONE':
                itens_convertidos.append(token)
        
        # Remove duplicados que possam ter surgido na conversão (ex: A06:2017 e A02:2025 no mesmo log)
        itens_unicos = list(dict.fromkeys(itens_convertidos))
        
        return ', '.join(itens_unicos) if itens_unicos else 'N/A'

    if 'owasp_detected' in df.columns:
        df['owasp_detected'] = df['owasp_detected'].apply(tratar_e_converter_owasp)
        print("-> Taxonomia OWASP convertida e unificada para a versão 2025 em 'owasp_detected'.")

    if not df.empty:
        save_to_db(df, table_name="clean_dataset")
        print(f"\nSucesso! {len(df)} linhas individuais salvas.")
    else:
        print("\nTabela vazia.")

if __name__ == "__main__":    
    preprossessamento_tcc()