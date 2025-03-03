import basedosdados as bd
import pandas as pd
from datetime import datetime, date

# Carregar a planilha e formatar os CNPJs corretamente
df_planilha = pd.read_excel("planilha_de_cnpjs.xlsx")

# Remover caracteres não numéricos e espaços extras
df_planilha['cnpj'] = df_planilha['CNPJs'].astype(str).str.replace(r'\D', '', regex=True).str.strip()

# Criar lista de CNPJs
lista_cnpjs = df_planilha['cnpj'].tolist()

# Verifica se a lista não está vazia
if not lista_cnpjs:
    raise ValueError("A planilha está vazia ou não contém uma coluna válida de CNPJs.")

# Converter a lista de CNPJs para consulta SQL
cnpjs_para_sql = ", ".join(f"'{cnpj}'" for cnpj in lista_cnpjs)

# Data para validação do Simples Nacional
data_atual = date.today()
primeiro_dia_mes = data_atual.replace(day=1)
ultimo_dia_ano = date(data_atual.year, 12, 31)

# Consulta SQL filtrando apenas os CNPJs da planilha
query = f"""
SELECT
    cnpj_basico,
    opcao_simples,
    data_opcao_simples,
    data_exclusao_simples
FROM `basedosdados.br_me_cnpj.simples`
WHERE cnpj_basico IN ({cnpjs_para_sql})
"""

# Executa a consulta
df = bd.read_sql(query, billing_project_id="simples-nacional-452014")

# Converter a coluna 'data_exclusao_simples' para datetime.date
df['data_exclusao_simples'] = pd.to_datetime(df['data_exclusao_simples']).dt.date

# Criar a coluna 'simples_nacional'
df['simples_nacional'] = df['data_exclusao_simples'].apply(
    lambda x: pd.isna(x) or (primeiro_dia_mes <= x <= ultimo_dia_ano)
)

# Separar os resultados
df_simples = df[df['simples_nacional'] == True]
df_nao_simples = df[df['simples_nacional'] == False]

# Criar um conjunto de CNPJs retornados pela consulta
cnpjs_encontrados = set(df['cnpj_basico'])

# Identificar os CNPJs que não foram encontrados
cnpjs_nao_encontrados = set(lista_cnpjs) - cnpjs_encontrados
df_nao_encontrados = pd.DataFrame({'cnpj': list(cnpjs_nao_encontrados)})

# Salvar os arquivos CSV
df_simples.to_csv("cnpjs_simples_nacional.csv", index=False)
df_nao_simples.to_csv("cnpjs_nao_simples_nacional.csv", index=False)
df_nao_encontrados.to_csv("cnpjs_nao_encontrados.csv", index=False)

print(f"Processo concluído! Arquivos gerados:")
print(f"- {len(df_simples)} CNPJs Simples Nacional")
print(f"- {len(df_nao_simples)} CNPJs Não Simples Nacional")
print(f"- {len(df_nao_encontrados)} CNPJs não encontrados na base de dados")


