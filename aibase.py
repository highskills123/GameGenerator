#!/usr/bin/env python3
"""
Aibase - AI Language to Code Translator
A tool that translates natural language descriptions into working code.
"""

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init(autoreset=True)

# Load environment variables
load_dotenv()


class AibaseTranslator:
    """Main class for translating natural language to code."""
    
    # Default model and generation parameters
    DEFAULT_MODEL = "gpt-3.5-turbo"
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 2000
    
    SUPPORTED_LANGUAGES = {
        'python': 'Python',
        'javascript': 'JavaScript',
        'java': 'Java',
        'cpp': 'C++',
        'csharp': 'C#',
        'go': 'Go',
        'rust': 'Rust',
        'typescript': 'TypeScript',
        'php': 'PHP',
        'ruby': 'Ruby',
        'swift': 'Swift',
        'kotlin': 'Kotlin',
        'dart': 'Dart',
        'flutter': 'Flutter/Dart',
        'flutter-widget': 'Flutter Widget',
        'react-native': 'React Native',
        'react-native-component': 'React Native Component'
    }
    
    def __init__(self, api_key=None, model=None, temperature=None, max_tokens=None):
        """
        Initialize the translator with OpenAI API key.
        
        Args:
            api_key (str): OpenAI API key (defaults to OPENAI_API_KEY env var)
            model (str): Model to use (defaults to gpt-3.5-turbo)
            temperature (float): Temperature for generation (defaults to 0.7)
            max_tokens (int): Maximum tokens to generate (defaults to 2000)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY environment variable "
                "or pass it to the constructor."
            )
        self.client = OpenAI(api_key=self.api_key)
        self.model = model or self.DEFAULT_MODEL
        self.temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE
        self.max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
    
    def translate(self, description, target_language='python', include_comments=True):
        """
        Translate natural language description to code.
        
        Args:
            description (str): Natural language description of what the code should do
            target_language (str): Programming language to generate code in
            include_comments (bool): Whether to include explanatory comments
            
        Returns:
            str: Generated code
        """
        if target_language.lower() not in self.SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language: {target_language}. "
                f"Supported languages: {', '.join(self.SUPPORTED_LANGUAGES.keys())}"
            )
        
        lang_name = self.SUPPORTED_LANGUAGES[target_language.lower()]
        
        system_prompt = (
            f"You are an expert programmer that translates natural language descriptions "
            f"into clean, efficient, and well-structured {lang_name} code. "
            f"Provide only the code without additional explanations unless specifically asked. "
            f"{'Include helpful comments to explain the code.' if include_comments else 'Minimize comments.'}"
        )
        
        user_prompt = (
            f"Convert the following natural language description into {lang_name} code:\n\n"
            f"{description}\n\n"
            f"Provide complete, working code that can be run or used directly."
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            generated_code = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if generated_code.startswith('```'):
                lines = generated_code.split('\n')
                # Remove first and last lines (markdown delimiters)
                generated_code = '\n'.join(lines[1:-1]) if len(lines) > 2 else generated_code
            
            return generated_code
            
        except Exception as e:
            raise RuntimeError(f"Error during translation: {str(e)}")
    
    def translate_interactive(self):
        """Run an interactive session for translating descriptions to code."""
        print(f"{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}Aibase - AI Language to Code Translator")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        while True:
            try:
                # Get description from user
                print(f"{Fore.GREEN}Enter your description (or 'quit' to exit):{Style.RESET_ALL}")
                description = input("> ").strip()
                
                if description.lower() in ['quit', 'exit', 'q']:
                    print(f"\n{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
                    break
                
                if not description:
                    print(f"{Fore.RED}Please enter a description.{Style.RESET_ALL}\n")
                    continue
                
                # Get target language
                print(f"\n{Fore.GREEN}Target language (default: python):{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Supported: {', '.join(self.SUPPORTED_LANGUAGES.keys())}{Style.RESET_ALL}")
                target_lang = input("> ").strip().lower() or 'python'
                
                if target_lang not in self.SUPPORTED_LANGUAGES:
                    print(f"{Fore.RED}Unsupported language. Using Python.{Style.RESET_ALL}")
                    target_lang = 'python'
                
                # Generate code
                print(f"\n{Fore.YELLOW}Generating code...{Style.RESET_ALL}\n")
                code = self.translate(description, target_lang)
                
                # Display result
                print(f"{Fore.CYAN}{'='*70}")
                print(f"{Fore.GREEN}Generated {self.SUPPORTED_LANGUAGES[target_lang]} Code:")
                print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
                print(code)
                print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
                
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}\n")


def main():
    """Main entry point for the CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Aibase - AI Language to Code Translator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Interactive mode
  python aibase.py
  
  # Direct translation
  python aibase.py -d "create a function that calculates fibonacci numbers"
  
  # Specify target language
  python aibase.py -d "create a REST API server" -l javascript
        '''
    )
    
    parser.add_argument(
        '-d', '--description',
        help='Natural language description of code to generate'
    )
    parser.add_argument(
        '-l', '--language',
        default='python',
        help='Target programming language (default: python)'
    )
    parser.add_argument(
        '--no-comments',
        action='store_true',
        help='Generate code without explanatory comments'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file path to save generated code'
    )
    parser.add_argument(
        '--model',
        help=f'OpenAI model to use (default: {AibaseTranslator.DEFAULT_MODEL})'
    )
    parser.add_argument(
        '--temperature',
        type=float,
        help=f'Temperature for generation 0.0-1.0 (default: {AibaseTranslator.DEFAULT_TEMPERATURE})'
    )
    parser.add_argument(
        '--max-tokens',
        type=int,
        help=f'Maximum tokens to generate (default: {AibaseTranslator.DEFAULT_MAX_TOKENS})'
    )
    
    args = parser.parse_args()
    
    try:
        translator = AibaseTranslator(
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens
        )
        
        if args.description:
            # Direct translation mode
            print(f"{Fore.YELLOW}Generating code...{Style.RESET_ALL}\n")
            code = translator.translate(
                args.description,
                args.language,
                include_comments=not args.no_comments
            )
            
            print(f"{Fore.CYAN}{'='*70}")
            print(f"{Fore.GREEN}Generated {translator.SUPPORTED_LANGUAGES.get(args.language.lower(), args.language)} Code:")
            print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
            print(code)
            print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
            
            # Save to file if specified
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(code)
                print(f"{Fore.GREEN}Code saved to: {args.output}{Style.RESET_ALL}\n")
        else:
            # Interactive mode
            translator.translate_interactive()
            
    except ValueError as e:
        print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}Unexpected error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == '__main__':
    main()
