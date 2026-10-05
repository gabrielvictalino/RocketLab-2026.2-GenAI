# CineData Analytics — agente Text-to-SQL

Projeto da atividade **GenAI — RocketLab 2026.2**. Permite fazer perguntas em português sobre o catálogo CineData pelo terminal. O agente usa **PydanticAI** e **NVIDIA Nemotron 3 Super 120B A12B**, na versão gratuita do OpenRouter (`nvidia/nemotron-3-super-120b-a12b:free`), para gerar consultas SQL, executá-las na camada Gold SQLite e explicar os resultados.

O projeto foi mantido localmente, conforme solicitado. Não depende de GitHub, servidor de banco, Databricks. O SQLite fornecido é aberto somente para leitura e não precisa ser movido ou renomeado.

## 1. Pré-requisitos

- Python **3.11 ou superior**; ambiente validado com Python 3.12 no Windows.
- Acesso à internet para instalar dependências e consultar o modelo.
- Uma chave do [OpenRouter](https://openrouter.ai/settings/keys), com acesso a `nvidia/nemotron-3-super-120b-a12b:free`. Não é necessário comprar créditos para usar essa variante gratuita, sujeita às cotas e à disponibilidade do serviço.
- O arquivo SQLite fornecido na atividade, já presente nesta pasta em `cinerocket-db/cinerocket (1).db`.

O banco é local, mas a inferência ocorre pela API do OpenRouter: a pergunta, o schema e os resultados das consultas utilizadas pelo agente são enviados ao OpenRouter e ao provedor que atende o modelo. O arquivo SQLite inteiro não é enviado. A variante configurada é gratuita; permanecem limites de uso e disponibilidade. Uma pergunta do agente pode consumir várias requisições.

## 2. Preparar o ambiente no Windows

Abra o PowerShell na pasta do projeto:

```powershell
Set-Location 'C:\Users\gabri\GenAI - RocketLab 2026.2'
```

**Nesta máquina já foi preparado um ambiente `.venv` com as dependências.** Você pode ir diretamente à configuração da chave, na seção 3. Para recriar o ambiente em outra máquina, instale Python e execute:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Se você usa outra versão compatível, substitua `py -3.12` pelo comando do seu Python, como `python`. O `requirements.txt` fixa as versões diretas e transitivas usadas na validação, incluindo pytest. O `pyproject.toml` descreve as dependências principais do projeto; não é necessário instalar o pacote para usar `python -m cinedata` dentro desta pasta.

Os comandos usam diretamente o Python da `.venv`, portanto não exigem ativar o ambiente nem alterar a política de execução do PowerShell.

### Linux e macOS

Na pasta do projeto:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
# Edite .env e preencha OPENROUTER_API_KEY antes de continuar.
.venv/bin/python -m cinedata
```

Essa sequência é fornecida como orientação de portabilidade; a validação local foi feita no Windows.

## 3. Configurar chave e banco

Na primeira execução, copie o arquivo de exemplo:

```powershell
Copy-Item .env.example .env
notepad .env
```

Preencha a chave:

```dotenv
OPENROUTER_API_KEY=sua_chave_do_openrouter
DATABASE_PATH=cinerocket-db/cinerocket (1).db
```

Se `.env` já existir, apenas edite-o; não o sobrescreva com o exemplo. Não coloque a chave no código ou no README. `.env` está incluído no `.gitignore` como precaução, embora nenhum repositório Git tenha sido iniciado para esta entrega.

`OPENROUTER_API_KEY` e `DATABASE_PATH` também podem ser variáveis de ambiente do processo; nesse caso prevalecem sobre `.env`. A opção `--db` prevalece sobre `DATABASE_PATH`. Caminhos relativos são resolvidos a partir da raiz deste projeto, inclusive os passados em `--db`.

Se você já tinha configurado a versão anterior, preencha `OPENROUTER_API_KEY` com uma chave do OpenRouter. A antiga variável `GOOGLE_API_KEY` não é utilizada.

O modelo é fixado no código como `nvidia/nemotron-3-super-120b-a12b:free`: NVIDIA Nemotron 3 Super 120B A12B, com suporte a ferramentas e saídas estruturadas no endpoint gratuito verificado. Essa capacidade motivou sua escolha para Text-to-SQL; a qualidade das respostas deve ser conferida com os resultados reais. Não há seleção aleatória de modelos nem fallback para modelos pagos no aplicativo. A mesma `OPENROUTER_API_KEY` continua sendo usada; não é necessário criar outra chave. Preserve o sufixo `:free`, que identifica a variante gratuita.

## 4. Executar

### Uma pergunta

```powershell
.\.venv\Scripts\python.exe -m cinedata "Quais são os 10 filmes com maior receita em reais?"
```

### Modo interativo

```powershell
.\.venv\Scripts\python.exe -m cinedata
```

Digite a pergunta depois de `Pergunta>`. Use `sair`, `exit`, `quit` ou Ctrl+C no prompt para encerrar. Cada pergunta é independente: não existe memória de conversa. Por exemplo, escreva “Quais são os cinco filmes de ação mais populares?” em vez de “E os de ação?” depois de outra pergunta.

### Outro arquivo SQLite

```powershell
.\.venv\Scripts\python.exe -m cinedata --db 'C:\dados\cinerocket.db' "Quantos filmes existem por gênero?"
```

### Ajuda

```powershell
.\.venv\Scripts\python.exe -m cinedata --help
```

A saída apresenta a explicação do agente, cada SQL efetivamente executado e seus resultados em JSON com `colunas` e `linhas`. O SQL e as linhas exibidos vêm da execução real, não de uma reconstituição pelo modelo. Se houver mais de 100 linhas, o terminal sinaliza o truncamento. Uma resposta de esclarecimento pode não executar SQL.

No modo de pergunta única, código de saída `0` indica resposta/esclarecimento concluído, `1` indica falha e `130` indica interrupção. O modo interativo permite tentar outra pergunta após uma falha.

## 5. Perguntas da atividade

As cinco categorias e os 14 exemplos do PDF orientam as instruções do agente e os testes SQL:

| Categoria | Exemplos de perguntas |
| --- | --- |
| Bilheteria e finanças | “Quais são os 10 filmes com maior receita em R$?”; “Qual o lucro médio por gênero, considerando filmes com receita informada?”; “Quais filmes têm maior margem de lucro, com receita e orçamento informados?” |
| Popularidade e engajamento | “Quais são os cinco filmes mais populares?”; “Quais filmes têm maior divergência entre notas TMDB e IMDb?”; “Qual a nota média IMDb por ano de lançamento?” |
| Elenco e equipe | “Qual ator participou de mais filmes lançados nos últimos cinco anos?”; “Quais diretores têm maior nota média, com no mínimo cinco filmes?”; “Qual dupla ator-diretor mais trabalhou junta?” |
| Gêneros e produtoras | “Quantos filmes existem por gênero?”; “Qual produtora tem o maior lucro total?”; “Qual gênero tem a maior margem de lucro média?” |
| Avaliações dos usuários | “Quais filmes foram mais avaliados pelos usuários?”; “Em quais filmes a nota média dos usuários mais diverge da nota IMDb?” |

O SQL é gerado a partir da pergunta, não selecionado de uma lista fixa. Perguntas adicionais são possíveis desde que possam ser respondidas com o schema disponível. A interpretação é probabilística; conferir o SQL e os filtros exibidos é parte da leitura do resultado.

## 6. Regras de análise

- **Receita, faturamento e bilheteria** são sinônimos. BRL é a moeda padrão; utiliza-se o valor já convertido da Gold. Não se consulta câmbio atual. USD pode ser pedido explicitamente.
- **Lucro:** `receita - orçamento`, usando apenas filmes com ambos informados. Isso vale também para lucro médio por gênero e lucro total por produtora. Assim, a consulta de lucro médio exige orçamento conhecido além da receita indicada no exemplo do PDF.
- **Margem de lucro:** `100.0 * (receita - orçamento) / receita`, com receita positiva e orçamento informado. A margem média por gênero é a média das margens individuais. Não é retorno sobre orçamento nem margem calculada a partir da soma das receitas.
- **Valores ausentes:** nunca são substituídos por zero. Os campos de lucro armazenados na base têm zeros quando faltam valores financeiros; por isso o lucro é recalculado. Resultado vazio significa ausência de registros para os filtros, e não valor zero.
- **Notas:** IMDb é o padrão para perguntas sem fonte explícita. Todas as notas estão na escala 0–10. Divergência é diferença absoluta, em pontos; pares com nota ausente são excluídos, mas nota zero é válida.
- **Diretores:** o mínimo de cinco filmes se aplica aos filmes distintos com nota informada utilizados na média. A média é simples, sem ponderação pela quantidade de votos.
- **Últimos cinco anos:** janela móvel inclusiva até a data local de execução. Por exemplo, em 05/10/2026 o intervalo vai de 05/10/2021 a 05/10/2026. Datas futuras e datas ausentes ficam fora. Em 29 de fevereiro, o início recua para 28 de fevereiro se necessário.
- **Pessoas:** os papéis disponíveis são `Ator`, `Diretor` e `Roteirista`. Participações e colaborações contam filmes distintos por ID.
- **Avaliações dos usuários:** utiliza-se o agregado Gold `dim_reviews`, com médias arredondadas. `movie_reviews` contém avaliações individuais. Esses dados são diferentes de votos IMDb/TMDB.
- **Gêneros:** os valores da base estão em inglês; o agente recebe instruções para traduzir os filtros em português e consultar valores quando necessário.
- **Múltiplos gêneros/produtoras:** cada filme contribui integralmente para cada grupo associado. Não há rateio; somar subtotais de grupos pode contar o mesmo filme mais de uma vez.
- **Rankings:** respeitam o N solicitado; sem N, listagens/rankings usam dez itens. Perguntas pelo maior valor devem preservar empates quando possível. O limite de exibição continua sendo 100 linhas.

Essas regras orientam o modelo. O executor garante leitura e limites técnicos, mas não prova automaticamente que todo SQL gerado segue corretamente todas as regras semânticas.

## 7. Estrutura e funcionamento

```text
cinedata/
  __init__.py
  __main__.py         # entrada: python -m cinedata
  cli.py              # argumentos, .env, interação e apresentação
  agent.py            # instruções, Nemotron 3 Super, ferramenta SQL e resposta tipada
  database.py         # schema e execução SQLite somente leitura
tests/
  conftest.py         # banco sintético e bloqueio de chamadas externas
  test_agent.py       # ciclo PydanticAI com modelo simulado
  test_categories.py  # consultas SQL das cinco categorias
  test_cli.py         # execução pelo terminal e configuração
  test_database.py   # leitura, bloqueio de escrita e limites
cinerocket-db/
  cinerocket (1).db   # banco original fornecido
.env.example
pyproject.toml
requirements.txt
README.md
```

Fluxo de uma pergunta:

1. O terminal carrega a configuração e verifica as dez tabelas exigidas.
2. O agente recebe a pergunta, o schema real, a data atual e as regras de negócio.
3. Nemotron 3 Super chama a ferramenta `consultar_sql` com uma consulta SQLite.
4. O executor abre uma conexão somente leitura e retorna colunas e linhas.
5. O agente interpreta os resultados. SQL inválido pode ser corrigido dentro dos limites de tentativas.
6. O terminal imprime a resposta e a evidência das consultas bem-sucedidas.

A resposta tipada distingue `resposta` de `esclarecimento`. Uma resposta classificada como análise de dados precisa ter ao menos uma consulta executada com sucesso; caso contrário, o PydanticAI pede correção ao modelo.

### Modelo dimensional

| Tabela | Papel e ligação principal |
| --- | --- |
| `dim_movies` | Filme, título, sinopse, idioma, duração e lançamento; chave `sk_movie_id` |
| `fact_movies_performance` | Finanças, popularidade e notas; um registro por `sk_movie_id` |
| `dim_genres` | Gêneros; chave `sk_genre_id` |
| `dim_people` | Pessoa e papel; chave `sk_person_id` |
| `dim_companies` | Produtoras; chave `sk_company_id` |
| `bridge_movie_genre` | Liga filmes a gêneros |
| `bridge_movie_person` | Liga filmes a pessoas |
| `bridge_movie_company` | Liga filmes a produtoras |
| `dim_reviews` | Contagem e nota média dos usuários por filme |
| `movie_reviews` | Avaliações individuais com nota, texto e data |

O schema é lido diretamente do SQLite; `alembic_version` é metadado técnico e não é exposto ao agente. A base fornecida contém 95.645 filmes e inclui lançamentos futuros, o que torna necessário o limite superior de data nas análises de filmes já lançados.

### Limites técnicos

- Conexão SQLite com `mode=ro` e `PRAGMA query_only=ON`.
- Autorizador SQLite permite leitura das dez tabelas de domínio e funções analíticas aprovadas; bloqueia escrita, anexação de bancos, comandos administrativos e carregamento de extensões.
- Uma instrução SQL por chamada; até 20.000 caracteres de SQL.
- Até 100 linhas retornadas; agregações continuam sendo calculadas sobre todos os registros filtrados.
- Limite de aproximadamente 30 segundos por consulta, verificado pelo progress handler SQLite.
- Até oito solicitações ao modelo e seis chamadas de ferramenta por pergunta; até duas tentativas de correção por validação conforme o PydanticAI.
- Timeout de 60 segundos configurado para requisições ao modelo; não é um limite global de duração da pergunta.
- Até 64 MiB de cache interno de páginas por conexão SQLite para os joins; liberado ao fechar. Não há cache de respostas, cópia do banco ou mudança de índices.

Esses controles implementam o requisito de consulta somente leitura e evitam execuções sem limite. Não foram adicionados interface visual, gráficos, memória, busca semântica, fallback, integração Databricks ou serviço web.

## 8. Testar

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes não precisam de chave nem fazem chamadas à API. A suíte verifica:

- execução das consultas de referência dos 14 exemplos no banco sintético e no SQLite fornecido;
- cálculo de lucro/margem com ausências, zero, prejuízo e múltiplos gêneros;
- janela de datas inclusiva e exclusão de filmes futuros;
- bloqueio de escrita e integridade do arquivo sintético após tentativas de alteração;
- limite de tempo, truncamento e resultados vazios;
- ciclo de ferramenta e resposta do PydanticAI usando `FunctionModel`, incluindo correção de SQL inválido e recusa de resposta sem consulta.
- interface de terminal, configuração ausente e independência entre perguntas.

Validação local em **05/10/2026**: a suíte completa passou com **52 testes**, incluindo
os 14 testes sobre a Gold fornecida, na integração inicial com OpenRouter. Após a
troca para `nvidia/nemotron-3-super-120b-a12b:free`, os **9 testes do agente e do terminal** foram executados
novamente e aprovados. A integração usa `OpenRouterModel` e PydanticAI 1.107.7.
O fluxo HTTP do OpenRouter, incluindo chamada de ferramenta e resposta estruturada,
é verificado com transporte simulado. Também foi feita uma chamada real com Nemotron
3 Super gratuito: a pergunta sobre a quantidade de filmes executou uma consulta SQL
e retornou **95.645 filmes**. A troca corrigiu o HTTP 404 da variante gratuita do Qwen,
que o OpenRouter informou não estar mais disponível gratuitamente.

Se a base original não estiver no caminho padrão, os 14 testes que a utilizam serão marcados como ignorados; os demais continuam funcionando. As consultas de referência ficam apenas nos testes, não são roteadas pelo programa em produção e não constituem um sistema adicional de avaliação de LLM.

**Limite da validação:** a chamada real confirmou o fluxo completo para uma pergunta de contagem, não todas as categorias. Testes com modelo simulado e SQL de referência não medem a qualidade de todas as consultas geradas pelo modelo real. Confira a resposta, o SQL e as linhas exibidas nas demais análises.

## 9. Resolver problemas

| Sintoma | O que verificar |
| --- | --- |
| `py`/`python` não encontrado | Instale Python 3.11+ e reabra o terminal. Nesta pasta, use diretamente `.\.venv\Scripts\python.exe` se o ambiente existente estiver disponível. |
| `No module named ...` | Instale `requirements.txt` usando o Python da mesma `.venv` usada para executar o programa. |
| Chave não configurada | Crie `.env` a partir do exemplo e preencha `OPENROUTER_API_KEY`. |
| HTTP 400/401/403 | Verifique chave, permissões e acesso à API do OpenRouter. |
| HTTP 402 | Confirme que está executando esta versão com `nvidia/nemotron-3-super-120b-a12b:free` e confira as restrições da conta no OpenRouter; uma conta com saldo negativo pode ter bloqueios mesmo em modelos gratuitos. |
| HTTP 404 | Verifique a disponibilidade de `nvidia/nemotron-3-super-120b-a12b:free` para sua conta/API. |
| HTTP 429 | A cota/limite da API pode ter sido atingido; verifique a conta e aguarde antes de tentar novamente. |
| Banco não encontrado | Confira `DATABASE_PATH` ou `--db`; mantenha aspas em caminhos com espaços. O programa não cria um banco vazio. |
| Tabelas ausentes | Use a camada Gold completa fornecida na atividade, com as dez tabelas listadas acima. |
| Consulta não concluída | Verifique rede/cota; formule uma pergunta mais específica. SQL muito caro ou tentativas excessivas são interrompidos. |
| Resultados truncados | Peça um top N menor, adicione filtros ou solicite uma agregação. |
| Resultado financeiro inesperado | Confira moeda, valores ausentes, definição de margem e duplicação natural entre grupos. |

## 10. Referências

- Enunciado local: `Atividade GenAI - RocketLab 26.2 Perfis vdev.docx.pdf`.
- [PydanticAI: integração com OpenRouter](https://ai.pydantic.dev/models/openrouter/).
- [PydanticAI: testes com modelos simulados](https://ai.pydantic.dev/testing/).
- [NVIDIA Nemotron 3 Super 120B A12B gratuito no OpenRouter](https://openrouter.ai/nvidia/nemotron-3-super-120b-a12b:free).
- [Python sqlite3](https://docs.python.org/3/library/sqlite3.html).

O tutorial OpenRouter original foi preservado como material recebido. Esta implementação usa `nvidia/nemotron-3-super-120b-a12b:free`, conforme a preferência por inferência gratuita.
