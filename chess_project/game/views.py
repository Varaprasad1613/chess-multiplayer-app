from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
import chess
import chess.svg
from .models import ChessGame, GameInvite
from django.contrib.auth import logout
from django.views.decorators.cache import cache_control
from django.urls import reverse




def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home(request):
    if request.user.is_authenticated:
        active_users = get_active_users(request)
        user_games = ChessGame.objects.filter(
            (Q(player1=request.user) | Q(player2=request.user)) & Q(is_active=False)
        ).order_by('-id')  

        user_games_with_opponents = []
        for game in user_games:
            if request.user == game.player1:
                opponent = game.player2
                player_move_count = game.player1_move_count
            else:
                opponent = game.player1
                player_move_count = game.player2_move_count

            user_games_with_opponents.append({
                'game': game,
                'opponent': opponent,
                'player_move_count': player_move_count,
            })

        context = {
            'active_users': active_users,
            'user_games_with_opponents': user_games_with_opponents,
        }

        return render(request, 'game_view.html', context)
    else:
        return redirect('login')

def history(request):
    return render(request, 'history.html')

def rules(request):
    return render(request, 'rules.html')

def about(request):
    return render(request, 'about.html')

def get_active_users(request):
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    user_ids = []
    
    for session in active_sessions:
        data = session.get_decoded()
        user_id = data.get('_auth_user_id')
        if user_id:
            user_ids.append(user_id)

    active_game_user_ids = ChessGame.objects.filter(is_active=True).values_list('player1', 'player2')
    active_game_user_ids = set([player_id for pair in active_game_user_ids for player_id in pair if player_id])

    available_users = User.objects.filter(id__in=user_ids).exclude(id__in=active_game_user_ids)

    return available_users

@login_required
def join_game(request, game_id):
    game = get_object_or_404(ChessGame, id=game_id)

    if request.user == game.player1:
        return JsonResponse({'status': 'error', 'message': 'You cannot join your own game as player 2'})

    if game.player2 is None and game.is_active:
        game.player2 = request.user
        game.save()

    return redirect('game_view', game_id=game.id)

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def game_view(request, game_id):
    game = get_object_or_404(ChessGame, id=game_id)
    board = chess.Board(game.fen)

    user_role = None
    if request.user == game.player1:
        user_role = 'white'
    elif request.user == game.player2:
        user_role = 'black'

    game_history = ChessGame.objects.filter(
        (Q(player1=request.user) | Q(player2=request.user)) & Q(is_active=False)
    )

    if not game.is_active:
        return redirect('home')

    context = {
        'game': game,
        'user_role': user_role,
        'board_svg': chess.svg.board(board),
        'current_turn': 'white' if board.turn == chess.WHITE else 'black',
        'active_users': get_active_users(request),
        'game_history': game_history,
    }

    return render(request, 'chessboard.html', context)



def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            ongoing_game = ChessGame.objects.filter(
                player1=user, is_active=True
            ).first() or ChessGame.objects.filter(
                player2=user, is_active=True
            ).first()

            if ongoing_game:
                return redirect('game_view', game_id=ongoing_game.id)
            else:
                return redirect('home')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

@login_required
def custom_logout(request):
    logout(request)
    if request.session.session_key:
        Session.objects.filter(session_key=request.session.session_key).delete()
    return redirect('login')



@login_required
def game_view(request, game_id):
    game = get_object_or_404(ChessGame, id=game_id)
    board = chess.Board(game.fen)

    if board.is_checkmate():
        game_status = f"Checkmate! {'White' if board.turn == chess.BLACK else 'Black'} wins!"
    elif board.is_stalemate():
        game_status = "Stalemate! The game is a draw."
    else:
        game_status = "active"

    current_turn_username = game.player1.username if board.turn == chess.WHITE else game.player2.username

    context = {
        'game': game,
        'current_turn_username': current_turn_username,
        'game_status': game_status,
    }

    return render(request, 'chessboard.html', context)


@login_required
def exit_game(request, game_id):
    game = get_object_or_404(ChessGame, id=game_id)

    if request.user == game.player1:
        exited_player = 'player1'
        opponent = game.player2.username if game.player2 else None
    elif request.user == game.player2:
        exited_player = 'player2'
        opponent = game.player1.username if game.player1 else None
    else:
        return JsonResponse({'status': 'error', 'message': 'You are not a participant in this game.'})
    
    game.is_active = False
    game.game_status = f'Game ended by {request.user.username}.'
    game.save()

    return JsonResponse({'status': 'success', 'exited_player': exited_player, 'opponent': opponent})
    



@login_required
def edit_game(request, game_id):
    game = get_object_or_404(ChessGame, id=game_id)

    if request.user != game.player1 and request.user != game.player2:
        return JsonResponse({'status': 'error', 'message': 'You are not allowed to edit this game.'}, status=403)

    if request.method == 'POST':
        journal_entry = request.POST.get('journal_entry')
        game.journal_entry = journal_entry
        game.save()
        return redirect('home')
    return render(request, 'edit_game.html', {'game': game})


@login_required
def delete_game(request, game_id):
    game = get_object_or_404(ChessGame, id=game_id)
    
    if request.user == game.player1 or request.user == game.player2:
        game.delete()
        return redirect(f'{reverse("home")}?deleted=1')
    else:
        return redirect('home')
