import sqlite3
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from database import init_db, list_feedback, save_feedback

load_dotenv()
client = genai.Client()
init_db()

app = FastAPI(title="Project Feedback Analyzer")


class Review(BaseModel):
    text: str = Field(min_length=1, description="The review text to analyze")


class Analysis(BaseModel):
    label: Literal["positive", "negative", "neutral"]
    score: int = Field(ge=1, le=5)
    theme: str


class FeedbackRecord(Analysis):
    id: int
    text: str
    created_at: str


@app.post("/analyze", response_model=Analysis)
def analyze(review: Review) -> Analysis:
    
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=(
                "Analyze this customer review.\n"
                "Label must be 'positive', 'negative', or 'neutral'.\n"
                "score must be a number from 1 (very bad) to 5 (very good).\n"
                "theme must be ONE lowercase word for the main topic "
                "(for example: delivery, taste, price, service, quality).\n"
                f"Review: {review.text}"
            ),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Analysis,
            ),
        )
        return response.parsed