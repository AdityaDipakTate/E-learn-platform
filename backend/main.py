from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import text
import models
from database import engine, get_db,SessionLocal
import schemas
import auth

import jwt
from jwt.exceptions import InvalidTokenError

# from openai import OpenAI
import os

from sentence_transformers import SentenceTransformer
from google import genai # <--- The brand new SDK import
# Configure the free Gemini API

from dotenv import load_dotenv
load_dotenv()
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
client = genai.Client() # Initializes the new SDK automatically using the environment variable

# 2. Configure Local AI for the database search (Downloads on first run)
print("Loading local AI embedder...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')
print("Local AI loaded!")
app = FastAPI(title="AI CS E-Learning Platform")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Vite's default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# This line automatically creates the tables in your PostgreSQL database on startup!
models.Base.metadata.create_all(bind=engine)

# --- DATABASE DEPENDENCY ---
# This opens a fresh database session for each request and closes it after
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@app.get("/")
def read_root():
    return {"message": "Welcome to the Computer Science E-Learning API!"}

# Quick test route to ensure the database connection works smoothly
@app.get("/db-test")
def test_db_connection(db: Session = Depends(get_db)):
    try:
        # Executes a raw, basic query to test the live connection
        db.execute(text("SELECT 1"))
        return {"status": "success", "message": "Database connected successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return {"users": users}

# 
# CONTENT DELIVERY ENDPOINTS (PHASE 1)

@app.get("/courses", response_model=list[schemas.CourseBase])
def get_courses(db: Session = Depends(get_db)):
    """Fetch all available Computer Science courses."""
    courses = db.query(models.Course).all()
    return courses

@app.get("/courses/{course_id}/lessons", response_model=list[schemas.LessonBase])
def get_lessons_for_course(course_id: int, db: Session = Depends(get_db)):
    """Fetch all lessons belonging to a specific course."""
    lessons = db.query(models.Lesson).filter(models.Lesson.course_id == course_id).all()
    
    if not lessons:
        raise HTTPException(status_code=404, detail="Course not found or contains no lessons.")
    
    return lessons

#  USER AUTHENTICATION ENDPOINTS

@app.post("/auth/signup", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registers a new student and hashes their password."""
    # Check if email already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password and save the user
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username, 
        email=user.email, 
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticates a user and returns a JWT token."""
    # Find user by username
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    # Verify user exists AND password is correct
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate the JWT Token
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# --- SECURITY DEPENDENCY ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Decodes the JWT token to find the active user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# USER PROGRESS ENDPOINTS


@app.post("/progress/update")
def update_progress(
    progress: schemas.ProgressUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user) # <-- Protects the route!
):
    """Marks a lesson as completed for the currently logged-in user."""
    # 1. Check if the user already has a progress record for this lesson
    db_progress = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == current_user.id,
        models.UserProgress.lesson_id == progress.lesson_id
    ).first()

    # 2. Update it if it exists, or create a new record if it doesn't
    if db_progress:
        db_progress.is_completed = progress.is_completed
    else:
        new_progress = models.UserProgress(
            user_id=current_user.id,
            lesson_id=progress.lesson_id,
            is_completed=progress.is_completed
        )
        db.add(new_progress)
    
    db.commit()
    return {"status": "success", "message": f"Lesson {progress.lesson_id} progress updated!"}

import time # Import this at the top of main.py if not already there
@app.post("/ai/chat", response_model=schemas.ChatResponse)
def ai_chat(
    request: schemas.ChatRequest, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_message = request.message
    
    try:
        # STEP 1: Generate a 384-dimensional embedding LOCALLY (No API needed!)
        query_embedding = embedder.encode(user_message).tolist()
        
        # STEP 2: Query PostgreSQL using pgvector
        query = text("""
            SELECT title, content 
            FROM lessons 
            ORDER BY content_embedding <=> :embedding 
            LIMIT 2
        """)
        results = db.execute(query, {"embedding": str(query_embedding)}).fetchall()
        
        context_text = "\n\n".join([f"Course Module: {row.title}\n{row.content}" for row in results])
        
        # STEP 3: Prompt the Gemini Chat Model using the NEW syntax
        prompt = f"""You are a helpful Computer Science AI Tutor for {current_user.username}.
        Answer the user's question clearly using ONLY the context provided below.
        
        CURRICULUM CONTEXT:
        {context_text}
        
        USER QUESTION: {user_message}
        """

        # The new SDK generate_content method
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
        )
        
        return {"reply": response.text}

    except Exception as e:
        return {"reply": f"System Error: {str(e)}"}