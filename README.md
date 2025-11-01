<h1 align="center">🌱 TESTE A/B 🌍</h1>

---

## 📖 O que o script faz?

O script implementa um teste A/B para comparar o tempo total gasto por usuários em duas versões de um mesmo fluxo de teste (Fluxo A e Fluxo B).
O objetivo principal é verificar se há diferença estatisticamente significativa entre as médias de duração dos dois fluxos.
>💡 **Nota:** Cada fluxo contém 5 telas
 
---

## 🤖 Passo a Passo do funcionamento do código

- Importar bibliotecas necessárias:
  
| Import | Descrição |
|:-------|:-----------|
| 🏢 **`Path`** | manipula caminhos de arquivos de forma robusta e independente do sistema operacional. |
| 👨‍💼 **`sys`** | usado para encerrar o programa `(sys.exit(1))` em caso de erro crítico |
| 📍 **`pandas`** | manipula e agrega dados dos CSVs. |
| 📍 **`pingouin`** | biblioteca estatística para testes t e outros. |

```bash
from pathlib import Path
import sys
import pandas as pd
import pingouin as pg

```

##

- Pegar os dados necessários
|:-------|:-----------|
| 🏢 **`BASE_DIR`** | obtém o diretório onde o script está localizado, garantindo que os arquivos sejam buscados no mesmo local do código. |
| 👨‍💼 **`EXPECTED_SCREENS`** | número esperado de telas (arquivos CSV) por fluxo (tela1.csv até tela5.csv). |
| 📍 **`COLUMNS_TO_KEEP`** | define as únicas colunas relevantes para a análise — o identificador do testador e o tempo total gasto. |

```bash
BASE_DIR = Path(__file__).parent
EXPECTED_SCREENS = 5
COLUMNS_TO_KEEP = ['Tester ID', 'Total duration (seconds)']
```


##
- Ler 5 arquivos CSV correspondentes a um fluxo (ex: testeA_tela1.csv até testeA_tela5.csv), somar o tempo total gasto por cada testador e retornar essa soma como uma pandas Series.
  
```bash
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
    # Garantir tipo numérico e remover NaNs
    full['Total duration (seconds)'] = pd.to_numeric(full['Total duration (seconds)'], errors='coerce')
    full = full.dropna(subset=['Tester ID', 'Total duration (seconds)'])

    agg = full.groupby('Tester ID')['Total duration (seconds)'].sum()
    return agg

```

##
- Roda todos os processos juntos e depois fecha a conexão
<details>
<summary>🔍 Explicação detalhada do que é feito e da execução</summary>

o código imprime as estatísticas descritivas de cada fluxo. Esse passo serve para compreender o comportamento geral dos dados antes do teste estatístico.
O método .describe() do pandas retorna um resumo com informações como:

| Medida | Descrição |
|:-------|:-----------|
| **count** | quantos usuários participaram do teste naquele fluxo |
| **mean** | média dos tempos (quanto tempo, em média, um usuário levou para completar o fluxo) |
| **std** | desvio padrão, que mostra o quanto os tempos variam entre os usuários |
| **min e max** | os valores extremos observados (tempo mínimo e máximo) |
| **quartis** | indicam como os tempos se distribuem (por exemplo, a mediana é o tempo que divide os usuários em dois grupos iguais) |

Esses números ajudam a visualizar se os dados de um dos fluxos são muito dispersos, se há usuários que demoraram muito mais que outros (outliers) e se as médias parecem muito diferentes ou não.

Depois disso, as séries de duração são transformadas em arrays NumPy:

``` bash
a_vals = a_series.values
b_vals = b_series.values
```

Esse passo é necessário porque a função estatística do Pingouin (pg.ttest) trabalha diretamente com arrays numéricos. A ideia é preparar os dados para o teste t de Student, que será o cálculo central da análise.

O teste t é então executado por meio da função:

```bash
res = pg.ttest(a_vals, b_vals, paired=False, alternative='two-sided')
```

Aqui acontece a comparação estatística entre os fluxos. O teste t verifica se a diferença entre as médias dos dois fluxos é grande o suficiente para não poder ser explicada apenas por variações aleatórias.

Como `paired=False`, o teste assume que os grupos são independentes (ou seja, os testadores do fluxo A não são necessariamente os mesmos do fluxo B).

E o parâmetro `alternative='two-sided'` indica que se trata de um teste bilateral, ou seja, não queremos saber se o fluxo A é maior ou menor, apenas se existe diferença entre eles, em qualquer direção.

A função retorna um DataFrame com vários resultados: a estatística t (T), o grau de liberdade (dof), o p-value, o intervalo de confiança (CI95%), o Cohen’s d ( Ele mede o tamanho da diferença entre duas médias, mostrando quão grande é o efeito em termos de desvios padrão.), o fator de Bayes (BF10) e o poder estatístico (power).

O p-value indica a probabilidade de observar uma diferença igual ou maior que essa, caso a hipótese nula (de que as médias são iguais) seja verdadeira.
Se o p-value for menor que o nível de significância adotado (geralmente 0.05), a diferença é considerada estatisticamente significativa.

> 💡 **Nota:** Depois de calcular o teste t, o código também calcula o Cohen’s d, que é o tamanho da diferença entre duas médias, mostrando quão grande é o efeito em termos de desvios padrão. Enquanto o p-value responde “essa diferença é real ou apenas sorte?”, o Cohen’s d responde “essa diferença é grande o bastante para importar?”. Ele mede a diferença entre as médias em unidades de desvio padrão, permitindo avaliar se a diferença, mesmo que real, tem magnitude pequena ou relevante. Por exemplo, um Cohen’s d próximo de 0.2 indica que as médias diferem em apenas 0.2 desvios padrão — uma diferença muito pequena, perceptível apenas em grandes amostras.

Com esses valores calculados, o código imprime o resultado formatado.
Ele mostra o valor de t, o p-value, o Cohen’s d, e interpreta o resultado à luz de um nível de significância de 5% (α = 0.05).
Se o p-value for menor que 0.05, o código conclui que existe diferença estatisticamente significativa entre os fluxos — ou seja, o tempo médio de um fluxo é diferente do outro com um nível de confiança de 95%.
Se o p-value for maior que 0.05, o programa entende que não há evidência suficiente para afirmar que os fluxos diferem — e portanto “não rejeita a hipótese nula”.

No caso da saída apresentada, o teste t retornou um valor t = 0.8674 e p-value = 0.3961, muito acima do limite de 0.05, o que indica que a diferença entre os tempos médios do fluxo A e do fluxo B é compatível com o acaso. O Cohen’s d = 0.2961 reforça essa interpretação: a diferença entre as médias existe, mas é pequena e provavelmente sem relevância prática.

Por fim, a função main() imprime a conclusão de forma interpretável: “Sem evidência estatística suficiente de diferença entre os fluxos (não rejeita H0)”.
Isso quer dizer que, com base nesses dados e nesse tamanho de amostra, não há motivos para acreditar que o fluxo A seja realmente mais lento ou mais rápido que o fluxo B — a variação observada pode ser apenas fruto do comportamento natural dos usuários.

</details>

>💡 **Nota:** Para abrir a explicação, clique na seta na esquerda. Ela contém o funcionamente e explicação final de cada ponto do código e também da saída.

```bash
def main():
    a_series = read_and_aggregate("testeA")
    b_series = read_and_aggregate("testeB")

    print("Estatísticas - Fluxo A (duração total por usuário):")
    print(a_series.describe().to_string())
    print("\nEstatísticas - Fluxo B (duração total por usuário):")
    print(b_series.describe().to_string())

    # Preparar arrays para o teste (amostras independentes)
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

```
---

## ✅ Saída do Código

- Saída do Fluxo A
  *  19 Usuários participaram
  *  Média de 934 s (muito alta, mas com grande dispersão).
  *  Desvio padrão (2585) mostra grande variação: alguns usuários gastaram muito mais tempo.
 
- Saída do Fluxo B
  * 24 Usuários participaram
  * Média menor (407 s).
  * Menor desvio padrão → tempo mais consistente entre usuários.
 
- Resultado

| Medida | Descrição |
|:-------|:-----------|
| **T = 0.8674** | diferença entre as médias é pequena em relação à variabilidade. |
| **dof = 19.765** | graus de liberdade ajustados conforme tamanhos e desvios. |
| **p-val = 0.3961** | muito acima de 0.05, não há diferença estatística significativa. |
| **CI95% = [-741.17, 1795.06]** | intervalo de confiança das médias; contém o zero → reforça ausência de diferença. |
| **Cohen’s d = 0.2961** | efeito pequeno (diferença fraca).|
| **BF10 = 0.408** | fator de Bayes < 1 → dados favorecem H₀. |
| **power = 0.1561** | poder estatístico baixo (alta chance de erro tipo II, amostras pequenas). |

>💡 **Nota:** BF₁₀ (Bayes Factor) indica quanto mais os dados apoiam a hipótese alternativa em relação à nula; Power (poder estatístico) é a probabilidade de detectar um efeito real quando ele existe; Erro tipo II (β) é a falha em detectar um efeito real, ou seja, aceitar a hipótese nula quando ela é falsa.


```bash
Estatísticas - Fluxo A (duração total por usuário):
count       19.000000
mean       934.043158
std       2585.456141
min         26.710000
25%        110.315000
50%        247.400000
75%        542.420000
max      11515.240000

Estatísticas - Fluxo B (duração total por usuário):
count      24.000000
mean      407.100000
std       642.392639
min        15.300000
25%       101.205000
50%       165.115000
75%       427.662500
max      3065.800000

--- Resultado do teste t (bilateral) ---
       T       dof alternative    p-val              CI95%  cohen-d  BF10    power
0.867445 19.765475   two-sided 0.396108 [-741.17, 1795.06] 0.296139 0.408 0.156181

t = 0.8674
p-value = 0.3961
Cohen's d = 0.2961

Conclusão (alfa = 0.05):
Sem evidência estatística suficiente de diferença entre os fluxos (não rejeita H0).
```

## ⚖️ Licença

Este projeto está sob a licença [**MIT**](https://choosealicense.com/licenses/mit/).  

---

<h3 align="center">✨ Desenvolvido para CALBON - Escolher fluxo para o Aplicativo 🌿</h3>
