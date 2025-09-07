# 📊 Excel Mock Interviewer

An AI-powered mock interview system for assessing Excel skills using Google's Gemini AI. This application provides an interactive interview experience with real-time evaluation, file upload capabilities, and comprehensive performance reporting.

## 🚀 Features

- **AI-Powered Interviews**: Dynamic question generation using Google Gemini AI
- **Multi-Format Support**: Text answers and Excel file uploads
- **Adaptive Difficulty**: Questions adjust based on performance
- **Real-Time Evaluation**: Instant feedback and scoring
- **Comprehensive Reports**: Detailed performance analysis
- **Interactive UI**: Streamlit-based web interface

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[Streamlit Web App]
    end
  
    subgraph "Core Components"
        B[Interview Agent]
        C[Answer Evaluator]
        D[Session State Manager]
    end
  
    subgraph "External Services"
        E[Google Gemini AI]
    end
  
    subgraph "Data Processing"
        F[Excel File Processor]
        G[Text Answer Parser]
        H[Report Generator]
    end
  
    A --> B
    A --> C
    A --> D
    B --> E
    C --> E
    C --> F
    C --> G
    C --> H
  
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#f3e5f5
    style E fill:#fff3e0
```

## 🔄 Interview Flow

```mermaid
flowchart TD
    A[Start Interview] --> B{API Key Valid?}
    B -->|No| C[Enter API Key]
    C --> B
    B -->|Yes| D[Initialize Session]
  
    D --> E[Introduction Phase]
    E --> F[Enter Candidate Name]
    F --> G[Begin Questioning]
  
    G --> H[Generate Question]
    H --> I{Question Type?}
    I -->|Text| J[Display Text Question]
    I -->|File| K[Display File Upload Question]
  
    J --> L[Submit Text Answer]
    K --> M[Upload Excel File]
  
    L --> N[Evaluate Answer]
    M --> N
  
    N --> O[Provide Feedback]
    O --> P{More Questions?}
    P -->|Yes| Q[Adjust Difficulty]
    Q --> H
    P -->|No| R[Generate Report]
    R --> S[Interview Complete]
  
    style A fill:#c8e6c9
    style S fill:#ffcdd2
    style N fill:#fff9c4
```

## 🧩 Component Interaction

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Streamlit UI
    participant A as Interview Agent
    participant E as Evaluator
    participant G as Gemini AI
  
    U->>UI: Start Interview
    UI->>A: Initialize Agent
    A->>G: Generate Introduction
    G->>A: Return Greeting
    A->>UI: Display Introduction
  
    loop For Each Question
        A->>G: Generate Question
        G->>A: Return Question Data
        A->>UI: Display Question
        U->>UI: Submit Answer
        UI->>E: Evaluate Answer
        E->>G: Analyze Response
        G->>E: Return Evaluation
        E->>UI: Display Feedback
        UI->>A: Update Progress
    end
  
    A->>E: Generate Final Report
    E->>UI: Display Results
```

## 📊 Evaluation System

```mermaid
graph LR
    subgraph "Input Types"
        A[Text Answer]
        B[Excel File]
    end
  
    subgraph "Evaluation Criteria"
        C[Technical Accuracy - 35%]
        D[Practical Application - 25%]
        E[Clarity & Communication - 25%]
        F[Completeness - 15%]
    end
  
    subgraph "Excel-Specific Criteria"
        G[Formula Correctness - 40%]
        H[Data Structure - 25%]
        I[Functionality - 20%]
        J[Best Practices - 15%]
    end
  
    subgraph "Output"
        K[Numerical Score 0-10]
        L[Detailed Feedback]
        M[Strengths List]
        N[Improvement Areas]
    end
  
    A --> C & D & E & F
    B --> G & H & I & J
    C & D & E & F --> K & L & M & N
    G & H & I & J --> K & L & M & N
  
    style A fill:#e3f2fd
    style B fill:#e8f5e8
    style K fill:#fff3e0
```

## 🛠️ Installation

### Prerequisites

- Python 3.12 or higher
- Google Gemini API key
- UV package manager (recommended) or pip

### Quick Start

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd coding-ninja
   ```
2. **Install dependencies**

   ```bash
   uv sync
   ```
3. **Set up environment variables**

   ```bash
   # Create .env file
   echo "GOOGLE_API_KEY=your_gemini_api_key_here" > .env
   ```
4. **Run the application**

   ```bash
   # Using UV
   uv run streamlit run app.py

   # Or using Python directly
   streamlit run app.py
   ```

## 🔧 Configuration

### Environment Variables

| Variable           | Description           | Required |
| ------------------ | --------------------- | -------- |
| `GOOGLE_API_KEY` | Google Gemini API key | Yes      |

### Interview Settings

The interview can be customized through the sidebar:

- **Number of Questions**: 3-10 questions
- **Starting Difficulty**: Easy (1) to Expert (5)
- **Question Types**: Text-only or Mixed (text + file uploads)

## 📁 Project Structure

```
coding-ninja/
├── app.py              # Main Streamlit application
├── agent.py            # Interview agent and question generation
├── evaluation.py       # Answer evaluation and scoring system
├── pyproject.toml      # Project configuration and dependencies
├── README.md           # This file
└── .env               # Environment variables (create this)
```

## 🎯 Usage Examples

### Basic Interview Flow

1. **Start**: Enter your Gemini API key in the sidebar
2. **Configure**: Set interview parameters (questions, difficulty)
3. **Begin**: Click "Start Interview" and enter your name
4. **Answer**: Respond to questions via text or file upload
5. **Review**: Get instant feedback after each answer
6. **Complete**: Receive comprehensive performance report

### Question Types

**Text Questions**: Conceptual questions about Excel features

- Example: "Explain the difference between VLOOKUP and INDEX-MATCH"

**File Upload Questions**: Practical Excel tasks

- Example: "Create a pivot table from the provided dataset"

## 📈 Performance Metrics

The system tracks multiple performance indicators:

```mermaid
pie title Performance Breakdown
    "Technical Accuracy" : 35
    "Practical Application" : 25
    "Communication" : 25
    "Completeness" : 15
```

### Scoring Scale

- **9-10**: Expert level performance
- **7-8**: Advanced proficiency
- **5-6**: Intermediate level
- **3-4**: Beginner level
- **0-2**: Needs significant improvement

## 🔗 Dependencies

- **streamlit**: Web application framework
- **langchain-google-genai**: Google Gemini AI integration
- **pandas**: Data manipulation and analysis
- **openpyxl**: Excel file processing
- **python-dotenv**: Environment variable management

## 🚨 Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your Gemini API key is valid and has sufficient quota
2. **File Upload Issues**: Check file size limits and Excel format compatibility
3. **Session State Problems**: Clear browser cache or restart the application

### Error Messages

```mermaid
graph TD
    A[Error Occurred] --> B{Error Type?}
    B -->|API| C[Check API Key & Quota]
    B -->|File| D[Verify Excel Format]
    B -->|Session| E[Clear Cache/Restart]
    B -->|Network| F[Check Internet Connection]
  
    C --> G[Retry Operation]
    D --> G
    E --> G
    F --> G
  
    style A fill:#ffcdd2
    style G fill:#c8e6c9
```
