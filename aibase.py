#!/usr/bin/env python3
"""
Aibase - AI Language to Code Translator
A tool that translates natural language descriptions into working code.
"""

import os
import sys
import requests
from dotenv import load_dotenv
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init(autoreset=True)

# Load environment variables
load_dotenv()


class AibaseTranslator:
    """Main class for translating natural language to code."""

    # Provider
    PROVIDER_OLLAMA = 'ollama'

    # Default generation parameters
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 2000

    # Ollama defaults
    DEFAULT_OLLAMA_BASE_URL = 'http://localhost:11434'
    DEFAULT_OLLAMA_MODEL = 'qwen2.5-coder:7b'

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
        'flame': 'Flame (Flutter Game Engine)',
        'flame-game': 'Flame Complete Game',
        'flame-component': 'Flame Game Component',
        'game-asset-sprite': 'Game Sprite Asset Code',
        'game-asset-animation': 'Game Animation Asset Code',
        'game-tilemap': 'Game Tilemap Code',
    }

    @staticmethod
    def resolve_provider(provider=None):
        """Always returns 'ollama' — the only supported provider."""
        return AibaseTranslator.PROVIDER_OLLAMA

    def __init__(self, model=None, temperature=None, max_tokens=None, **_ignored):
        """
        Initialize the translator.

        Args:
            model (str): Ollama model to use (default: qwen2.5-coder:7b).
            temperature (float): Temperature for generation (default: 0.7).
            max_tokens (int): Maximum tokens to generate (default: 2000).
        """
        self.provider = self.PROVIDER_OLLAMA
        self.temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE
        self.max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', self.DEFAULT_OLLAMA_BASE_URL)
        self.model = model or os.getenv('OLLAMA_MODEL', self.DEFAULT_OLLAMA_MODEL)
    
    def _build_prompts(self, description, lang_name, include_comments, language_key=''):
        """Build system and user prompts for code generation."""
        key = language_key.lower()

        # System prompt: specialized for Flame or game-asset, default otherwise
        if key.startswith('flame'):
            system_prompt = (
                f"You are an expert Flutter and Flame game engine developer. "
                f"Generate clean, efficient, and well-structured {lang_name} code. "
                f"Use Flame best practices, proper game component structure, and Flutter conventions. "
                f"Include necessary imports (flame, flutter packages). "
                f"{'Include helpful comments to explain game logic and components.' if include_comments else 'Minimize comments.'}"
            )
        elif key.startswith('game-'):
            system_prompt = (
                f"You are an expert game developer specializing in {lang_name}. "
                f"Generate clean, efficient code for game asset management and rendering. "
                f"Focus on performance, reusability, and proper asset loading patterns. "
                f"{'Include helpful comments to explain asset handling.' if include_comments else 'Minimize comments.'}"
            )
        else:
            system_prompt = (
                f"You are an expert programmer that translates natural language descriptions "
                f"into clean, efficient, and well-structured {lang_name} code. "
                f"Provide only the code without additional explanations unless specifically asked. "
                f"{'Include helpful comments to explain the code.' if include_comments else 'Minimize comments.'}"
            )

        # User prompt: specialized per language key
        if key == 'flame-game':
            user_prompt = (
                f"Create a complete Flame game project for: {description}\n\n"
                f"Include:\n"
                f"- Main game class extending FlameGame\n"
                f"- Game components and entities\n"
                f"- Proper initialization and lifecycle methods\n"
                f"- Game loop integration\n"
                f"Provide complete, working code that can be integrated into a Flutter app."
            )
        elif key == 'flame-component':
            user_prompt = (
                f"Create Flame game components for: {description}\n\n"
                f"Include:\n"
                f"- Component classes extending PositionComponent or SpriteComponent\n"
                f"- Update and render methods\n"
                f"- Collision detection if needed\n"
                f"- Proper component lifecycle\n"
                f"Provide complete, working code."
            )
        elif key == 'flame':
            user_prompt = (
                f"Create Flame game code for: {description}\n\n"
                f"Use Flame framework and Flutter best practices.\n"
                f"Include necessary imports and proper game structure.\n"
                f"Provide complete, working code."
            )
        elif key == 'game-asset-sprite':
            user_prompt = (
                f"Create sprite asset management code for: {description}\n\n"
                f"Include:\n"
                f"- Sprite loading and caching\n"
                f"- Sprite sheet handling if needed\n"
                f"- Animation frame management\n"
                f"- Efficient rendering code\n"
                f"Provide complete, working code."
            )
        elif key == 'game-asset-animation':
            user_prompt = (
                f"Create animation asset code for: {description}\n\n"
                f"Include:\n"
                f"- Animation state management\n"
                f"- Frame interpolation\n"
                f"- Animation controllers\n"
                f"- Smooth transitions\n"
                f"Provide complete, working code."
            )
        elif key == 'game-tilemap':
            user_prompt = (
                f"Create tilemap generation and rendering code for: {description}\n\n"
                f"Include:\n"
                f"- Tilemap data structure\n"
                f"- Tile rendering logic\n"
                f"- Map parsing and loading\n"
                f"- Collision detection for tiles\n"
                f"Provide complete, working code."
            )
        else:
            user_prompt = (
                f"Convert the following natural language description into {lang_name} code:\n\n"
                f"{description}\n\n"
                f"Provide complete, working code that can be run or used directly."
            )
        return system_prompt, user_prompt

    @staticmethod
    def _strip_code_fences(text):
        """Remove surrounding markdown code fences if present."""
        if text.startswith('```'):
            lines = text.split('\n')
            if len(lines) > 2 and lines[-1].strip() == '```':
                text = '\n'.join(lines[1:-1])
        return text

    def _generate_ollama(self, system_prompt, user_prompt):
        """Generate code using the local Ollama HTTP API."""
        url = f"{self.ollama_base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            return resp.json()["response"].strip()
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.ollama_base_url}. "
                "Make sure Ollama is running (https://ollama.com) and the model is pulled."
            )
        except Exception as e:
            raise RuntimeError(f"Error during Ollama generation: {str(e)}")

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
        system_prompt, user_prompt = self._build_prompts(description, lang_name, include_comments, target_language.lower())
        return self._strip_code_fences(self._generate_ollama(system_prompt, user_prompt))
    
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
        help=f'Ollama model to use (default: {AibaseTranslator.DEFAULT_OLLAMA_MODEL})'
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
            max_tokens=args.max_tokens,
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
