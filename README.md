# Self-Healing Code Reviewer

An AI-powered code generation and review system built using **LangGraph, LangChain, Streamlit, and Groq**. The application generates code from natural-language problem statements, reviews it using an LLM, and iteratively attempts to correct issues based on reviewer feedback.

## 🚀 Features

- **AI Code Generation:** Generates code from natural-language problem statements.
- **Automated Code Review:** Evaluates code for correctness, edge cases, memory management, and performance.
- **Self-Healing Workflow:** Iteratively regenerates code based on reviewer feedback.
- **Multi-Language Support:** Supports Python, C++, Java, Go, and JavaScript.
- **Python Syntax Validation:** Uses Python's AST parser to detect syntax errors in generated Python code.
- **Dynamic Model Selection:** Discovers available Groq models and selects a supported model.
- **Configurable Generation Attempts:** Lets users configure the maximum number of generation attempts.
- **Interactive Web Interface:** Displays generation progress, review decisions, and final results.
- **Downloadable Reports:** Exports the final code, review status, iteration count, and feedback as a text file.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Interactive web interface |
| LangGraph | Workflow orchestration |
| LangChain | LLM integration and message handling |
| Groq API | AI inference |
| Python AST | Python syntax validation |
| python-dotenv | Environment variable management |

## ⚙️ How It Works

1. **Task Input:** The user enters a coding problem and selects a target language.
2. **Code Generation:** The generator node produces code using a Groq-hosted language model.
3. **Validation:** Python code is checked for syntax errors using AST parsing. An LLM reviews the code for potential correctness and quality issues.
4. **Feedback:** If the reviewer identifies problems, it provides feedback to the generator.
5. **Iteration:** LangGraph repeats the generation and review cycle until the code is approved or the configured attempt limit is reached.
6. **Results:** The application displays the final code, review status, iteration count, and downloadable report.

## 📋 Prerequisites

- Python 3.10 or later
- A Groq API key
- Internet connectivity

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/Kumar-Suryansh/Self-Healing-Code-Reviewer.git
cd Self-Healing-Code-Reviewer
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 🔑 Configuration

The application accepts a Groq API key through the sidebar or a local `.env` file.

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Replace the placeholder with your actual API key.

**Security note:** Never commit your real `.env` file or expose your API key in a public repository.

## ▶️ Run the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

Open the local URL shown in your terminal, usually `http://localhost:8501`.

Enter a coding task, select the target language, choose the maximum generation attempts, and click **Generate & Review Code**.

## 📁 Project Structure

```text
Self-Healing-Code-Reviewer/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

This is the intended structure; your actual files and folders may differ.

## ⚠️ Limitations

- LLM approval does not guarantee that generated code is correct or secure.
- Python receives AST-based syntax validation; the other supported languages do not receive equivalent compiler-based syntax checks in the current implementation.
- Generated code is not executed, and unit tests are not automatically run.
- Model availability, API errors, and prompt quality can affect results.
- Generated code should be reviewed and tested before production use.

## 🔮 Future Improvements

- Integrate language-specific compilers, parsers, and linters.
- Add automated unit-test generation and execution in a secure sandbox.
- Introduce structured review reports with severity levels.
- Maintain review history and code quality metrics.
- Improve error handling and model selection.

## 🔒 Security

Never expose API keys, credentials, or sensitive information in public repositories. Do not execute untrusted generated code outside a suitable security sandbox.

## 👨‍💻 Author

**Kumar Suryansh**

- GitHub: [@Kumar-Suryansh](https://github.com/Kumar-Suryansh)
- Repository: [Self-Healing-Code-Reviewer](https://github.com/Kumar-Suryansh/Self-Healing-Code-Reviewer)

---

*Built using Python, LangGraph, Streamlit, and Groq for AI-assisted code generation and iterative review.*
