from typing import Dict, List
from enum import Enum


class FlashcardStyle(Enum):
    BASIC = "basic"
    CLOZE = "cloze"
    CONCEPT = "concept"


class PromptTemplates:
    """Centralized prompt templates for different AI tasks"""
    
    # Flashcard Generation Prompts
    FLASHCARD_GENERATION = """
Anda adalah seorang ahli dalam membuat flashcard untuk pembelajaran Active Recall. 
Buatlah flashcard yang efektif berdasarkan konten yang diberikan.

INSTRUKSI:
1. Buat {n_cards} flashcard berkualitas tinggi
2. Setiap flashcard harus fokus pada satu konsep atau fakta
3. Pertanyaan harus jelas dan spesifik
4. Jawaban harus akurat dan informatif
5. Gunakan gaya {style} sesuai permintaan
6. Tentukan tingkat kesulitan yang sesuai (easy/medium/hard)
7. Berikan tag yang relevan untuk setiap kartu

KONTEN:
{context}

FORMAT OUTPUT (JSON array):
[
  {{
    "question": "Pertanyaan yang jelas dan spesifik",
    "answer": "Jawaban yang akurat dan informatif",
    "difficulty": "easy|medium|hard",
    "tags": ["tag1", "tag2", "tag3"]
  }}
]

STYLE GUIDELINES:
- BASIC: Pertanyaan dan jawaban langsung
- CLOZE: Pertanyaan dengan bagian yang dihilangkan, jawaban melengkapi bagian kosong
- CONCEPT: Pertanyaan konseptual yang memerlukan pemahaman mendalam

Pastikan output adalah JSON yang valid dan dapat di-parse.
"""

    # Quiz Grading Prompt
    QUIZ_GRADING = """
Anda adalah seorang guru yang ahli dalam mengevaluasi jawaban siswa. 
Evaluasi jawaban siswa berdasarkan pertanyaan dan jawaban ideal yang diberikan.

PERTANYAAN: {question}
JAWABAN IDEAL: {ideal_answer}
JAWABAN SISWA: {user_answer}
KONTEKS: {context}

INSTRUKSI EVALUASI:
1. Berikan skor 0.0 - 1.0 (0.0 = salah total, 1.0 = benar sempurna)
2. Tentukan verdict: "correct", "partial", atau "incorrect"
3. Berikan feedback yang konstruktif dan membantu
4. Sertakan jawaban ideal yang lebih baik jika perlu

KRITERIA PENILAIAN:
- Correct (0.8-1.0): Jawaban benar atau hampir benar dengan detail yang tepat
- Partial (0.4-0.7): Jawaban sebagian benar atau ada konsep yang tepat tapi kurang detail
- Incorrect (0.0-0.3): Jawaban salah atau tidak relevan

FORMAT OUTPUT (JSON):
{{
  "score": 0.85,
  "verdict": "correct|partial|incorrect",
  "feedback": "Feedback yang konstruktif dan membantu",
  "ideal_answer": "Jawaban ideal yang lebih baik jika diperlukan"
}}

Pastikan output adalah JSON yang valid.
"""

    # Socratic Follow-up Prompt
    SOCRATIC_FOLLOWUP = """
Anda adalah seorang guru yang menggunakan metode Socratic untuk membantu siswa belajar.
Berdasarkan jawaban siswa yang {verdict}, berikan satu pertanyaan atau petunjuk yang akan membantu mereka memahami konsep dengan lebih baik.

PERTANYAAN ASLI: {question}
JAWABAN SISWA: {user_answer}
FEEDBACK SEBELUMNYA: {feedback}

INSTRUKSI:
1. Berikan satu pertanyaan atau petunjuk yang membimbing
2. Fokus pada pemahaman konsep, bukan hafalan
3. Gunakan pertanyaan terbuka yang mendorong pemikiran
4. Sesuaikan dengan tingkat kesulitan yang tepat
5. Hindari memberikan jawaban langsung

FORMAT OUTPUT (JSON):
{{
  "socratic_question": "Pertanyaan atau petunjuk yang membimbing",
  "hint_type": "conceptual|analytical|practical|comparative"
}}

Pastikan output adalah JSON yang valid.
"""

    # Content Analysis Prompt
    CONTENT_ANALYSIS = """
Analisis konten berikut dan berikan ringkasan yang berguna untuk pembelajaran.

KONTEN:
{content}

INSTRUKSI:
1. Identifikasi topik utama dan subtopik
2. Tentukan tingkat kesulitan konten
3. Identifikasi konsep kunci yang perlu dipahami
4. Berikan saran untuk pembelajaran yang efektif

FORMAT OUTPUT (JSON):
{{
  "main_topics": ["topik1", "topik2", "topik3"],
  "key_concepts": ["konsep1", "konsep2", "konsep3"],
  "difficulty_level": "beginner|intermediate|advanced",
  "learning_suggestions": ["saran1", "saran2", "saran3"],
  "estimated_study_time": "X menit"
}}

Pastikan output adalah JSON yang valid.
"""

    # Quiz Question Generation Prompt
    QUIZ_QUESTION_GENERATION = """
Berdasarkan konten yang diberikan, buatlah pertanyaan kuis yang bervariasi dan menantang.

KONTEN:
{context}

INSTRUKSI:
1. Buat {count} pertanyaan kuis
2. Variasikan jenis pertanyaan (pemahaman, analisis, aplikasi)
3. Pastikan pertanyaan sesuai dengan konten
4. Berikan jawaban yang benar dan jelas
5. Tentukan tingkat kesulitan yang sesuai

JENIS PERTANYAAN:
- Pemahaman: "Apa yang dimaksud dengan...?"
- Analisis: "Mengapa...?" atau "Bagaimana...?"
- Aplikasi: "Bagaimana cara menerapkan...?"
- Evaluasi: "Apa kelebihan dan kekurangan...?"

FORMAT OUTPUT (JSON array):
[
  {{
    "question": "Pertanyaan yang jelas dan menantang",
    "correct_answer": "Jawaban yang benar dan lengkap",
    "difficulty": "easy|medium|hard",
    "question_type": "understanding|analysis|application|evaluation"
  }}
]

Pastikan output adalah JSON yang valid.
"""


class PromptBuilder:
    """Helper class to build prompts with dynamic content"""
    
    @staticmethod
    def build_flashcard_prompt(context: str, n_cards: int = 5, style: FlashcardStyle = FlashcardStyle.BASIC) -> str:
        """Build flashcard generation prompt"""
        return PromptTemplates.FLASHCARD_GENERATION.format(
            context=context,
            n_cards=n_cards,
            style=style.value
        )
    
    @staticmethod
    def build_grading_prompt(question: str, ideal_answer: str, user_answer: str, context: str = "") -> str:
        """Build quiz grading prompt"""
        return PromptTemplates.QUIZ_GRADING.format(
            question=question,
            ideal_answer=ideal_answer,
            user_answer=user_answer,
            context=context
        )
    
    @staticmethod
    def build_socratic_prompt(question: str, user_answer: str, feedback: str, verdict: str) -> str:
        """Build Socratic follow-up prompt"""
        return PromptTemplates.SOCRATIC_FOLLOWUP.format(
            question=question,
            user_answer=user_answer,
            feedback=feedback,
            verdict=verdict
        )
    
    @staticmethod
    def build_content_analysis_prompt(content: str) -> str:
        """Build content analysis prompt"""
        return PromptTemplates.CONTENT_ANALYSIS.format(content=content)
    
    @staticmethod
    def build_quiz_question_prompt(context: str, count: int = 10) -> str:
        """Build quiz question generation prompt"""
        return PromptTemplates.QUIZ_QUESTION_GENERATION.format(
            context=context,
            count=count
        )


# Example usage and validation
def validate_prompt_output(prompt_type: str, output: str) -> bool:
    """Validate that prompt output is properly formatted JSON"""
    try:
        import json
        data = json.loads(output)
        
        if prompt_type == "flashcard":
            return isinstance(data, list) and all(
                "question" in item and "answer" in item and "difficulty" in item
                for item in data
            )
        elif prompt_type == "grading":
            return all(
                key in data for key in ["score", "verdict", "feedback"]
            )
        elif prompt_type == "socratic":
            return all(
                key in data for key in ["socratic_question", "hint_type"]
            )
        elif prompt_type == "analysis":
            return all(
                key in data for key in ["main_topics", "key_concepts", "difficulty_level"]
            )
        elif prompt_type == "quiz":
            return isinstance(data, list) and all(
                "question" in item and "correct_answer" in item
                for item in data
            )
        
        return False
        
    except json.JSONDecodeError:
        return False
