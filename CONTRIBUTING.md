# Contributing to FixFlow

Thank you for your interest in contributing to FixFlow! FixFlow is designed to bridge classical Dynamic Programming algorithms with modern NLP techniques. We welcome contributions from developers, researchers, and linguists alike.

---

## 📋 Table of Contents
- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Pull Requests](#pull-requests)
- [Local Development Setup](#local-development-setup)
- [Running Tests](#running-tests)
- [Coding Guidelines](#coding-guidelines)
- [License](#license)

---

## 📜 Code of Conduct
Please be polite, respectful, and collaborative. We aim to foster an inclusive and productive open-source community.

---

## 🚀 How to Contribute

### Reporting Bugs
If you encounter a bug:
1. Search the existing [GitHub Issues](https://github.com/) to see if it has already been reported.
2. If not, open a new issue using our **Bug Report** template.
3. Include clear reproduction steps, expected vs. actual behavior, and relevant system details (OS, Python version).

### Suggesting Enhancements
Feature requests and algorithm improvements are welcome! Please open an issue using the **Feature Request** template describing the proposed feature, the use case, and any relevant algorithmic considerations (time/space complexity).

### Pull Requests
1. **Fork** the repository and clone it to your machine.
2. Create a new topic branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes and ensure tests pass.
4. Add unit tests for any new functionality or bug fixes.
5. Commit with clear, descriptive commit messages:
   ```bash
   git commit -m "feat(dp): optimize Levenshtein rolling buffer memory layout"
   ```
6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
7. Open a Pull Request against the `main` branch.

---

## 💻 Local Development Setup

1. **Clone your fork:**
   ```bash
   git clone https://github.com/<your-username>/fixflow.git
   cd fixflow
   ```

2. **Create and activate a virtual environment:**
   - **Linux / macOS:**
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```
   - **Windows:**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```

---

## 🧪 Running Tests

Always verify that the test suite passes before opening a pull request:

```bash
python test_fixflow.py
```

If you have `pytest` installed:
```bash
pytest
```

---

## 📐 Coding Guidelines

- **PEP 8**: Follow standard Python conventions (naming, 4-space indentation, docstrings).
- **DP Algorithms**: When adding or modifying Dynamic Programming functions, document:
  - Recurrence relations
  - Base cases
  - Time complexity ($O(m \cdot n)$ etc.)
  - Space complexity
- **Type Hints**: Include type hints (`typing`) on public function signatures where appropriate.
- **Pure Python First**: Core DP algorithms should run without mandatory external C/CUDA dependencies so they remain universally accessible.

---

## 📄 License
By contributing to FixFlow, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).

