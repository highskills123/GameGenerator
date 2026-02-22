"""
Example usage of Aibase translator
"""

from aibase import AibaseTranslator
import os

# Example 1: Simple function generation
def example_simple():
    """Generate a simple function."""
    print("Example 1: Simple Function Generation")
    print("-" * 50)
    
    translator = AibaseTranslator()
    
    description = "Create a function that checks if a number is prime"
    code = translator.translate(description, target_language='python')
    
    print(f"Description: {description}")
    print(f"\nGenerated Code:\n{code}\n")


# Example 2: Generate code in different languages
def example_multiple_languages():
    """Generate the same logic in different languages."""
    print("\nExample 2: Multiple Language Generation")
    print("-" * 50)
    
    translator = AibaseTranslator()
    
    description = "Create a function that reverses a string"
    
    for lang in ['python', 'javascript', 'java']:
        print(f"\n{lang.upper()}:")
        code = translator.translate(description, target_language=lang, include_comments=False)
        print(code)
        print()


# Example 3: Complex application
def example_complex():
    """Generate a more complex application."""
    print("\nExample 3: Complex Application")
    print("-" * 50)
    
    translator = AibaseTranslator()
    
    description = """
    Create a simple todo list manager with the following features:
    - Add a new todo item
    - Mark a todo as completed
    - List all todos
    - Delete a todo
    Use a list to store the todos.
    """
    
    code = translator.translate(description, target_language='python')
    
    print(f"Description: {description.strip()}")
    print(f"\nGenerated Code:\n{code}\n")


if __name__ == '__main__':
    print("Aibase Examples")
    print("=" * 50)

    # Run examples
    try:
        example_simple()
        # Uncomment to run more examples:
        # example_multiple_languages()
        # example_complex()

    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}")
        print("\nMake sure Ollama is running and the model is pulled:")
        print("  ollama pull qwen2.5-coder:7b")
    except Exception as e:
        print(f"Unexpected error: {e}")
