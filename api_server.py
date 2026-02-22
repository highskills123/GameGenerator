#!/usr/bin/env python3
"""
Aibase API Server
REST API interface for the AI code translator
"""

import os
import socket
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from aibase import AibaseTranslator

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize translator
translator = None

def get_translator():
    """Get or create translator instance."""
    global translator
    if translator is None:
        translator = AibaseTranslator()
    return translator


@app.route('/', methods=['GET'])
def index():
    """Serve the Aibase web UI."""
    return render_template('index.html')


@app.route('/api/info', methods=['GET'])
def api_info():
    """JSON description of available API endpoints."""
    return jsonify({
        'name': 'Aibase API',
        'version': '1.0.0',
        'description': 'AI-powered Natural Language to Code Translator',
        'endpoints': {
            'POST /api/translate': 'Translate natural language to code',
            'GET /api/languages': 'Get list of supported languages',
            'GET /api/health': 'Health check endpoint'
        }
    })


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'aibase-api'
    })


@app.route('/api/languages', methods=['GET'])
def get_languages():
    """Get list of supported programming languages."""
    return jsonify({
        'languages': list(AibaseTranslator.SUPPORTED_LANGUAGES.keys()),
        'count': len(AibaseTranslator.SUPPORTED_LANGUAGES)
    })


@app.route('/api/translate', methods=['POST'])
def translate():
    """
    Translate natural language description to code.
    
    Request body:
    {
        "description": "natural language description",
        "language": "python",       // optional, defaults to python
        "include_comments": true,   // optional, defaults to true
        "model": "qwen2.5-coder:7b", // optional, overrides OLLAMA_MODEL
        "temperature": 0.7,         // optional
        "max_tokens": 2000          // optional
    }
    
    Response:
    {
        "success": true,
        "code": "generated code",
        "language": "python"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        description = data.get('description')
        if not description:
            return jsonify({
                'success': False,
                'error': 'Description is required'
            }), 400
        
        # Get optional parameters
        language = data.get('language', 'python')
        include_comments = data.get('include_comments', True)
        model = data.get('model')
        temperature = data.get('temperature')
        max_tokens = data.get('max_tokens')
        
        # Validate language
        if language.lower() not in AibaseTranslator.SUPPORTED_LANGUAGES:
            return jsonify({
                'success': False,
                'error': f'Unsupported language: {language}',
                'supported_languages': list(AibaseTranslator.SUPPORTED_LANGUAGES.keys())
            }), 400
        
        # Get or create translator with custom parameters if provided
        if model or temperature is not None or max_tokens is not None:
            trans = AibaseTranslator(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            trans = get_translator()
        
        # Generate code
        code = trans.translate(
            description=description,
            target_language=language,
            include_comments=include_comments
        )
        
        # Return success response
        return jsonify({
            'success': True,
            'code': code,
            'language': language
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        app.logger.error(f"Translation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


def get_local_ip():
    """Return the machine's primary local-network IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
    except OSError:
        return None


def check_provider_config():
    """Return a status string about the Ollama configuration for the startup banner."""
    ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    model = os.getenv('OLLAMA_MODEL', 'qwen2.5-coder:7b')
    return (
        f'  Provider:       Ollama  ✓ (free, no API key needed)\n'
        f'  Ollama URL:     {ollama_url}\n'
        f'  Model:          {model}'
    )


def start_ngrok_tunnel(port):
    """
    Open a public ngrok HTTPS tunnel to *port* using pyngrok.

    Returns the public URL string on success, or None with a printed
    error message if pyngrok is not installed or the tunnel fails.
    """
    try:
        from pyngrok import ngrok, conf

        # Use authtoken from environment if provided
        authtoken = os.getenv('NGROK_AUTHTOKEN')
        if authtoken:
            conf.get_default().auth_token = authtoken

        tunnel = ngrok.connect(port, "http", bind_tls=True)
        return tunnel.public_url
    except ImportError:
        print(
            "\n  ⚠  pyngrok is not installed. Run:\n"
            "       pip install pyngrok\n"
            "  then restart the server.\n"
        )
        return None
    except Exception as exc:
        print(f"\n  ⚠  Could not start ngrok tunnel: {exc}\n")
        return None


def main():
    """Run the API server."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Aibase API Server - REST API for AI code translation'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind the server to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to run the server on (default: 5000)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )
    parser.add_argument(
        '--ngrok',
        action='store_true',
        help=(
            'Open a public ngrok tunnel so anyone on the internet can access '
            'the server. Requires pyngrok (pip install pyngrok). Optionally '
            'set NGROK_AUTHTOKEN in .env for longer sessions.'
        )
    )

    args = parser.parse_args()

    local_ip = get_local_ip()
    lan_line = (
        f"  Local network:  http://{local_ip}:{args.port}/\n  (anyone on your Wi-Fi/LAN can use this URL)"
        if local_ip else
        "  Local network:  (could not detect local IP)"
    )

    # Start ngrok tunnel before Flask so the URL is ready to print
    ngrok_url = None
    if args.ngrok:
        print("  Starting ngrok tunnel…", flush=True)
        ngrok_url = start_ngrok_tunnel(args.port)

    if ngrok_url:
        ngrok_line = (
            f"  🌍 Public URL:   {ngrok_url}\n"
            f"  Share this link with anyone — no router setup needed!"
        )
    else:
        ngrok_line = "  Public URL:     (ngrok not active — run with --ngrok to enable)"

    provider_info = check_provider_config()

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    Aibase API Server                         ║
╚══════════════════════════════════════════════════════════════╝

{provider_info}

Server running!  Open one of these URLs in a browser:

  This computer:  http://localhost:{args.port}/
{lan_line}
{ngrok_line}

Debug mode: {args.debug}

Endpoints:
  GET  /                   - Web UI (browser)
  GET  /api/info           - API information (JSON)
  GET  /api/health         - Health check
  GET  /api/languages      - List supported languages
  POST /api/translate      - Translate natural language to code

Press Ctrl+C to stop the server
""")
    
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\n\nError starting server: {e}")


if __name__ == '__main__':
    main()
