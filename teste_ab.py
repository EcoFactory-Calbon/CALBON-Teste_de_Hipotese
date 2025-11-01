from pathlib import Path
import sys
import pandas as pd
import pingouin as pg

BASE_DIR = Path(__file__).parent

EXPECTED_SCREENS = 5
COLUMNS_TO_KEEP = ['Tester ID', 'Total duration (seconds)']

def read_and_aggregate(flow_prefix: str) -> pd.Series:
    """
    Lê os CSVs nomeados <flow_prefix>_tela1.csv ... _tela5.csv,
    concatena, filtra colunas e agrega soma de duração por Tester ID.
    Retorna uma Series indexada por Tester ID com a soma das durações.
    """
    files = [BASE_DIR / f"{flow_prefix}_tela{i}.csv" for i in range(1, EXPECTED_SCREENS + 1)]
    missing = [str(f) for f in files if not f.exists()]
    if missing:
        print("Erro: arquivos não encontrados:")
        for m in missing:
            print("  ", m)
        sys.exit(1)

    dfs = [pd.read_csv(f) for f in files]
    full = pd.concat(dfs, ignore_index=True)

    if not set(COLUMNS_TO_KEEP).issubset(full.columns):
        print("Erro: colunas esperadas não encontradas nos CSVs. Esperado:", COLUMNS_TO_KEEP)
        sys.exit(1)

    full = full[COLUMNS_TO_KEEP].copy()
    full['Total duration (seconds)'] = pd.to_numeric(full['Total duration (seconds)'], errors='coerce')
    full = full.dropna(subset=['Tester ID', 'Total duration (seconds)'])

    agg = full.groupby('Tester ID')['Total duration (seconds)'].sum()
    return agg

def main():
    a_series = read_and_aggregate("testeA")
    b_series = read_and_aggregate("testeB")

    print("Estatísticas - Fluxo A (duração total por usuário):")
    print(a_series.describe().to_string())
    print("\nEstatísticas - Fluxo B (duração total por usuário):")
    print(b_series.describe().to_string())

    a_vals = a_series.values
    b_vals = b_series.values

    res = pg.ttest(a_vals, b_vals, paired=False, alternative='two-sided')
    if res.empty:
        print("Erro: resultado do teste t está vazio. Verifique os dados de entrada e se há valores válidos nas amostras.")
        print(res)
        sys.exit(1)

    t_stat = res.iloc[0]['T']
    p_val = res.iloc[0]['p-val']

    try:
        cohens_d = pg.compute_effsize(a_vals, b_vals, paired=False, eftype='cohen')
    except Exception:
        cohens_d = float('nan')

    print("\n--- Resultado do teste t (bilateral) ---")
    print(res.to_string(index=False))
    print(f"\nt = {t_stat:.4f}")
    print(f"p-value = {p_val:.4f}")
    if not pd.isna(cohens_d):
        print(f"Cohen's d = {cohens_d:.4f}")
    else:
        print("Cohen's d = NA")

    alpha = 0.05
    print("\nConclusão (alfa = {:.2f}):".format(alpha))
    if p_val < alpha:
        print("Diferença estatisticamente significativa entre os fluxos (rejeita H0).")
    else:
        print("Sem evidência estatística suficiente de diferença entre os fluxos (não rejeita H0).")

if __name__ == "__main__":
    main()
