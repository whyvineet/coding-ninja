from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from datetime import datetime
import logging


class InterviewPhase(Enum):
    """Interview phases"""
    INTRODUCTION = "introduction"
    QUESTIONING = "questioning" 
    WRAP_UP = "wrap_up"
    COMPLETED = "completed"


@dataclass
class QuestionHistory:
    """Individual question record"""
    question_id: int
    question_text: str
    question_type: str
    difficulty_level: int
    skill_area: str = "General Excel"
    answer: Optional[str] = None
    file_upload: Optional[Any] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    strengths: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    timestamp: Optional[datetime] = field(default_factory=datetime.now)


@dataclass
class InterviewState:
    """Complete interview state"""
    candidate_name: Optional[str] = None
    current_phase: InterviewPhase = InterviewPhase.INTRODUCTION
    question_count: int = 0
    max_questions: int = 5
    current_difficulty: int = 2
    question_history: List[QuestionHistory] = field(default_factory=list)
    overall_score: Optional[float] = None
    session_id: str = field(default_factory=lambda: f"interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}")


class InterviewAgent:
    def __init__(self, gemini_api_key: str, evaluator=None):
        """Initialize the interview agent with Gemini API key and optional evaluator"""
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=gemini_api_key, temperature=0.3)
        self.evaluator = evaluator
        self.state = InterviewState()
        
        # Excel skill areas for question generation
        self.skill_areas = [
            "Basic Functions (SUM, AVERAGE, COUNT)",
            "Lookup Functions (VLOOKUP, INDEX/MATCH)", 
            "Pivot Tables and Data Analysis",
            "Data Validation and Conditional Formatting",
            "Advanced Formulas and Array Functions",
            "Charts and Visualization",
            "Data Cleaning and Transformation"
        ]
        
        # Track which skills have been tested
        self.tested_skills = set()
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def start_interview(self) -> Dict[str, Any]:
        """Initialize the interview and return introduction message"""
        self.state = InterviewState()
        self.state.current_phase = InterviewPhase.INTRODUCTION
        
        introduction_msg = """Hello! I'm your AI Excel Interview Assistant.

            I'll be conducting a comprehensive assessment of your Microsoft Excel skills today. This interview will consist of 5-7 questions covering various Excel competencies, from basic functions to advanced data analysis.

            Here's what to expect:
            • Mix of theoretical questions and practical Excel tasks
            • Some questions may require file uploads with your Excel solutions
            • Difficulty will adapt based on your performance
            • You'll receive constructive feedback after each response
            • Total interview time: approximately 15-20 minutes

            Are you ready to begin? Please tell me your name and we'll get started!
        """

        return {
            "phase": self.state.current_phase.value,
            "message": introduction_msg,
            "question_id": None,
            "next_action": "await_name"
        }
    
    def process_response(self, user_input: str, uploaded_file: Optional[Any] = None) -> Dict[str, Any]:
        try:
            if self.state.current_phase == InterviewPhase.INTRODUCTION:
                return self._handle_introduction(user_input)
            
            elif self.state.current_phase == InterviewPhase.QUESTIONING:
                return self._handle_questioning_phase(user_input, uploaded_file)
            
            elif self.state.current_phase == InterviewPhase.WRAP_UP:
                return self._handle_wrap_up()
            
            else:
                return {"error": "Invalid interview phase"}
                
        except Exception as e:
            self.logger.error(f"Error processing response: {str(e)}")
            return {
                "error": f"An error occurred: {str(e)}",
                "phase": self.state.current_phase.value
            }
    
    def _handle_introduction(self, user_input: str) -> Dict[str, Any]:
        # Extract name from user input
        self.state.candidate_name = user_input.strip()
        self.state.current_phase = InterviewPhase.QUESTIONING
        
        # Generate first question
        first_question = self._generate_next_question()
        
        return {
            "phase": self.state.current_phase.value,
            "message": f"Great to meet you, {self.state.candidate_name}! Let's begin with your first question.",
            "question": first_question,
            "question_id": self.state.question_count,
            "progress": f"Question {self.state.question_count} of {self.state.max_questions}",
            "next_action": "await_answer"
        }
    
    def _handle_questioning_phase(self, user_input: str, uploaded_file: Optional[Any]) -> Dict[str, Any]:
        
        # Get current question
        current_question = self.state.question_history[-1] if self.state.question_history else None
        evaluation_result = None
        
        if current_question:
            # Store the answer
            current_question.answer = user_input
            current_question.file_upload = uploaded_file
            
            # Evaluate the response
            evaluation_result = self._evaluate_response(user_input, uploaded_file, current_question)
            
            # Store evaluation results
            current_question.score = evaluation_result["score"]
            current_question.feedback = evaluation_result["feedback"]
            current_question.strengths = evaluation_result.get("strengths", [])
            current_question.improvements = evaluation_result.get("improvements", [])
            
            # Adapt difficulty based on performance
            self._adapt_difficulty(evaluation_result["score"])
        
        # Check if interview should continue
        if self.state.question_count >= self.state.max_questions:
            self.state.current_phase = InterviewPhase.WRAP_UP
            return self._handle_wrap_up()
        
        # Generate next question
        next_question = self._generate_next_question()
        
        return {
            "phase": self.state.current_phase.value,
            "evaluation": evaluation_result,
            "question": next_question,
            "question_id": self.state.question_count,
            "progress": f"Question {self.state.question_count} of {self.state.max_questions}",
            "next_action": "await_answer"
        }
    
    def _evaluate_response(self, user_input: str, uploaded_file: Optional[Any], question: QuestionHistory) -> Dict[str, Any]:
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if self.evaluator:
                    if uploaded_file:
                        # Excel file evaluation
                        eval_result = self.evaluator.evaluate_excel_upload(
                            uploaded_file, question.question_text
                        )
                        return {
                            "score": eval_result.score,
                            "feedback": eval_result.feedback,
                            "strengths": eval_result.strengths,
                            "improvements": eval_result.improvements,
                            "category_scores": getattr(eval_result, 'category_scores', {})
                        }
                    else:
                        # Text answer evaluation
                        question_data = {
                            "question_text": question.question_text,
                            "question_type": question.question_type,
                            "difficulty_level": question.difficulty_level,
                            "expected_answer_format": "Text explanation",
                            "evaluation_criteria": "Excel knowledge and communication",
                            "skill_area": question.skill_area
                        }
                        eval_result = self.evaluator.evaluate_text_answer(user_input, question_data)
                        return {
                            "score": eval_result.score,
                            "feedback": eval_result.feedback,
                            "strengths": eval_result.strengths,
                            "improvements": eval_result.improvements,
                            "category_scores": getattr(eval_result, 'category_scores', {})
                        }
                else:
                    raise ValueError("Evaluator not initialized")
                    
            except Exception as e:
                self.logger.warning(f"Evaluation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    # Final attempt failed, return error response
                    return {
                        "score": 0.0,
                        "feedback": f"Unable to evaluate response after {max_retries} attempts. Please try again.",
                        "strengths": [],
                        "improvements": ["Please resubmit your response"],
                        "category_scores": {},
                        "error": True
                    }
                # Wait before retrying
                import time
                time.sleep(1 * (attempt + 1))
    
    def _generate_next_question(self) -> Dict[str, Any]:
        self.state.question_count += 1
        
        # Choose skill area that hasn't been tested yet
        available_skills = [skill for skill in self.skill_areas if skill not in self.tested_skills]
        if not available_skills:
            available_skills = self.skill_areas  # Reset if all tested
        
        # Build context for LLM
        context = self._build_question_context()
        
        prompt = f"""You are an expert Excel interviewer. Generate the next interview question based on:

            CONTEXT:
            {context}

            REQUIREMENTS:
            - Current difficulty level: {self.state.current_difficulty}/5 (1=Beginner, 5=Expert)
            - Question number: {self.state.question_count} of {self.state.max_questions}
            - Focus on practical Excel skills assessment
            - Choose from available skill areas: {', '.join(available_skills[:3])}
            - Question types: "text" (explanation), "excel_upload" (file required), "scenario" (case study)

            DIFFICULTY GUIDELINES:
            Level 1-2: Basic functions, simple formulas, cell references
            Level 3: Intermediate functions, pivot tables, basic charts
            Level 4-5: Advanced formulas, complex analysis, automation

            CRITICAL: You MUST return valid JSON with ALL required fields:
            {{{{
                "question_text": "The actual question to ask the candidate (required)",
                "question_type": "text|excel_upload|scenario (required)",
                "difficulty_level": {self.state.current_difficulty},
                "skill_area": "Choose from the available skill areas above (required)",
                "expected_answer_format": "What kind of response is expected",
                "evaluation_criteria": "Key points to evaluate in the response"
            }}}}

            Make the question challenging but fair for the difficulty level. Be specific and practical.
            ENSURE the JSON is valid and complete.
        """

        max_retries = 3
        for attempt in range(max_retries):
            try:
                prompt_template = ChatPromptTemplate.from_template(prompt)
                parser = JsonOutputParser()
                chain = prompt_template | self.llm | parser
                question_data = chain.invoke({})
                
                # Robust validation
                required_fields = ["question_text", "question_type", "skill_area"]
                missing_fields = [field for field in required_fields if field not in question_data or not question_data[field]]
                
                if missing_fields:
                    raise ValueError(f"Missing required fields: {missing_fields}")
                
                # Validate question_type
                valid_types = ["text", "excel_upload", "scenario"]
                if question_data["question_type"] not in valid_types:
                    question_data["question_type"] = "text"  # Default to text
                
                # Ensure skill_area is from available skills
                if question_data["skill_area"] not in available_skills:
                    question_data["skill_area"] = available_skills[0]
                
                # Set defaults for optional fields
                question_data.setdefault("difficulty_level", self.state.current_difficulty)
                question_data.setdefault("expected_answer_format", "Detailed explanation")
                question_data.setdefault("evaluation_criteria", "Knowledge accuracy and communication clarity")
                
                # Create question history entry
                question_history = QuestionHistory(
                    question_id=self.state.question_count,
                    question_text=question_data["question_text"],
                    question_type=question_data["question_type"],
                    difficulty_level=question_data.get("difficulty_level", self.state.current_difficulty),
                    skill_area=question_data["skill_area"]
                )
                
                self.state.question_history.append(question_history)
                self.tested_skills.add(question_data["skill_area"])
                
                self.logger.info(f"Successfully generated question {self.state.question_count}")
                return question_data
                
            except Exception as e:
                self.logger.warning(f"Question generation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    # Final attempt failed - create a basic but valid question
                    skill_area = available_skills[0] if available_skills else "Basic Functions (SUM, AVERAGE, COUNT)"
                    
                    basic_question = {
                        "question_text": "Explain how to use basic Excel functions for data analysis. Specifically, describe when and how you would use SUM, AVERAGE, and COUNT functions in a real-world scenario.",
                        "question_type": "text",
                        "difficulty_level": max(1, min(3, self.state.current_difficulty)),
                        "skill_area": skill_area,
                        "expected_answer_format": "Detailed explanation with examples",
                        "evaluation_criteria": "Understanding of basic functions and practical application"
                    }
                    
                    question_history = QuestionHistory(
                        question_id=self.state.question_count,
                        question_text=basic_question["question_text"],
                        question_type=basic_question["question_type"],
                        difficulty_level=basic_question["difficulty_level"],
                        skill_area=basic_question["skill_area"]
                    )
                    
                    self.state.question_history.append(question_history)
                    self.tested_skills.add(skill_area)
                    
                    self.logger.info("Used basic question after generation failures")
                    return basic_question
                
                # Wait before retrying
                import time
                time.sleep(1 * (attempt + 1))
    
    def _build_question_context(self) -> str:
        context_parts = []
        
        context_parts.append(f"Candidate: {self.state.candidate_name}")
        context_parts.append(f"Questions asked so far: {len(self.state.question_history)}")
        
        if self.state.question_history:
            context_parts.append("Recent performance:")
            for q in self.state.question_history[-2:]:
                if q.score:
                    context_parts.append(f"- Q{q.question_id}: {q.skill_area} (Score: {q.score:.1f}/10)")
        
        context_parts.append(f"Skills already tested: {', '.join(self.tested_skills)}")
        context_parts.append(f"Available skill areas: {', '.join([s for s in self.skill_areas if s not in self.tested_skills])}")
        
        return "\n".join(context_parts)
    
    def _adapt_difficulty(self, last_score: float):
        if last_score >= 8.5:
            self.state.current_difficulty = min(5, self.state.current_difficulty + 1)
            self.logger.info(f"Difficulty increased to {self.state.current_difficulty}")
        elif last_score <= 4.0:
            self.state.current_difficulty = max(1, self.state.current_difficulty - 1)
            self.logger.info(f"Difficulty decreased to {self.state.current_difficulty}")
    
    def _handle_wrap_up(self) -> Dict[str, Any]:
        self.state.current_phase = InterviewPhase.COMPLETED
        
        # Calculate overall score
        scores = [q.score for q in self.state.question_history if q.score is not None]
        self.state.overall_score = sum(scores) / len(scores) if scores else 0
        
        summary = f"""
            Thank you for completing the Excel interview, {self.state.candidate_name}!

            **Interview Summary:**
            - Questions completed: {len(self.state.question_history)}
            - Overall score: {self.state.overall_score:.1f}/10
            - Performance level: {self._get_performance_level(self.state.overall_score)}
            - Session ID: {self.state.session_id}

            Your detailed performance report is ready for review.
        """

        return {
            "phase": self.state.current_phase.value,
            "message": summary,
            "overall_score": self.state.overall_score,
            "next_action": "show_report"
        }
    
    def _get_performance_level(self, score: float) -> str:
        if score >= 8.5:
            return "Excellent"
        elif score >= 7.0:
            return "Good"
        elif score >= 5.0:
            return "Average"
        else:
            return "Needs Improvement"
    
    def get_interview_summary(self) -> Dict[str, Any]:
        return {
            "session_id": self.state.session_id,
            "candidate_name": self.state.candidate_name,
            "overall_score": self.state.overall_score,
            "performance_level": self._get_performance_level(self.state.overall_score or 0),
            "questions_completed": len(self.state.question_history),
            "question_history": [
                {
                    "question_id": q.question_id,
                    "question_text": q.question_text,
                    "question_type": q.question_type,
                    "difficulty_level": q.difficulty_level,
                    "skill_area": q.skill_area,
                    "score": q.score,
                    "feedback": q.feedback,
                    "strengths": q.strengths,
                    "improvements": q.improvements
                }
                for q in self.state.question_history
            ],
            "timestamp": datetime.now().isoformat(),
            "skills_tested": list(self.tested_skills)
        }