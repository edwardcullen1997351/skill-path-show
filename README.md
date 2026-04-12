# Skill Path Show - FastAPI Backend Service

A FastAPI backend service for extracting skills from college curricula, identifying skill gaps for target job roles, and generating MECE (Mutually Exclusive, Collectively Exhaustive) subject/elective recommendations.

## Features

- **Curriculum Processing**: Extract skills from text, subject codes, or structured JSON
- **Role Profiles**: Get required skills with weightages for various job roles
- **Gap Analysis**: Identify skill gaps between current skills and target role
- **MECE Recommendations**: Generate minimal, non-overlapping subject recommendations
- **Coverage Simulation**: Simulate skill coverage for selected subjects
- **Skill Similarity**: Find similar skills using semantic embeddings (sentence-transformers) and character n-grams
- **Caching**: TTL-based caching for repeated queries
- **Multi-LLM Integration**: Google Gemini, OpenAI, Anthropic Claude, and Ollama (local)
- **Vector Store**: ChromaDB-based semantic skill matching
- **Skill Ontology**: Hierarchical skill taxonomy with parent/child relationships
- **User Profiles**: Persistent user profiles with Supabase
- **Progress Tracking**: Track learning progress and skill coverage over time
- **Adaptive Recommendations**: Personalized recommendations using collaborative filtering and Q-learning
- **Sequence Optimization**: Optimal learning path sequencing

## Project Structure

```
skill-path-show/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── models/                 # Pydantic models
│   │   ├── curriculum.py       # Curriculum parsing models
│   │   ├── roles.py           # Role profile models
│   │   ├── skills.py          # Skill gap analysis models
│   │   ├── recommendations.py # Recommendation models
│   │   ├── simulation.py      # Coverage simulation models
│   │   └── user.py            # User profile models
│   ├── routers/               # API endpoints
│   │   ├── curriculum.py      # POST /parse-curriculum
│   │   ├── roles.py           # GET /roles/{role_name}
│   │   ├── gap_analysis.py   # POST /analyze-gap
│   │   ├── recommendations.py # POST /recommend-subjects
│   │   ├── simulation.py     # POST /simulate-selection
│   │   ├── similarity.py      # POST /similar-skills
│   │   ├── llm.py            # POST /llm-parse-curriculum
│   │   ├── user.py           # User profile endpoints
│   │   ├── progress.py       # Progress tracking endpoints
│   │   └── adaptive.py       # Adaptive recommendations
│   ├── services/             # Business logic
│   ├── providers/            # LLM provider abstraction
│   │   ├── base.py           # Abstract base class
│   │   ├── gemini_provider.py
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   └── ollama_provider.py
│   ├── utils/                # Utility functions
│   │   ├── data_loader.py    # JSON data loading
│   │   ├── nlp_utils.py     # Text processing
│   │   ├── skill_normalizer.py # Skill mapping
│   │   ├── mece_algorithm.py # Greedy set cover
│   │   ├── similarity.py    # Cosine similarity for skills
│   │   ├── cache.py         # TTL-based caching
│   │   ├── llm_service.py   # Google Gemini LLM integration
│   │   ├── llm_unified.py   # Unified LLM interface
│   │   ├── supabase_client.py # Supabase client
│   │   ├── skill_ontology.py # Hierarchical skill taxonomy
│   │   ├── sequence_optimizer.py # Learning path sequencing
│   │   └── embeddings/      # Vector embeddings
│   │       ├── model.py     # sentence-transformers wrapper
│   │       ├── vector_store.py # ChromaDB integration
│   │       └── skills_index.py # Skills index
│   ├── prompts/              # Prompt templates
│   └── data/                 # JSON data files
│       ├── skills_taxonomy.json
│       ├── role_profiles.json
│       ├── subjects_catalog.json
│       ├── skill_ontology.json
│       └── fine_tuning_examples.json
├── plans/                    # Architecture plans
│   ├── personalized_learning_paths.md
│   └── supabase_schema.sql
├── requirements.txt
├── .env.example
└── README.md
```

## Requirements

- Python 3.9+
- FastAPI
- Uvicorn
- Pydantic
- Supabase (for user profiles & progress tracking)
- sentence-transformers (for semantic embeddings)
- ChromaDB (for vector storage)

### Dependencies (requirements.txt)

```
fastapi>=0.115.0
uvicorn>=0.32.0
pydantic>=2.10.0
genai>=0.7.0
supabase>=2.0.0
python-multipart>=0.0.6
openai>=1.0.0
anthropic>=0.25.0
requests>=2.31.0
sentence-transformers>=2.2.0
chromadb>=0.4.0
numpy>=1.24.0
```

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key

# LLM Provider Configuration
# Choose one or more providers:

# Google Gemini
GOOGLE_API_KEY=your_google_api_key

# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=  # Optional: for custom endpoints

# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_key

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Optional: JWT Secret for authentication
# SECRET_KEY=your_jwt_secret_key_here

# Optional: Embedding model
# EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Installation

1. Clone the repository or navigate to the project directory:

   ```bash
   cd skill-path-show
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up Supabase (if using user profiles):
   - Copy the SQL from `plans/supabase_schema.sql`
   - Run it in your Supabase SQL Editor

4. Copy `.env.example` to `.env` and add your credentials

## Running the Server

### Option 1: Using Uvicorn (Recommended)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Using Python

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Direct Execution

```bash
python app/main.py
```

The API will be available at:

- **Base URL**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Core Endpoints

### 1. POST /api/v1/parse-curriculum

Extract skills from curriculum text or structured data.

**Request:**

```json
{
  "text": "Data Structures, Algorithms, Python Programming, Web Development with React, Database Systems using SQL",
  "subjects": ["CS201", "CS301", "CS302"]
}
```

**Response:**

```json
{
  "subjects": [
    "Data Structures and Algorithms",
    "Web Development Fundamentals",
    "Database Systems"
  ],
  "extracted_skills": [
    {
      "skill": "algorithms",
      "proficiency": "intermediate",
      "source": "Data Structures and Algorithms"
    },
    {
      "skill": "python",
      "proficiency": "intermediate",
      "source": "Text Analysis"
    }
  ],
  "skill_proficiency": "intermediate"
}
```

### 2. GET /api/v1/roles/{role_name}

Get required skills for a target role.

**Response:**

```json
{
  "role_name": "Frontend Developer",
  "role_key": "frontend_developer",
  "required_skills": [
    { "skill": "javascript", "weightage": 0.95 },
    { "skill": "html_css", "weightage": 0.9 },
    { "skill": "react", "weightage": 0.85 }
  ],
  "description": "Builds user interfaces and web applications using modern JavaScript frameworks"
}
```

### 3. POST /api/v1/analyze-gap

Identify gaps between current skills and target role.

**Request:**

```json
{
  "extracted_skills": ["python", "sql", "data_analysis"],
  "target_role": "data_analyst"
}
```

**Response:**

```json
{
  "matched_skills": [
    { "skill": "python", "weightage": 0.9, "matched": true },
    { "skill": "sql", "weightage": 0.85, "matched": true }
  ],
  "missing_skills": ["data_visualization", "statistics"],
  "partial_skills": [],
  "gap_score": 0.65,
  "coverage_percentage": 65.0
}
```

### 4. POST /api/v1/recommend-subjects

Generate MECE subject recommendations.

**Request:**

```json
{
  "missing_skills": ["react", "responsive_design", "api_design"]
}
```

**Response:**

```json
{
  "selected_subjects": [
    {
      "subject_name": "Web Development Fundamentals",
      "subject_code": "CS301",
      "covered_skills": ["html_css", "javascript", "responsive_design"],
      "marginal_contribution": 0.75,
      "redundancy_penalty": 0.0
    }
  ],
  "total_coverage": 0.75,
  "remaining_gaps": []
}
```

### 5. POST /api/v1/simulate-selection

Simulate skill coverage for selected subjects.

**Request:**

```json
{
  "selected_subjects": ["React Development", "Database Systems"],
  "target_role": "frontend_developer"
}
```

**Response:**

```json
{
  "updated_coverage_percent": 45.5,
  "remaining_gaps": ["javascript", "html_css", "git"],
  "skill_coverage_breakdown": [
    {
      "skill": "javascript",
      "covered": true,
      "weightage": 0.95,
      "source_subjects": ["React Development"]
    },
    {
      "skill": "html_css",
      "covered": false,
      "weightage": 0.9,
      "source_subjects": []
    }
  ]
}
```

### 6. POST /api/v1/similar-skills

Find skills similar to a target skill using semantic embeddings or character n-grams.

**Request:** `POST /api/v1/similar-skills?target_skill=python&threshold=0.3&top_k=5`

**Response:**

```json
{
  "target_skill": "python",
  "similar_skills": [
    { "skill": "python", "similarity": 1.0 },
    { "skill": "java", "similarity": 0.45 }
  ],
  "count": 2
}
```

### 7. GET /api/v1/cache-stats

Get cache hit/miss statistics for TTL-based caching.

**Response:**

```json
{
  "role_cache": {
    "size": 5,
    "max_size": 50,
    "hits": 10,
    "misses": 2,
    "hit_rate": 0.833
  },
  "skill_cache": {
    "size": 0,
    "max_size": 100,
    "hits": 0,
    "misses": 0,
    "hit_rate": 0.0
  }
}
```

### 8. GET /api/v1/llm-status

Check if any LLM API is configured and available.

**Response:**

```json
{
  "llm_available": true,
  "providers": ["gemini", "openai", "anthropic", "ollama"],
  "default_provider": "gemini",
  "message": "LLM services ready"
}
```

### 9. POST /api/v1/llm-parse-curriculum

Parse curriculum using LLM for intelligent skill extraction.

**Request:**

```json
{
  "curriculum_text": "Data Structures, Algorithms, Python Programming, Web Development with React",
  "use_llm": true
}
```

**Response:**

```json
{
  "success": true,
  "skills": [
    {
      "name": "algorithms",
      "proficiency": "intermediate",
      "source": "Data Structures"
    },
    {
      "name": "python",
      "proficiency": "intermediate",
      "source": "Python Programming"
    }
  ],
  "proficiency_level": "intermediate"
}
```

### Skill Ontology Endpoints

### 10. GET /api/v1/ontology/skill/{skill_id}

Get skill details including hierarchy relationships.

**Response:**

```json
{
  "skill_id": "python",
  "name": "Python",
  "level": "intermediate",
  "description": "Python programming language",
  "parent": "programming",
  "parent_name": "Programming",
  "children": ["django", "flask", "fastapi"],
  "children_names": ["Django", "Flask", "FastAPI"],
  "related": ["data_science", "machine_learning"],
  "related_names": ["Data Science", "Machine Learning"]
}
```

### 11. GET /api/v1/ontology/related/{skill_id}

Get related skills.

### 12. GET /api/v1/ontology/tree

Get complete skill tree.

### User Profile Endpoints

### 13. POST /api/v1/users/profile

Create a new user profile.

**Request:**

```json
{
  "email": "user@example.com",
  "role_goal": "data_analyst",
  "experience_level": "intermediate",
  "career_interests": ["data science", "machine learning"]
}
```

### 14. GET /api/v1/users/profile

Get the current user's profile.

### 15. PUT /api/v1/users/profile

Update user profile.

### 16. GET /api/v1/users/skills

Get user's skill history.

**Response:**

```json
{
  "skills": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "skill_name": "python",
      "proficiency": "intermediate",
      "acquired_at": "2024-01-15T10:00:00Z"
    }
  ],
  "count": 1
}
```

### 17. POST /api/v1/users/skills

Add a skill to user's history.

**Request:**

```json
{
  "skill_name": "python",
  "proficiency": "intermediate",
  "source_subject": "CS101"
}
```

### 18. GET /api/v1/users/preferences

Get user's learning preferences.

### 19. PUT /api/v1/users/preferences

Update user's learning preferences.

**Request:**

```json
{
  "learning_style": "visual",
  "weekly_hours": 10,
  "difficulty_preference": "balanced"
}
```

### 20. GET /api/v1/users/progress

Get user's learning progress.

### 21. POST /api/v1/users/subjects/complete

Mark a subject as completed.

**Request:**

```json
{
  "subject_code": "CS301",
  "grade": 95.5
}
```

### 22. GET /api/v1/users/skill-coverage

Get skill coverage based on completed subjects.

**Request:** `GET /api/v1/users/skill-coverage?target_role=data_analyst`

**Response:**

```json
{
  "covered": ["python", "sql"],
  "in_progress": [],
  "missing": ["data_visualization", "statistics"]
}
```

### Adaptive Recommendation Endpoints

### 23. POST /api/v1/recommendations/adaptive

Get adaptive recommendations using collaborative filtering and Q-learning.

**Request:**

```json
{
  "target_role": "data_analyst",
  "use_collaborative": true,
  "use_rl": true,
  "top_k": 5
}
```

**Response:**

```json
{
  "recommendations": [
    {
      "subject_code": "CS401",
      "covered_skills": ["data_visualization"],
      "marginal_contribution": 0.8,
      "source": "MECE",
      "combined_score": 0.75
    }
  ],
  "algorithm": "Adaptive",
  "uses_collaborative": true,
  "uses_rl": true,
  "user_id": "uuid"
}
```

### 24. POST /api/v1/recommendations/feedback

Record user feedback for recommendations.

**Request:**

```json
{
  "subject_code": "CS401",
  "user_action": "accepted"
}
```

### 25. GET /api/v1/recommendations/sequence

Get optimized learning sequence for a role.

**Request:** `GET /api/v1/recommendations/sequence?target_role=frontend_developer`

## Available Roles

- `frontend_developer` - Frontend Developer
- `backend_developer` - Backend Developer
- `data_analyst` - Data Analyst
- `full_stack_developer` - Full Stack Developer
- `devops_engineer` - DevOps Engineer
- `data_scientist` - Data Scientist
- `ml_engineer` - Machine Learning Engineer
- `software_engineer` - Software Engineer

## Testing

You can test the API using:

1. **Swagger UI**: Visit http://localhost:8000/docs
2. **cURL**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/parse-curriculum" \
     -H "Content-Type: application/json" \
     -d '{"text": "Python Programming, SQL, Data Analysis"}'
   ```
3. **Python requests**:

   ```python
   import requests

   response = requests.post(
       "http://localhost:8000/api/v1/parse-curriculum",
       json={"text": "Python Programming, SQL, Data Analysis"}
   )
   print(response.json())
   ```

## Extension Points

The codebase is designed for easy extension:

1. **Database**: Add SQLAlchemy for persistent storage in `data_loader.py`
2. **Caching**: Add Redis for repeated role queries in `role_service.py`
3. **More LLMs**: Add support for additional providers in `app/providers/`
4. **Vector DB**: Already integrated with ChromaDB for semantic matching
5. **Authentication**: Add JWT-based authentication
6. **Embeddings**: Swap sentence-transformers model in `app/utils/embeddings/model.py`

## License

MIT License