import pandas as pd
import os

BASE = r'D:\Code\Python\especialista_filmes\DataSet\MovieLeans'

ratings = pd.read_csv(os.path.join(BASE, 'ratings.csv'))

# LEITURA CORRETA
movies = pd.read_csv(os.path.join(BASE, 'movies.csv'))

tags = pd.read_csv(os.path.join(BASE, 'tags.csv'))

# Remove tags vazias
tags['tag'] = tags['tag'].fillna('')

# Agrega tags por filme
tags_agg = tags.groupby('movieId')['tag'].apply(
    lambda x: ' '.join(x.astype(str))
).reset_index()

# Junta tudo
df = movies.merge(tags_agg, on='movieId', how='left')

# Preenche NaN
df['tag'] = df['tag'].fillna('')

# Limpa gêneros
df['genres_clean'] = df['genres'].str.replace('|', ' ', regex=False)

# Cria soup
df['soup'] = df['genres_clean'] + ' ' + df['tag']

print(df.shape)

print(df[['movieId', 'title', 'genres', 'tag']].head())