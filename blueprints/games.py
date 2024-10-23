"""Game routes."""

from flask import Blueprint, render_template, redirect, flash, g, request
from models import db, Game, Favorite, Survey
import requests
import random
from helpers import unauthorized

games_bp = Blueprint('games', __name__)

base_URL = "https://www.freetogame.com/api"
browser_games_URL = "https://www.freetogame.com/api/games?platform=browser"

@games_bp.route('/games')
def get_random_games():
    """Get three random games from API and display the options."""

    if not g.user:
        unauthorized()
        return redirect('/')

    res = requests.get(browser_games_URL)

    if res.status_code == 200:
        games = res.json()

        # Get three random games
        random_games = random.sample(games, 3)

        game_data = [
            {
                "title": game["title"],
                "id": game["id"],
                "description": game["short_description"],
                "genre": game["genre"],
                "url": game["game_url"]
            }
            for game in random_games
        ]

        return render_template('games/random-games.html', games=game_data)

    else:
        return "Failed to retrieve data from the API", 500
    
@games_bp.route('/games/<int:game_id>')
def show_game_details(game_id):
    """Show game information"""

    if not g.user:
        unauthorized()
        return redirect('/')
    
    game = Game.query.get_or_404(game_id)

    surveys = Survey.query.filter_by(user_id=g.user.id, game_id=game_id).all()

    return render_template('games/game.html', game=game, user=g.user, surveys=surveys)

@games_bp.route('/games/add-like/<int:game_id>', methods=['POST'])
def favorite_game(game_id):
    """Add or remove a game from user's favorites."""
    
    if not g.user:
        unauthorized()
        return redirect('/')

    game = Game.query.get_or_404(game_id)

    # Check if the game is already favorited by the user
    favorite = Favorite.query.filter_by(user_id=g.user.id, game_id=game.id).first()

    if favorite:
        # If it exists, remove it (unfavorite)
        db.session.delete(favorite)
        db.session.commit()
        flash(f"Removed {game.title} from your favorites.", "info")
    else:
        # If it doesn't exist, add it (favorite)
        new_favorite = Favorite(user_id=g.user.id, game_id=game.id)
        db.session.add(new_favorite)
        db.session.commit()
        flash(f"Added {game.title} to your favorites.", "success")

    return redirect(f'/users/{g.user.id}/games')

@games_bp.route('/games/save-game', methods=['POST'])
def save_selected_game():
    """Save the game selected to database and open game tab."""

    if not g.user:
        unauthorized()
        return redirect('/')

    game_id = request.form.get("game_id") # is this line necessary?

    res = requests.get(f"{base_URL}/game?id={game_id}")

    if res.status_code == 200:
        game = res.json()

        # Check if this game has already been saved for this specific user
        existing_game = Game.query.filter_by(game_id=game['id'], user_id=g.user.id).first()

        if not existing_game:
            new_game = Game(
                game_id=game['id'],
                title=game['title'],
                genre=game['genre'],
                game_url=game['game_url'],
                user_id=g.user.id
            )
            db.session.add(new_game)
            db.session.commit()

            before_survey = Survey.query.filter_by(user_id=g.user.id, before_survey=True).order_by(Survey.created_at.desc()).first()
            before_survey.game_id = new_game.id
            db.session.commit()

        flash("Game saved successfully!", "success")
        return redirect('/surveys/finish')

    else:
        flash("Failed to retrieve game data.", "danger")
        return redirect('/games')