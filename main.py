from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from agents.sales_call_agent import sales_call_agent

from docx import Document
import fitz
import tempfile
import os


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


previous_stage = None
conversation_window = []
checklist_status_by_stage = {}


class AnalyzeRequest(BaseModel):
    speaker: str
    transcript: str


@app.get("/")
def home():
    return FileResponse("index.html")


@app.post("/analyze")
def analyze_conversation(request: AnalyzeRequest):
    global previous_stage
    global conversation_window
    global checklist_status_by_stage

    result = sales_call_agent(
        transcript=request.transcript,
        speaker=request.speaker.lower(),
        previous_stage=previous_stage,
        checklist_status_by_stage=checklist_status_by_stage,
        conversation_window=conversation_window
    )

    previous_stage = result["active_stage"]
    checklist_status_by_stage = result["checklist_status_by_stage"]
    conversation_window = result["conversation_window"]

    return result


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global previous_stage
    global conversation_window
    global checklist_status_by_stage

    suffix = os.path.splitext(file.filename)[1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        if suffix == ".pdf":
            text = extract_text_from_pdf(temp_path)

        elif suffix == ".docx":
            text = extract_text_from_docx(temp_path)

        elif suffix == ".txt":
            text = extract_text_from_txt(temp_path)

        else:
            return {
                "error": "Only PDF, DOCX, and TXT files are supported"
            }

        turns = split_transcript_into_turns(text)

        if not turns:
            return {
                "error": "Could not detect Advisor: or Customer: lines in uploaded file"
            }

        turn_results = []

        for index, turn in enumerate(turns[:6], start=1):
                result = sales_call_agent(
                    transcript=turn["text"],
                    speaker=turn["speaker"],
                    previous_stage=previous_stage,
                    checklist_status_by_stage=checklist_status_by_stage,
                    conversation_window=conversation_window
                )

                previous_stage = result["active_stage"]
                checklist_status_by_stage = result["checklist_status_by_stage"]
                conversation_window = result["conversation_window"]
                

                turn_results.append({
                    "turn_number": index,
                    "speaker": turn["speaker"],
                    "transcript": turn["text"],
                    "result": result
                })

        print(turn_results)
        return {
                "total_turns_detected": len(turns),
                "processed_turns": len(turn_results),
                "turn_results": turn_results,
                "final_result": turn_results[-1]["result"] if turn_results else None
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/reset")
def reset_conversation():
    global previous_stage
    global conversation_window
    global checklist_status_by_stage

    previous_stage = None
    conversation_window = []
    checklist_status_by_stage = {}

    return {"message": "Conversation reset successfully"}


def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""

    for page in doc:
        text += page.get_text() + "\n"

    doc.close()
    return text


def extract_text_from_docx(file_path):
    doc = Document(file_path)
    lines = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)

    return "\n".join(lines)


def extract_text_from_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def split_transcript_into_turns(text):
    turns = []
    lines = text.split("\n")

    current_speaker = None

    speaker_map = {
        "speaker 1": "customer",
        "speaker 2": "advisor"
    }

    for line in lines:
        line = line.strip().replace("\xa0", " ")

        if not line:
            continue

        lower_line = line.lower().strip()

        # Detect Speaker 1 / Speaker 2
        if lower_line.startswith("speaker 1"):
            current_speaker = "customer"
            continue

        if lower_line.startswith("speaker 2"):
            current_speaker = "advisor"
            continue

        # Detect Advisor: / Customer:
        if lower_line.startswith("advisor:"):
            turns.append({
                "speaker": "advisor",
                "text": line.split(":", 1)[1].strip()
            })
            continue

        if lower_line.startswith("customer:"):
            turns.append({
                "speaker": "customer",
                "text": line.split(":", 1)[1].strip()
            })
            continue

        # Skip timestamp lines like 0:00 - 0:01
        if "-" in line and ":" in line and any(ch.isdigit() for ch in line):
            continue

        # Add actual dialogue line
        if current_speaker and len(line) > 1:
            turns.append({
                "speaker": current_speaker,
                "text": line
            })

    return turns