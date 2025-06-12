# Chess Multiplayer Web Application

This is a real-time, multiplayer chess web application built using Django, Django Channels, and WebSockets. The game supports login/logout, game invites, turn-based play, game history, journaling, and deployment on Google Cloud Platform. Developed as part of the CSCI 620 Full Stack Web Development course.

## Features

- User registration, login, and logout functionality
- Real-time multiplayer chess with move validation via python-chess
- Invite and challenge other logged-in players
- Turn indicator and resign option
- Game restrictions: one game per user at a time
- Game history tracking: moves, outcomes, and opponent
- Journal entry feature for completed games
- Option to delete game history with confirmation modal
- Static pages: Rules, About, and History (publicly viewable)
- Organized static files (CSS, JS, fonts, images)
- Responsive layout using Bootstrap grid system

## Technology Stack

- **Backend**: Django, Django Channels, python-chess
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Database**: PostgreSQL
- **Real-time Communication**: WebSockets (via Django Channels)
- **Deployment**: Docker, Google Cloud Platform (GCP)


