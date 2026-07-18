"""
CyberSecure Log Analysis & Threat Hunting System
Main Application Entry Point

Multi-Level Secured Log Analysis and Threat Hunting Web Application
with Real-Time Email Alert System
"""
import os
import sys
from flask import Flask, redirect, url_for, render_template

# Ensure src directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from models import init_db
from auth import auth_bp
from dashboard import dashboard_bp
from threat_hunter import threat_bp


def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(threat_bp)
    
    # Root route - splash intro page
    @app.route('/')
    def index():
        return render_template('splash.html')
    
    # Welcome page with Login / Sign Up options
    @app.route('/welcome')
    def welcome():
        return render_template('welcome.html')
    
    # Initialize database
    with app.app_context():
        init_db()
    
    return app


if __name__ == '__main__':
    app = create_app()
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║   🛡️  CYBERSECURE LOG ANALYSIS & THREAT HUNTING  🛡️  ║
    ║                                                      ║
    ║   Multi-Level Secured Log Analysis System             ║
    ║   with Real-Time Email Alert System                   ║
    ║                                                      ║
    ║   Server: http://127.0.0.1:5000                      ║
    ╚══════════════════════════════════════════════════════╝
    """)
    app.run(debug=True, host='127.0.0.1', port=5000)
