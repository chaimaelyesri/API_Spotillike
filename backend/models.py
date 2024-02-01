from tortoise import Tortoise, fields
from tortoise.models import Model
from datetime import timedelta

class Genre(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255)
    description = fields.TextField()

class Artist(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    avatar = fields.BinaryField()
    biography = fields.TextField()

class Album(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255)
    cover_image = fields.BinaryField()
    release_date = fields.DateField()
    artist = fields.ForeignKeyField('models.Artist', related_name='albums')
    tracks = fields.ManyToManyField('models.Track', related_name='albums')

class Track(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255)
    duration: timedelta
    artist = fields.ForeignKeyField('models.Artist', related_name='tracks')
    genres = fields.ManyToManyField('models.Genre', related_name='tracks')

class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=255)
    password = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255)

# Configurer Tortoise-ORM
TORTOISE_ORM = {
    "connections": {
        "default": "sqlite://db.sqlite3"
    },
    "apps": {
        "models": {
            "models": "models",
            "default_connection": "default",
        }
    }
}

# Initialiser Tortoise
async def init():
    # Check if the event loop is already running
    if Tortoise._inited:
        return

    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()

# Exécuter l'initialisation
# import asyncio

# # Use the existing event loop if one exists, otherwise create a new one
# loop = asyncio.get_event_loop() if asyncio.get_event_loop().is_running() else asyncio.new_event_loop()
# asyncio.set_event_loop(loop)

# loop.run_until_complete(init())
