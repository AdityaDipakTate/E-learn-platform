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
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    os.environ["GEMINI_API_KEY"] = gemini_api_key
client = genai.Client() # Initializes the new SDK automatically using the environment variable

# 2. Configure Local AI for the database search (Downloads on first run)
print("Loading local AI embedder...")
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
GEMINI_MODEL_NAME = "gemini-2.5-flash"
embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
print("Local AI loaded!")
app = FastAPI(title="AI CS E-Learning Platform")
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Vite's default ports
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Kept as fallback
    allow_origin_regex=".*", # 🟢 Safely allows ALL origins while keeping credentials True
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
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    lessons = db.query(models.Lesson).filter(models.Lesson.course_id == course_id).all()
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

@app.post("/ai/chat", response_model=schemas.ChatResponse)
def ai_chat(
    request: schemas.ChatRequest, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_message = request.message
    normalized_message = user_message.lower()
    search_terms = [word for word in normalized_message.replace("-", " ").split() if len(word) > 2]
    if "oops" in normalized_message or "oop" in normalized_message or "object oriented" in normalized_message:
        search_terms.extend([
            "object",
            "oriented",
            "programming",
            "oop",
            "class",
            "classes",
            "encapsulation",
            "inheritance",
            "polymorphism",
            "abstraction",
        ])

    def fetch_keyword_context():
        rows = db.execute(text("""
            SELECT title, content
            FROM lessons
            ORDER BY id
        """)).fetchall()

        def score(row):
            haystack = f"{row.title} {row.content}".lower().replace("-", " ")
            return sum(1 for term in set(search_terms) if term in haystack)

        ranked_rows = sorted(rows, key=score, reverse=True)
        return [row for row in ranked_rows if score(row) > 0][:4]
    
    try:
        # STEP 1: Generate a 384-dimensional embedding LOCALLY (No API needed!)
        query_embedding = embedder.encode(user_message).tolist()
        
        # STEP 2: Query PostgreSQL using pgvector
        query = text("""
            SELECT title, content 
            FROM lessons 
            WHERE content_embedding IS NOT NULL
            ORDER BY content_embedding <=> :embedding 
            LIMIT 2
        """)
        try:
            results = fetch_keyword_context()
            if not results:
                results = db.execute(query, {"embedding": str(query_embedding)}).fetchall()
            if not results:
                results = db.execute(text("""
                    SELECT title, content
                    FROM lessons
                    ORDER BY id
                    LIMIT 4
                """)).fetchall()
        except Exception:
            db.rollback()
            results = fetch_keyword_context()
            if not results:
                results = db.execute(text("""
                    SELECT title, content
                    FROM lessons
                    ORDER BY id
                    LIMIT 4
                """)).fetchall()
        
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
            model=GEMINI_MODEL_NAME,
            contents=prompt,
        )
        
        return {"reply": response.text}

    except Exception as e:
        return {"reply": f"System Error: {str(e)}"}
