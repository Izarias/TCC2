import json
import re
import requests
import pandas as pd
from db import get_connection
import os
from dotenv import load_dotenv

load_dotenv()

SONAR_RULES_URL = os.getenv("SONAR_RULES_URL")
SONAR_TOKEN = os.getenv("SONAR_TOKEN")
FOLDER_PATH = os.getenv("FOLDER_PATH")

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

def parse_snippet_id(component_string):
    """
    Extrai o ID do snippet a partir do campo component.
    Exemplo: "TCC2-CS-REPAIRED:D-A04-EN-CS-G5:Program.cs" -> "D-A04-EN-CS-G5"
    """
    match = re.search(r':([^:]+):', component_string)
    if match:
        return match.group(1)
    
    return component_string

def fetch_rule_metadata(rule_key):
    """
    Versão robusta: Faz a requisição na API de regras do SonarQube e extrai 
    MÚLTIPLOS CWEs e categorias OWASP do HTML descritivo, tratando estruturas variadas.
    """
    cwe_detected = "N/A"
    owasp_detected = "N/A"
    
    try:
        response = requests.get(
            f"{SONAR_RULES_URL}?rule_key={rule_key}", 
            auth=(SONAR_TOKEN, ""), 
            timeout=10
        )
        if response.status_code == 200:
            rule_data = response.json()
            rules = rule_data.get("rules", [])
            
            if rules:
                sections = rules[0].get("descriptionSections", [])
                # Une todas as seções de texto/HTML para busca global
                full_html = "".join([sec.get("content", "") for sec in sections])
                
                # --- 1. EXTRAÇÃO DE CWE ---
                cwe_finds = re.findall(r'(?:CWE[- ]|definitions/)(\d+)', full_html, re.IGNORECASE)
                if cwe_finds:
                    # Remove duplicatas mantendo a ordem e formata como CWE-XXX
                    unique_cwes = list(dict.fromkeys([f"CWE-{num}" for num in cwe_finds]))
                    cwe_detected = ", ".join(unique_cwes)
                
                # --- 2. EXTRAÇÃO DE OWASP ---
                owasp_finds = re.findall(
                    r'A(10|0[1-9]|[1-9])[_:](\d{4})',
                    full_html,
                    re.IGNORECASE
                )

                if owasp_finds:
                    unique_owasps = list(dict.fromkeys([
                        f"A{num.zfill(2)}:{year}"
                        for num, year in owasp_finds
                    ]))

                    if unique_owasps:
                        owasp_detected = ", ".join(unique_owasps)
                    
    except Exception as e:
        print(f"Aviso: Falha ao buscar metadados para a regra {rule_key}. Erro: {e}")
        
    return cwe_detected, owasp_detected

def process_sonarqube_results():
    folder_path = FOLDER_PATH
    
    if not os.path.exists(folder_path):
        print(f"Erro: pasta não encontrada.")
        return pd.DataFrame()

    rows = []

    seen_issues = set()
    severity_weights = {"BLOCKER": 3, "CRITICAL": 2, "MAJOR": 1, "MINOR": 0}
    consolidated_rows = {}

    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                print(f"Não foi possível ler o arquivo {filename}. Erro: {e}")
                continue

            issues = data.get("issues", [])
            
            for issue in issues:
                component = issue.get("component", "")
                snippet_id = parse_snippet_id(component)
                
                parts = snippet_id.split('-')
                if len(parts) < 5:
                    continue 
                    
                prompt_type_map = {"Z": "zero-shot", "F": "few-shot", "D": "detalhado", "A": "adversarial"}
                code_lang_map = {"PY": "Python", "CS": "C#"}
                llm_map = {"G5": "GPT 5.2", "C4": "Claude 4.5 Haiku"}
                
                p_type = prompt_type_map.get(parts[0], parts[0])
                owasp_aim = (parts[1] + ":2025") if len(parts) > 1 else "Unknown"
                p_lang = "Portuguese" if parts[2] == "PT" else "English"
                c_lang = code_lang_map.get(parts[3], parts[3])
                llm_model = llm_map.get(parts[4], parts[4])

                current_severity = issue.get("severity", "INFO").upper()
                rule_key = issue.get("rule", "")
                category = issue.get("type", "UNKNOWN").upper()
                line = issue.get("line", "N/A")

                cwe_detected, owasp_detected = fetch_rule_metadata(rule_key)

                issue_fingerprint = (snippet_id, rule_key, tuple(cwe_detected), line)

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
                        "category": category,  
                        "line": line,
                        "cwe_detected": cwe_detected,
                        "owasp_detected": owasp_detected
                    }
                    rows.append(new_row)
                    consolidated_rows[issue_fingerprint] = new_row
                    print(f"Processada issue [{rule_key}] para o snippet {snippet_id} (Arquivo: {filename})")

                else:
                    existing_severity = consolidated_rows[issue_fingerprint]["severity"]
                    existing_weight = severity_weights.get(existing_severity, 0)
                    current_weight = severity_weights.get(current_severity, 0)

                    if current_weight > existing_weight:
                        consolidated_rows[issue_fingerprint]["severity"] = current_severity
                        consolidated_rows[issue_fingerprint]["category"] = category
                        consolidated_rows[issue_fingerprint]["owasp_detected"] = owasp_detected

    df = pd.DataFrame(rows)
    
    if not df.empty:
        save_to_db(df, table_name="sonarqube_results")
        print(f"\nSucesso! {len(df)} linhas individuais processadas e salvas.")
    else:
        print("\nNenhuma issue foi encontrada ou processada nos arquivos JSON.")
        
    return df

if __name__ == "__main__":
    process_sonarqube_results()