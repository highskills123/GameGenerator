# Quick Start Guide

## Setup (One-time)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API key:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

## Usage Examples

### Interactive Mode (Recommended for Beginners)
```bash
python aibase.py
```
Then follow the prompts to describe your code and select a language.

### Command Line Examples

**Generate a Python function:**
```bash
python aibase.py -d "create a function that checks if a string is a palindrome"
```

**Generate JavaScript code:**
```bash
python aibase.py -d "create an async function to fetch data from an API" -l javascript
```

**Save to a file:**
```bash
python aibase.py -d "create a class for a stack data structure" -o stack.py
```

**Generate without comments:**
```bash
python aibase.py -d "create a merge sort function" --no-comments
```

## Common Use Cases

### 1. Algorithm Implementation
```bash
python aibase.py -d "implement binary search algorithm"
```

### 2. Data Structure
```bash
python aibase.py -d "create a linked list class with insert and delete methods" -l python
```

### 3. Utility Functions
```bash
python aibase.py -d "create a function to validate email addresses using regex"
```

### 4. API Endpoints
```bash
python aibase.py -d "create an Express.js endpoint for user registration" -l javascript
```

### 5. Database Queries
```bash
python aibase.py -d "create a SQL query to find top 10 customers by purchase amount"
```

## Programmatic Usage

```python
from aibase import AibaseTranslator

# Initialize
translator = AibaseTranslator()

# Generate code
code = translator.translate(
    description="Create a function that finds the longest common substring",
    target_language="python"
)

# Use the generated code
print(code)
```

## Tips for Best Results

1. **Be Specific**: The more detailed your description, the better the output
   - ❌ "create a function"
   - ✅ "create a function that takes a list of integers and returns the sum of even numbers"

2. **Specify Requirements**: Include any constraints or requirements
   - ✅ "create a REST API endpoint with error handling and input validation"

3. **Mention Data Structures**: If you need specific data structures, mention them
   - ✅ "create a function using a hash map to find duplicate elements"

4. **Include Edge Cases**: Mention important edge cases
   - ✅ "create a function that handles empty strings and null values"

## Troubleshooting

**Error: OpenAI API key not found**
- Make sure you've created a `.env` file with your API key
- Check that the key is correct and active

**Error: Unsupported language**
- Check the list of supported languages in README.md
- Use the exact language name (e.g., "javascript" not "js")

**Generated code is not what you expected**
- Try being more specific in your description
- Break complex requests into smaller parts
- Use the interactive mode to iterate on your request

## Next Steps

- Check out `examples.py` for more code examples
- Read the full README.md for detailed documentation
- Experiment with different languages and descriptions
