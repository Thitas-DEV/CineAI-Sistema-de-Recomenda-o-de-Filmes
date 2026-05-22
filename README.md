# 🎬 CineAI — Sistema de Recomendação de Filmes

Sistema de recomendação de filmes com três estratégias distintas: **Content-Based Filtering**, **Collaborative Filtering via SVD** e **Hybrid Recommender**. Construído sobre o dataset MovieLens com backend em FastAPI e interface web.

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Tecnologias](#tecnologias)
- [Dataset](#dataset)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Instalação](#instalação)
- [Como Executar](#como-executar)
- [Endpoints da API](#endpoints-da-api)
- [Estratégias de Recomendação](#estratégias-de-recomendação)
- [Arquitetura](#arquitetura)

---

## Visão Geral

O CineAI implementa as três principais abordagens da literatura de sistemas de recomendação sobre um dataset real de larga escala:

| Estratégia | Base | Quando usar |
|---|---|---|
| **Content-Based** | Gêneros + tags textuais | Usuário sem histórico, busca por similaridade de conteúdo |
| **Collaborative Filtering** | Histórico de ratings (SVD) | Usuário com histórico, descoberta de preferências latentes |
| **Hybrid** | Combinação 50/50 normalizada | Melhor cobertura geral |

**Escala do dataset:**
- 87.585 filmes
- 200.948 usuários
- ~30 milhões de ratings

---

## Tecnologias

| Camada | Tecnologia | Versão |
|---|---|---|
| Linguagem | Python | 3.9+ |
| API REST | FastAPI | latest |
| Servidor ASGI | Uvicorn | latest |
| Manipulação de dados | Pandas | latest |
| Machine Learning | Scikit-learn | latest |
| Álgebra linear | NumPy | latest |
| Matrizes esparsas | SciPy | latest |
| Frontend | HTML + CSS + JavaScript | — |

---

## Dataset

Este projeto utiliza o **[MovieLens Dataset](https://grouplens.org/datasets/movielens/)**, mantido pelo GroupLens Research Lab da Universidade de Minnesota.

### Download

Acesse: https://grouplens.org/datasets/movielens/ e baixe a versão **ml-latest** (dataset completo).

### Arquivos necessários

| Arquivo | Descrição | Tamanho aprox. |
|---|---|---|
| `movies.csv` | Catálogo de filmes (movieId, title, genres) | ~3 MB |
| `ratings.csv` | Ratings dos usuários (userId, movieId, rating, timestamp) | ~900 MB |
| `tags.csv` | Tags textuais atribuídas por usuários | ~70 MB |
| `links.csv` | Correspondência movieId ↔ imdbId ↔ tmdbId | ~2 MB |

> ⚠️ O arquivo `ratings.csv` tem ~900 MB. O carregamento inicial leva entre 30–60 segundos dependendo da máquina.

---

## Estrutura do Projeto

```
especialista_filmes/
│
├── DataSet/
│   └── MovieLeans/
│       ├── api.py          ← Backend FastAPI (ponto de entrada)
│       ├── index.html      ← Frontend web
│       ├── movies.csv      ← Dataset (baixar separado)
│       ├── ratings.csv     ← Dataset (baixar separado)
│       ├── tags.csv        ← Dataset (baixar separado)
│       ├── links.csv       ← Dataset (baixar separado)
│       └── README.txt      ← Documentação original do MovieLens
│
└── README.md
```

---

## Instalação

### Pré-requisitos

- Python 3.9 ou superior
- pip

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/cineai.git
cd cineai
```

### 2. Instale as dependências

```bash
pip install fastapi uvicorn scikit-learn scipy numpy pandas
```

Ou via arquivo de requirements:

```bash
pip install -r requirements.txt
```

**`requirements.txt`:**
```
fastapi
uvicorn
scikit-learn
scipy
numpy
pandas
```

### 3. Baixe o dataset

Acesse https://grouplens.org/datasets/movielens/, baixe o **ml-latest** e extraia os arquivos `movies.csv`, `ratings.csv`, `tags.csv` e `links.csv` dentro de `DataSet/MovieLeans/`.

### 4. Ajuste o caminho no `api.py`

Abra o `api.py` e altere a variável `BASE` na linha 8 para o caminho absoluto da pasta no seu sistema:

```python
# Windows
BASE = r'C:\caminho\para\DataSet\MovieLeans'

# Linux / macOS
BASE = '/caminho/para/DataSet/MovieLeans'
```

---

## Como Executar

### 1. Inicie o servidor

```bash
# Windows
cd DataSet\MovieLeans
python api.py

# Linux / macOS
cd DataSet/MovieLeans
python3 api.py
```

### 2. Aguarde o carregamento

O terminal vai exibir o progresso:

```
⏳ Carregando datasets...
⏳ Construindo matriz TF-IDF...
⏳ Treinando SVD...
✅ Sistema pronto!
🎬 Filmes: 87585
👥 Usuários: 200948
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 3. Acesse a interface

Abra o arquivo `index.html` no navegador ou acesse:

```
http://localhost:8000
```

---

## Endpoints da API

Base URL: `http://localhost:8000`

### `GET /stats`
Retorna estatísticas gerais do dataset carregado.

```json
{
  "totalMovies": 87585,
  "totalRatings": 33832162,
  "totalUsers": 200948,
  "svdMovies": 45000,
  "svdUsers": 120000
}
```

---

### `GET /search?q={query}&limit={n}`
Busca filmes por título (usado no autocomplete).

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `q` | string | obrigatório | Texto para busca |
| `limit` | int | 10 | Número máximo de resultados |

```bash
GET /search?q=toy&limit=5
```

---

### `GET /recommend/content?title={title}&n={n}`
Recomendação por similaridade de conteúdo (gêneros + tags).

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `title` | string | obrigatório | Título exato do filme |
| `n` | int | 10 | Número de recomendações |

```bash
GET /recommend/content?title=Toy Story (1995)&n=10
```

---

### `GET /recommend/collaborative?userId={id}&n={n}`
Recomendação baseada no histórico de ratings do usuário via SVD.

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `userId` | int | obrigatório | ID do usuário (precisa ter ≥ 20 ratings) |
| `n` | int | 10 | Número de recomendações |

```bash
GET /recommend/collaborative?userId=1&n=10
```

---

### `GET /recommend/hybrid?title={title}&userId={id}&n={n}`
Recomendação híbrida combinando content-based e collaborative (50/50).

```bash
GET /recommend/hybrid?title=Toy Story (1995)&userId=1&n=10
```

---

## Estratégias de Recomendação

### Content-Based Filtering

Vetoriza os metadados de cada filme (gêneros + tags dos usuários) usando **TF-IDF** e calcula a **similaridade de cosseno** entre o filme de referência e todos os outros. Não depende do histórico de nenhum usuário.

```
soup = genres + tags_agregadas
      ↓
TfidfVectorizer (max_features=10.000)
      ↓
Matriz esparsa (87585 × 10000)
      ↓
cosine_similarity(filme_alvo, todos_filmes)
      ↓
Top-N mais similares
```

### Collaborative Filtering (SVD)

Constrói a matriz usuário-item esparsa e aplica **Truncated SVD** com 50 componentes latentes para capturar padrões de preferência que não estão explícitos no conteúdo dos filmes.

```
ratings.csv
      ↓
Filtragem (mínimo 20 ratings por usuário/filme)
      ↓
csr_matrix (usuarios × filmes)
      ↓
TruncatedSVD (k=50)  →  U (usuários), Vt (filmes)
      ↓
pred = U[user] @ Vt  →  score para cada filme
      ↓
Top-N com maior score (excluindo já avaliados)
```

### Hybrid

Combina os dois scores com normalização min-max para torná-los comparáveis em escala:

```
score_hybrid = 0.5 × norm(content_score) + 0.5 × norm(cf_score)
```

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                      index.html                         │
│              (Frontend — HTML/CSS/JS)                   │
│  ┌──────────┐  ┌───────────────┐  ┌──────────────────┐  │
│  │ Content  │  │ Collaborative │  │     Hybrid       │  │
│  │  tab     │  │     tab       │  │      tab         │  │
│  └────┬─────┘  └──────┬────────┘  └────────┬─────────┘  │
└───────┼───────────────┼────────────────────┼────────────┘
        │    fetch()    │                    │
        └───────────────┴────────────────────┘
                        │ HTTP REST
┌───────────────────────▼─────────────────────────────────┐
│                   FastAPI (api.py)                       │
│                                                         │
│  /recommend/content   →  TF-IDF + cosine_similarity     │
│  /recommend/collaborative  →  SVD (U @ Vt)              │
│  /recommend/hybrid    →  norm(content) + norm(CF)        │
│  /search              →  título lookup                   │
│  /stats               →  métricas do dataset            │
│                                                         │
│  Modelos carregados em memória no startup               │
└─────────────────────────────────────────────────────────┘
```

---

## Licença

Dataset MovieLens disponível para uso não-comercial conforme os [termos do GroupLens](https://grouplens.org/datasets/movielens/).

---

> Desenvolvido como projeto acadêmico — Engenharia da Computação · UniNobre
