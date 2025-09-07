import streamlit as st
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any
from agent import InterviewAgent, InterviewPhase
from evaluation import AnswerEvaluator, create_performance_report

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Excel Mock Interviewer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    default_values = {
        'agent': None,
        'evaluator': None,
        'interview_started': False,
        'interview_completed': False,
        'api_key_valid': False,
        'current_question_data': None,
        'awaiting_answer': False,
        'evaluation_results': [],
        'error_message': None
    }
    
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value

def setup_sidebar():
    with st.sidebar:
        st.header("🔧 Setup & Configuration")

        # API Key Configuration
        st.subheader("API Configuration")
        
        # Try to get Gemini API key from environment
        default_api_key = os.getenv("GOOGLE_API_KEY", "")
        
        api_key = st.text_input(
            "Google Gemini API Key", 
            value=default_api_key,
            type="password",
            help="Enter your Google Gemini API key for AI evaluation",
            placeholder="Enter your API key here..."
        )

        if api_key and not st.session_state.api_key_valid:
            with st.spinner("Validating API key..."):
                try:
                    # Initialize evaluator and agent
                    st.session_state.evaluator = AnswerEvaluator(api_key)
                    st.session_state.agent = InterviewAgent(api_key, st.session_state.evaluator)
                    st.session_state.api_key_valid = True
                    st.success("✅ API key configured successfully!")
                except Exception as e:
                    st.error(f"❌ API key validation failed: {str(e)}")
                    st.info("Please check your API key and try again")

        elif not api_key:
            st.info("👆 Enter your Gemini API key above to begin")

        st.divider()

        # Interview Status Panel
        if st.session_state.agent and hasattr(st.session_state.agent, 'state'):
            st.header("📋 Interview Status")
            state = st.session_state.agent.state
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Phase", state.current_phase.value.title().replace('_', ' '))
            with col2:
                st.metric("Progress", f"{state.question_count}/{state.max_questions}")

            # Progress bar
            if state.max_questions > 0:
                progress = min(state.question_count / state.max_questions, 1.0)
                st.progress(progress, text=f"Questions: {state.question_count}/{state.max_questions}")

            # Difficulty indicator
            if state.current_difficulty:
                difficulty_text = ["", "Beginner", "Basic", "Intermediate", "Advanced", "Expert"]
                st.info(f"Current Difficulty: {difficulty_text[state.current_difficulty]} ({state.current_difficulty}/5)")

        st.divider()

        # Interview Controls
        st.header("🎛️ Controls")
        
        if st.button("🔄 Reset Interview", type="secondary"):
            reset_interview()

        # API Key Instructions
        if not st.session_state.api_key_valid:
            st.divider()
            st.subheader("🔑 How to Get API Key")
            
            with st.expander("Instructions"):
                st.markdown("""
                1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
                2. Click "Create API Key"
                3. Copy the generated key
                4. Paste it in the input box above
                """)

def reset_interview():
    """Reset the interview session state"""
    for key in st.session_state.keys():
        if key not in ['api_key_valid', 'evaluator']:  # Keep API setup
            del st.session_state[key]
    initialize_session_state()
    st.success("Interview session has been reset.")
    st.rerun()

def display_question(question_data: Dict[str, Any]) -> None:
    """Display the current question"""
    st.subheader(f"Question {st.session_state.agent.state.question_count}")
    st.markdown(question_data["question_text"])
    
    # Show question metadata
    with st.expander("Question Details"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Skill Area:** {question_data.get('skill_area', 'General')}")
        with col2:
            st.info(f"**Type:** {question_data.get('question_type', 'text').title()}")
        with col3:
            st.info(f"**Difficulty:** {question_data.get('difficulty_level', 2)}/5")

def handle_text_answer() -> None:
    """Handle text-based answers"""
    user_answer = st.text_area(
        "Your Answer",
        height=150,
        placeholder="Type your detailed answer here...",
        key="answer_input"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Submit Answer", type="primary", disabled=not user_answer.strip()):
            if user_answer.strip():
                process_answer(user_answer)
            else:
                st.warning("Please enter an answer before submitting.")

def handle_file_upload() -> None:
    """Handle Excel file uploads"""
    st.info("📎 This question requires an Excel file upload.")
    
    uploaded_file = st.file_uploader(
        "Upload your Excel file here",
        type=["xlsx", "xls"],
        help="Upload an Excel file (.xlsx or .xls) that answers the question",
        key="file_upload"
    )
    
    if uploaded_file is not None:
        st.success(f"File uploaded: {uploaded_file.name}")
        
        if st.button("Submit Excel File", type="primary"):
            with st.spinner("Processing and evaluating your Excel file..."):
                try:
                    process_answer("", uploaded_file.read())
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")

def process_answer(answer: str, file_content: bytes = None) -> None:
    """Process user answer and get evaluation"""
    try:
        with st.spinner("Evaluating your response..."):
            # Process the response through the agent
            response = st.session_state.agent.process_response(answer, file_content)
            
            if "error" in response:
                st.error(f"Error processing response: {response['error']}")
                return
            
            # Display evaluation if available
            if "evaluation" in response and response["evaluation"]:
                display_evaluation(response["evaluation"])
            
            # Store the response for the next question or completion
            st.session_state.current_question_data = response.get("question")
            
            # Check if interview is completed
            if response.get("phase") == "completed":
                st.session_state.interview_completed = True
                st.success("🎉 Interview completed! Generating your performance report...")
                st.rerun()
            
            # Move to next question
            elif st.session_state.current_question_data:
                st.success("Answer submitted! Here's your next question:")
                st.rerun()
            
    except Exception as e:
        st.error(f"An error occurred while processing your answer: {str(e)}")
        st.info("Please try submitting your answer again.")

def display_evaluation(evaluation: Dict[str, Any]) -> None:
    """Display evaluation results"""
    if evaluation.get("error"):
        st.warning("⚠️ Evaluation encountered an issue. Please try again.")
        return
        
    st.success("✅ Your response has been evaluated!")
    
    # Score display
    score = evaluation.get("score", 0)
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("Score", f"{score}/10", delta=None)
    
    # Feedback
    if evaluation.get("feedback"):
        st.markdown("**Feedback:**")
        st.write(evaluation["feedback"])
    
    # Strengths and improvements
    col1, col2 = st.columns(2)
    
    with col1:
        if evaluation.get("strengths"):
            st.markdown("**Strengths:**")
            for strength in evaluation["strengths"]:
                st.write(f"✅ {strength}")
    
    with col2:
        if evaluation.get("improvements"):
            st.markdown("**Areas for Improvement:**")
            for improvement in evaluation["improvements"]:
                st.write(f"💡 {improvement}")

def display_interview_interface():
    """Main interview interface"""
    if not st.session_state.agent:
        st.error("Interview agent not initialized. Please check your API key.")
        return
    
    state = st.session_state.agent.state
    
    # Handle introduction phase
    if state.current_phase == InterviewPhase.INTRODUCTION:
        st.markdown("### Welcome to the Excel Mock Interview!")
        st.markdown("""
        I'll be conducting a comprehensive assessment of your Microsoft Excel skills today. 
        This interview will consist of 5-7 questions covering various Excel competencies.
        
        **What to expect:**
        - Mix of theoretical questions and practical Excel tasks
        - Some questions may require file uploads
        - Difficulty adapts based on your performance
        - Constructive feedback after each response
        """)
        
        name = st.text_input("Please enter your name to begin:", placeholder="Your full name")
        
        if st.button("Start Interview", type="primary", disabled=not name.strip()):
            if name.strip():
                response = st.session_state.agent.process_response(name.strip())
                st.session_state.current_question_data = response.get("question")
                st.success(f"Welcome, {name}! Let's begin your Excel interview.")
                st.rerun()
    
    # Handle questioning phase
    elif state.current_phase == InterviewPhase.QUESTIONING:
        # Display current question
        if st.session_state.current_question_data:
            display_question(st.session_state.current_question_data)
            
            # Handle answer input based on question type
            question_type = st.session_state.current_question_data.get("question_type", "text")
            
            if question_type == "excel_upload":
                handle_file_upload()
            else:
                handle_text_answer()
                
        else:
            st.info("Preparing your next question...")
    
    # Handle completion
    elif state.current_phase == InterviewPhase.COMPLETED:
        st.session_state.interview_completed = True

def generate_final_report():
    """Generate and display the final performance report"""
    st.header("📊 Interview Complete!")
    
    try:
        # Get interview summary from agent
        summary_data = st.session_state.agent.get_interview_summary()
        
        # Generate detailed report
        report_data = create_performance_report(summary_data)
        
        if report_data.get("error"):
            st.error(f"Error generating report: {report_data['error']}")
            return
        
        report = report_data["report"]
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Overall Score", f"{report['overall_score']}/10")
        with col2:
            st.metric("Performance Level", report['performance_level'])
        with col3:
            st.metric("Questions Completed", f"{report['questions_completed']}/{report['total_questions']}")
        with col4:
            st.metric("Skills Tested", len(report['skill_breakdown']))
        
        # Skill breakdown
        st.subheader("📈 Performance by Skill Area")
        
        for skill, data in report['skill_breakdown'].items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{skill}**")
                st.progress(data['average_score'] / 10)
            with col2:
                st.metric("", f"{data['average_score']}/10")
        
        # Detailed feedback
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Your Strengths")
            for strength in report['strengths'][:5]:  # Top 5
                st.write(f"✅ {strength}")
        
        with col2:
            st.subheader("🚀 Areas for Growth")
            for improvement in report['improvements'][:5]:  # Top 5
                st.write(f"💡 {improvement}")
        
        # Recommendations
        if report.get('recommendations'):
            st.subheader("📚 Learning Recommendations")
            for i, rec in enumerate(report['recommendations'], 1):
                st.write(f"{i}. {rec}")
        
        # Download report
        if st.button("📥 Download Detailed Report"):
            report_json = json.dumps(report, indent=2)
            st.download_button(
                label="Download Report as JSON",
                data=report_json,
                file_name=f"excel_interview_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
    except Exception as e:
        st.error(f"Error generating report: {str(e)}")

def main():
    """Main application function"""
    st.title("📊 Excel Mock Interviewer")
    st.markdown("""
    Welcome to the AI-powered Excel Mock Interviewer! This tool simulates a comprehensive 
    job interview focused on Microsoft Excel skills. Get personalized questions, instant 
    feedback, and a detailed performance report.
    """)

    initialize_session_state()
    setup_sidebar()

    # Error message display
    if st.session_state.error_message:
        st.error(st.session_state.error_message)
        st.session_state.error_message = None

    # Main flow control
    if not st.session_state.api_key_valid:
        st.info("🔑 Please enter a valid Google Gemini API key in the sidebar to start the interview.")
        return

    if not st.session_state.interview_started:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Excel Interview", type="primary", use_container_width=True):
                try:
                    st.session_state.agent.start_interview()
                    st.session_state.interview_started = True
                    st.success("Interview initialized! Let's begin...")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to start interview: {str(e)}")
        
        # Instructions
        with st.expander("📋 What to Expect"):
            st.markdown("""
            **Interview Structure:**
            - 5-7 questions covering different Excel skill areas
            - Mix of theoretical and practical questions
            - Some questions may require Excel file uploads
            - Adaptive difficulty based on your performance
            
            **Evaluation Criteria:**
            - Technical accuracy of your Excel knowledge
            - Practical application and examples
            - Clarity of communication
            - Completeness of your responses
            
            **Tips for Success:**
            - Provide detailed explanations
            - Use specific Excel terminology
            - Include practical examples when possible
            - Be clear and organized in your responses
            """)

    elif st.session_state.interview_started and not st.session_state.interview_completed:
        display_interview_interface()

    elif st.session_state.interview_completed:
        generate_final_report()

if __name__ == "__main__":
    main()
