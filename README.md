# Capstone 1

api: [text](https://www.freetogame.com/api)

MentalGaming - LINK WHERE ITS DEPLOYED

# Features implemented:
- Optional favoriting of games played
    --> allows the user to return to only the games they've favorited instead of having to list through all the games they've previously played
- Profile page and profile editing
    --> allows the user to view their information and a list of games they've played as well as edit their profile information such as username or email
- seeing survey results for each individual game played
    --> clicking on a game from the "Your Games" tab brings you to a page describing the game along with the user's survey results when they played that particular game

# Standard user flow:
1. User registers and creates an account
2. User clicks 'play game' button
3. User is taken to a 'before' survey
4. On submission of the survey the user is brought to a page of three randomly selected games from the freetogame api
5. The user selects a game and is taken to a separate tab to play the game
6. The user then returns to MentalGaming and submits which game they played by clicking 'save game'
7. User is taken to the 'after' survey
8. On submission the user is taken to the thank you page that displays their before and after survey results
9. User can choose to take another 'before' survey in order to access additional free browser games

# Tech stack used:
- Python/flask
- WTForms
- Jinja
- CSS
- HTML
- JavaScript
- PostgreSQL
- SQLAlchemy