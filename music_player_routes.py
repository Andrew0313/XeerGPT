from flask import send_from_directory
import os

def init_music_player_routes(app):
    @app.route('/music-player/')
    @app.route('/music-player/<path:filename>')
    def serve_music_player(filename='index.html'):
        # Get the path to the music-player folder (one level up from ai-website)
        music_player_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'music-player')
        
        # Security: prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            return "Not found", 404
            
        # Check if the file exists
        full_path = os.path.join(music_player_path, filename)
        if not os.path.exists(full_path):
            return f"File not found: {filename}", 404
            
        return send_from_directory(music_player_path, filename)