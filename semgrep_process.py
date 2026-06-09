import json
import re
import pandas as pd
from db import get_connection
import os
from dotenv import load_dotenv

load_dotenv()

SEMGREP_JSON_PATH = os.getenv("SEMGREP_JSON_PATH")

SEVERITY_WEIGHTS = {
    "ERROR": 3,
    "WARNING": 2,
    "INFO": 1
}

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

def parse_snippet_id(path_string):
    """
    Extrai o ID do snippet a partir do caminho do arquivo.
    Exemplo: "SnippetsPY\\D-A01-EN-PY-C4.py" -> "D-A01-EN-PY-C4"
    """
    # Captura a parte do nome do arquivo antes da extensão
    match = re.search(r'([^\\/]+)\.[^.]+$', path_string)
    if match:
        return match.group(1)
    return path_string

def map_owasp_to_2025(owasp_string):
    """
    Normaliza tags OWASP antigas encontradas no Semgrep para a versão de referência 2025.
    """
    if not owasp_string:
        return "N/A"
    
    standard_match = re.search(r'(A\d{2}:\d{4})', owasp_string)
    return standard_match.group(1) if standard_match else owasp_string

def process_semgrep_results(json_path):
    """
    Processa resultados do Semgrep e desduplicada resultados duplicados.

    Problema resolvido: Quando a mesma vulnerabilidade é detectada por regras
    diferentes (pro_rules vs community), mantém apenas a com severidade mais alta.
    """
    with open(json_path, 'r', encoding='utf-16') as f:
        data = json.load(f)

    results = data.get("results", data) if isinstance(data, dict) else data

    rows = []
    seen_issues = set()

    severity_weights = {"ERROR": 3, "WARNING": 2, "INFO": 1}
    consolidated_rows = {}

    for item in results:
        path = item.get("path", "")
        snippet_id = parse_snippet_id(path)

        parts = snippet_id.split('-')

        prompt_type_map = {"Z": "zero-shot", "F": "few-shot", "D": "detalhado", "A": "adversarial"}
        code_lang_map = {"PY": "Python", "CS": "C#"}
        llm_map = {"G5": "GPT 5.2", "C4": "Claude 4.5 Haiku"}

        p_type = prompt_type_map.get(parts[0], parts[0]) if len(parts) > 0 else "Unknown"
        owasp_aim = (parts[1] + ":2025") if len(parts) > 1 else "Unknown"
        p_lang = "Portuguese" if len(parts) > 2 and parts[2] == "PT" else "English"
        c_lang = code_lang_map.get(parts[3], parts[3]) if len(parts) > 3 else "Unknown"
        llm_model = llm_map.get(parts[4], parts[4]) if len(parts) > 4 else "Unknown"

        start_info = item.get("start", {})
        line = str(start_info.get("line", "Unknown"))

        # Extração de dados de segurança do Semgrep
        metadata = item.get("extra", {}).get("metadata", {})
        current_severity = item.get("extra", {}).get("severity", "INFO").upper()

        subcategories = metadata.get("subcategory", ["vuln"])
        current_subcategory = subcategories[0] if isinstance(subcategories, list) else subcategories

        cwes = metadata.get("cwe", ["N/A"])
        cwe_list = cwes if isinstance(cwes, list) else [cwes]

        cwe_formatted = ", ".join([cwe_item.split(':')[0].strip() for cwe_item in cwe_list])

        rule_key = metadata.get("semgrep.dev", {}).get("rule", {}).get("rule_id", "")

        owasp_raw = metadata.get("owasp", "N/A")
        owasp_list = owasp_raw if isinstance(owasp_raw, list) else [owasp_raw]

        if owasp_list:
            owasp_item = max(
                owasp_list, 
                key=lambda x: int(re.search(r':(\d{4})', str(x)).group(1)) if re.search(r':(\d{4})', str(x)) else 0
            )
        else:
            owasp_item = "N/A"

        issue_fingerprint = (snippet_id, tuple(cwe_formatted), line)

        if issue_fingerprint not in seen_issues:
            seen_issues.add(issue_fingerprint)
            
            new_row = {
                "id_snippet": snippet_id,
                "prompt_type": p_type,
                "prompt_language": p_lang,
                "code_language": c_lang,
                "llm_model": llm_model,
                "owasp_aim": owasp_aim,
                "severity": current_severity,
                "category": current_subcategory,  
                "line": line,
                "cwe_detected": cwe_formatted,
                "owasp_detected": map_owasp_to_2025(owasp_item)
            }
            rows.append(new_row)
            consolidated_rows[issue_fingerprint] = new_row
            print(f"Processada issue [{rule_key}] para o snippet {snippet_id}")
        
        else:
            existing_severity = consolidated_rows[issue_fingerprint]["severity"]
            existing_weight = severity_weights.get(existing_severity, 0)
            current_weight = severity_weights.get(current_severity, 0)

            if current_weight > existing_weight:
                    consolidated_rows[issue_fingerprint]["severity"] = current_severity
                    consolidated_rows[issue_fingerprint]["category"] = current_subcategory
                    consolidated_rows[issue_fingerprint]["owasp_detected"] = map_owasp_to_2025(owasp_item)

    df = pd.DataFrame(rows)

    if not df.empty:
        save_to_db(df, table_name="semgrep_results")
        print(f"\nSucesso! {len(df)} linhas individuais salvas.")
    else:
        print("\nNenhuma issue foi encontrada ou processada.")

    return df

if __name__ == "__main__":
    try:
        process_semgrep_results(SEMGREP_JSON_PATH)
        
    except FileNotFoundError:
        print(f"Erro: arquivo não encontrado. Verifique o caminho.")