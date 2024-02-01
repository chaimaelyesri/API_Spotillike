# Importez vos modèles
from tortoise import Tortoise, fields, run_async
from models import Artist, Album, Track, Genre, User

# Fonction pour insérer des données fictives
async def insert_data():
    # Insérer des genres
    genre1 = await Genre.create(name="Rock")
    genre2 = await Genre.create(name="Pop")

    # Insérer des artistes
    artist1 = await Artist.create(name="John Artist", avatar=b'...', biography="A talented musician.")
    artist2 = await Artist.create(name="Jane Artist", avatar=b'...', biography="An amazing singer and songwriter.")

    # Insérer des albums
    album1 = await Album.create(id_artist=artist1.id, title="Awesome Album", cover_image=b'...', release_date="2022-01-01")
    album2 = await Album.create(id_artist=artist2.id, title="Greatest Hits", cover_image=b'...', release_date="2022-02-01")

    # Insérer des chansons
    song1 = await Track.create(id_album=album1.id, title="Best Song Ever", duration=240, artist=artist1)
    song2 = await Track.create(id_album=album2.id, title="Hit Single", duration=180, artist=artist2)

    # Insérer des utilisateurs
    user1 = await User.create(username="john_doe", password="hashed_password", email="john@example.com")
    user2 = await User.create(username="jane_doe", password="hashed_password", email="jane@example.com")

# Exécutez la fonction d'insertion de données dans l'événement de boucle asyncio
run_async(insert_data())
