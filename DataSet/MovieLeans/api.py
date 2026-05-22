import os
import unicodedata
import pandas as pd
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD

from scipy.sparse import csr_matrix

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

BASE = r'D:\Code\Python\especialista_filmes\DataSet\MovieLeans'

app = FastAPI(title="CineAI – Movie Recommender")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# CARREGA DATASETS
# ─────────────────────────────────────────────────────────────

print("⏳ Carregando datasets...")

ratings = pd.read_csv(
    os.path.join(BASE, 'ratings.csv'),
    encoding='latin-1'
)

movies = pd.read_csv(
    os.path.join(BASE, 'movies.csv'),
    encoding='latin-1'
)

tags = pd.read_csv(
    os.path.join(BASE, 'tags.csv'),
    encoding='latin-1'
)

# ─────────────────────────────────────────────────────────────
# PRÉ-PROCESSAMENTO
# ─────────────────────────────────────────────────────────────

tags['tag'] = tags['tag'].fillna('')

tags_agg = tags.groupby('movieId')['tag'].apply(
    lambda x: ' '.join(x.astype(str))
).reset_index()

df = movies.merge(
    tags_agg,
    on='movieId',
    how='left'
)

df['tag'] = df['tag'].fillna('')

df['genres_clean'] = df['genres'].fillna('').str.replace(
    '|',
    ' ',
    regex=False
)

df['soup'] = (
    df['genres_clean']
    +
    ' '
    +
    df['tag']
)

df = df.reset_index(drop=True)

# ─────────────────────────────────────────────────────────────
# RATINGS MÉDIOS
# ─────────────────────────────────────────────────────────────

avg_ratings = ratings.groupby('movieId').agg(
    avg_rating=('rating', 'mean'),
    num_ratings=('rating', 'count')
).reset_index()

avg_ratings['avg_rating'] = (
    avg_ratings['avg_rating'].round(2)
)

df = df.merge(
    avg_ratings,
    on='movieId',
    how='left'
)

df['avg_rating'] = (
    df['avg_rating'].fillna(0)
)

df['num_ratings'] = (
    df['num_ratings']
    .fillna(0)
    .astype(int)
)

# ─────────────────────────────────────────────────────────────
# CONTENT-BASED
# ─────────────────────────────────────────────────────────────

print("⏳ Construindo matriz TF-IDF...")

tfidf = TfidfVectorizer(
    stop_words='english',
    max_features=10000
)

tfidf_matrix = tfidf.fit_transform(
    df['soup']
)

# ─────────────────────────────────────────────────────────────
# COLLABORATIVE FILTERING
# ─────────────────────────────────────────────────────────────

print("⏳ Treinando SVD...")

movie_counts = ratings['movieId'].value_counts()

user_counts = ratings['userId'].value_counts()

filtered = ratings[
    ratings['movieId'].isin(
        movie_counts[
            movie_counts >= 20
        ].index
    )
    &
    ratings['userId'].isin(
        user_counts[
            user_counts >= 20
        ].index
    )
]

user_ids = filtered['userId'].unique()

movie_ids = filtered['movieId'].unique()

user_map = {
    u: i
    for i, u in enumerate(user_ids)
}

movie_map = {
    m: i
    for i, m in enumerate(movie_ids)
}

rows = filtered['userId'].map(user_map)

cols = filtered['movieId'].map(movie_map)

vals = filtered['rating'].values

sparse_matrix = csr_matrix(
    (vals, (rows, cols)),
    shape=(
        len(user_ids),
        len(movie_ids)
    )
)

svd = TruncatedSVD(
    n_components=50,
    random_state=42
)

U = svd.fit_transform(sparse_matrix)

Vt = svd.components_

print("✅ Sistema pronto!")
print(f"🎬 Filmes: {len(df)}")
print(f"👥 Usuários: {len(user_ids)}")

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def normalize_text(text):

    text = str(text).lower().strip()

    text = unicodedata.normalize(
        'NFKD',
        text
    ).encode(
        'ascii',
        errors='ignore'
    ).decode('utf-8')

    return text


def _movie_info(movie_id: int):

    row = df[df['movieId'] == movie_id]

    if row.empty:
        return {}

    r = row.iloc[0]

    return {
        "movieId": int(r['movieId']),
        "title": r['title'],
        "genres": (
            r['genres'].split('|')
            if pd.notna(r['genres'])
            else []
        ),
        "avgRating": float(r['avg_rating']),
        "numRatings": int(r['num_ratings'])
    }

# ─────────────────────────────────────────────────────────────
# ROOT
# ─────────────────────────────────────────────────────────────

@app.get("/")
def root():

    return {
        "message": "CineAI API funcionando 🚀"
    }

# ─────────────────────────────────────────────────────────────
# SEARCH
# ─────────────────────────────────────────────────────────────

@app.get("/search")
def search(q: str, limit: int = 10):

    key = normalize_text(q)

    df['title_norm'] = df['title'].apply(
        normalize_text
    )

    matches = df[
        df['title_norm'].str.contains(
            key,
            na=False
        )
    ]

    matches = matches.sort_values(
        by=['num_ratings', 'avg_rating'],
        ascending=False
    )

    results = matches.head(limit)

    return [
        _movie_info(mid)
        for mid in results['movieId'].tolist()
    ]

# ─────────────────────────────────────────────────────────────
# CONTENT-BASED
# ─────────────────────────────────────────────────────────────

@app.get("/recommend/content")
def recommend_content(
    title: str,
    n: int = 10
):

    key = normalize_text(title)

    df['title_norm'] = df['title'].apply(
        normalize_text
    )

    matches = df[
        df['title_norm'].str.contains(
            key,
            na=False
        )
    ]

    if matches.empty:

        raise HTTPException(
            status_code=404,
            detail=f"Nenhum filme encontrado para '{title}'."
        )

    matches = matches.sort_values(
        by=['num_ratings', 'avg_rating'],
        ascending=False
    )

    movie_row = matches.iloc[0]

    idx = movie_row.name

    movie_title = movie_row['title']

    movie_vec = tfidf_matrix[idx]

    scores = cosine_similarity(
        movie_vec,
        tfidf_matrix
    ).flatten()

    top_idx = scores.argsort()[::-1][1:n+1]

    results = []

    for i in top_idx:

        info = _movie_info(
            int(df.iloc[i]['movieId'])
        )

        info['score'] = round(
            float(scores[i]),
            4
        )

        results.append(info)

    return {
        "source": movie_title,
        "recommendations": results
    }

# ─────────────────────────────────────────────────────────────
# COLLABORATIVE
# ─────────────────────────────────────────────────────────────

@app.get("/recommend/collaborative")
def recommend_collaborative(
    userId: int,
    n: int = 10
):

    if userId not in user_map:

        raise HTTPException(
            status_code=404,
            detail=f"Usuário {userId} não encontrado."
        )

    u_idx = user_map[userId]

    pred = U[u_idx] @ Vt

    rated_movies = set(
        filtered[
            filtered['userId'] == userId
        ]['movieId'].tolist()
    )

    top_idx = np.argsort(pred)[::-1]

    results = []

    for i in top_idx:

        mid = movie_ids[i]

        if mid in rated_movies:
            continue

        info = _movie_info(int(mid))

        if not info:
            continue

        info['score'] = round(
            float(pred[i]),
            4
        )

        results.append(info)

        if len(results) >= n:
            break

    return {
        "userId": userId,
        "recommendations": results
    }

# ─────────────────────────────────────────────────────────────
# HÍBRIDO
# ─────────────────────────────────────────────────────────────

@app.get("/recommend/hybrid")
def recommend_hybrid(
    title: str,
    userId: int,
    n: int = 10
):

    key = normalize_text(title)

    df['title_norm'] = df['title'].apply(
        normalize_text
    )

    matches = df[
        df['title_norm'].str.contains(
            key,
            na=False
        )
    ]

    if matches.empty:

        raise HTTPException(
            status_code=404,
            detail=f"Nenhum filme encontrado para '{title}'."
        )

    matches = matches.sort_values(
        by=['num_ratings', 'avg_rating'],
        ascending=False
    )

    movie_row = matches.iloc[0]

    idx = movie_row.name

    movie_title = movie_row['title']

    movie_vec = tfidf_matrix[idx]

    content_scores = cosine_similarity(
        movie_vec,
        tfidf_matrix
    ).flatten()

    cf_scores = np.zeros(len(df))

    if userId in user_map:

        u_idx = user_map[userId]

        pred = U[u_idx] @ Vt

        for i, mid in enumerate(movie_ids):

            df_idx = df[
                df['movieId'] == mid
            ].index

            if len(df_idx) > 0:
                cf_scores[df_idx[0]] = pred[i]

    def norm(arr):

        mn = arr.min()

        mx = arr.max()

        return (
            (arr - mn)
            /
            (mx - mn + 1e-9)
        )

    hybrid = (
        0.5 * norm(content_scores)
        +
        0.5 * norm(cf_scores)
    )

    top_idx = hybrid.argsort()[::-1][1:n+1]

    results = []

    for i in top_idx:

        info = _movie_info(
            int(df.iloc[i]['movieId'])
        )

        info['score'] = round(
            float(hybrid[i]),
            4
        )

        results.append(info)

    return {
        "source": movie_title,
        "userId": userId,
        "recommendations": results
    }

# ─────────────────────────────────────────────────────────────
# FILME
# ─────────────────────────────────────────────────────────────

@app.get("/movie/{movie_id}")
def movie_detail(movie_id: int):

    info = _movie_info(movie_id)

    if not info:

        raise HTTPException(
            status_code=404,
            detail="Filme não encontrado."
        )

    return info

# ─────────────────────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────────────────────

@app.get("/stats")
def stats():

    return {
        "totalMovies": len(df),
        "totalRatings": len(ratings),
        "totalUsers": ratings['userId'].nunique(),
        "svdMovies": len(movie_ids),
        "svdUsers": len(user_ids)
    }

# ─────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )