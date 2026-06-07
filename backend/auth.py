from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt

# Security Constants (In a production app, SECRET_KEY goes in a .env file!)
SECRET_KEY = "your-super-secret-key-change-this-later" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # Keeps them logged in for 1 week

# Setup Bcrypt for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Checks if the typed password matches the hashed one in the database."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Turns a raw password into a secure hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict):
    """Generates the JWT token for the frontend."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt