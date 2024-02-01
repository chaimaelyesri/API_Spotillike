from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from tortoise.contrib.fastapi import HTTPNotFoundError, register_tortoise
from tortoise.transactions import in_transaction
from models import Album, Artist, Genre, Track, User
from tortoise.contrib.pydantic import pydantic_model_creator
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

app = FastAPI()

# Configuration de l'authentification JWT
SECRET_KEY = "test"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configuration du hachage du mot de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fonctions d'authentification et d'autorisation
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception: HTTPException):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"}
    )
    return verify_token(token, credentials_exception)

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.is_active:
        return current_user
    raise HTTPException(status_code=400, detail="Inactive user")

# Modèles Pydantic
Album_Pydantic = pydantic_model_creator(Album)
Artist_Pydantic = pydantic_model_creator(Artist)
Genre_Pydantic = pydantic_model_creator(Genre)
Track_Pydantic = pydantic_model_creator(Track)
User_Pydantic = pydantic_model_creator(User)

class UserIn_Pydantic(BaseModel):
    username: str
    password: str
    email: str

class UserOut_Pydantic(BaseModel):
    username: str

class UserLogin_Pydantic(BaseModel):
    username: str
    password: str

# CRUD Operations

# 1. GET - /api/albums
@app.get("/api/albums", response_model=list[Album_Pydantic])
async def get_albums():
    return await Album_Pydantic.from_queryset(Album.all())

# 2. GET - /api/albums/{id}
@app.get("/api/albums/{album_id}", response_model=Album_Pydantic)
async def get_album(album_id: int):
    return await Album_Pydantic.from_queryset_single(Album.get(id=album_id))

# 3. GET - /api/albums/{id}/songs
@app.get("/api/albums/{album_id}/songs", response_model=list[Track_Pydantic])
async def get_album_songs(album_id: int):
    return await Track_Pydantic.from_queryset(Track.filter(album_id=album_id))

# 4. GET - /api/genres
@app.get("/api/genres", response_model=list[Genre_Pydantic])
async def get_genres():
    return await Genre_Pydantic.from_queryset(Genre.all())

# 5. GET - /api/artists/{id}/songs
@app.get("/api/artists/{artist_id}/songs", response_model=list[Track_Pydantic])
async def get_artist_songs(artist_id: int):
    return await Track_Pydantic.from_queryset(Track.filter(artist_id=artist_id))

# 6. POST - /api/users/signin
@app.post("/api/users/signin", response_model=User_Pydantic)
async def add_user(user: UserIn_Pydantic):
    hashed_password = pwd_context.hash(user.password)
    user_obj = await User.create(username=user.username, password=hashed_password, email=user.email)
    return await User_Pydantic.from_tortoise_orm(user_obj)

# 7. POST - /api/users/login
@app.post("/api/users/login", response_model=Token)
async def login_for_access_token(form_data: UserLogin_Pydantic = Depends()):
    user = await User.get(username=form_data.username)
    if user and pwd_context.verify(form_data.password, user.password):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# 8. POST - /api/albums
@app.post("/api/albums", response_model=Album_Pydantic)
async def add_album(album: Album_Pydantic):
    album_obj = await Album.create(**album.dict())
    return await Album_Pydantic.from_tortoise_orm(album_obj)

# 9. POST - /api/albums/{id}/songs
@app.post("/api/albums/{album_id}/songs", response_model=Track_Pydantic)
async def add_song_to_album(album_id: int, track: Track_Pydantic, current_user: User = Depends(get_current_active_user)):
    track_data = track.dict()
    track_data["album_id"] = album_id
    track_obj = await Track.create(**track_data)
    return await Track_Pydantic.from_tortoise_orm(track_obj)

# 10. PUT - /api/artists/{id}
@app.put("/api/artists/{artist_id}", response_model=Artist_Pydantic)
async def update_artist(artist_id: int, artist: Artist_Pydantic, current_user: User = Depends(get_current_active_user)):
    await Artist.filter(id=artist_id).update(**artist.dict(exclude_unset=True))
    return await Artist_Pydantic.from_queryset_single(Artist.get(id=artist_id))

# 11. PUT - /api/albums/{id}
@app.put("/api/albums/{album_id}", response_model=Album_Pydantic)
async def update_album(album_id: int, album: Album_Pydantic, current_user: User = Depends(get_current_active_user)):
    await Album.filter(id=album_id).update(**album.dict(exclude_unset=True))
    return await Album_Pydantic.from_queryset_single(Album.get(id=album_id))

# 12. PUT - /api/genres/{id}
@app.put("/api/genres/{genre_id}", response_model=Genre_Pydantic)
async def update_genre(genre_id: int, genre: Genre_Pydantic, current_user: User = Depends(get_current_active_user)):
    await Genre.filter(id=genre_id).update(**genre.dict(exclude_unset=True))
    return await Genre_Pydantic.from_queryset_single(Genre.get(id=genre_id))

# 13. DELETE - /api/users/{id}
@app.delete("/api/users/{user_id}", response_model=dict)
async def delete_user(user_id: int, current_user: User = Depends(get_current_active_user)):
    await User.filter(id=user_id).delete()
    return {"message": "User deleted successfully"}

# 14. DELETE - /api/albums/{id}
@app.delete("/api/albums/{album_id}", response_model=dict)
async def delete_album(album_id: int, current_user: User = Depends(get_current_active_user)):
    await Album.filter(id=album_id).delete()
    return {"message": "Album deleted successfully"}

# 15. DELETE - /api/artists/{id}
@app.delete("/api/artists/{artist_id}", response_model=dict)
async def delete_artist(artist_id: int, current_user: User = Depends(get_current_active_user)):
    await Artist.filter(id=artist_id).delete()
    return {"message": "Artist deleted successfully"}

# Configuration de Tortoise-ORM avec FastAPI
register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)