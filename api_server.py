#!/usr/bin/env python3
"""
Aibase API Server
REST API interface for the AI code translator
"""

import os
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
        "language": "python",  // optional, defaults to python
        "include_comments": true,  // optional, defaults to true
        "model": "gpt-3.5-turbo",  // optional
        "temperature": 0.7,  // optional
        "max_tokens": 2000  // optional
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
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    Aibase API Server                         ║
╚══════════════════════════════════════════════════════════════╝

Server starting...
URL: http://{args.host}:{args.port}
Debug mode: {args.debug}

Web UI:   http://{args.host}:{args.port}/

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
