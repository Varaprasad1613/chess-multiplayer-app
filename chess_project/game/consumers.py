import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.db.models import Q
from .models import GameInvite, ChessGame
import logging
import chess
from .models import ChessGame

logger = logging.getLogger(__name__)

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.group_name = f'game_{self.game_id}'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"WebSocket connected: {self.channel_name} for game {self.game_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected: {self.channel_name}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'move':
            await self.handle_move(data.get('move'))
        elif action == 'exit':
            await self.handle_exit()
        else:
            logger.warning(f"Unknown action received: {action}")



    async def handle_move(self, move):
        try:
            game = await self.get_game()
            board = chess.Board(game.fen)
            user = self.scope['user']

            if user != game.player1 and user != game.player2:
                await self.send(text_data=json.dumps({'action': 'error', 'message': 'You are not a player in this game.'}))
                return

            board.push_uci(move)
            game.fen = board.fen()

            if user == game.player1:
                game.player1_move_count += 1
            elif user == game.player2:
                game.player2_move_count += 1


            if board.is_checkmate():
                winner = game.player2 if board.turn == chess.WHITE else game.player1
                game.game_status = f"{winner.username} won by checkmate"
                game.is_active = False
                game.current_turn = None
            elif board.is_stalemate():
                game.game_status = f"Game drawn by stalemate between {game.player1.username} and {game.player2.username}"
                game.is_active = False
                game.current_turn = None
            elif board.is_insufficient_material():
                game.game_status = "Draw by insufficient material"
                game.is_active = False
            elif board.is_fivefold_repetition():
                game.game_status = "Draw by repetition"
                game.is_active = False
            else:
                game.current_turn = game.player1 if board.turn == chess.WHITE else game.player2

            await sync_to_async(game.save)()

            current_turn_username = game.current_turn.username if game.current_turn else "unknown"

            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'game_update',
                    'fen': game.fen,
                    'game_status': game.game_status,
                    'current_turn_username': current_turn_username,
                }
            )
        except ValueError:
            await self.send(text_data=json.dumps({'action': 'error', 'message': 'Invalid move'}))

    async def game_update(self, event):
        await self.send(text_data=json.dumps({
            'action': 'move',
            'fen': event['fen'],
            'game_status': event['game_status'],
            'current_turn_username': event['current_turn_username'],
        }))

    @sync_to_async
    def get_game(self):
        return ChessGame.objects.select_related('player1', 'player2', 'current_turn').get(id=self.game_id)

    async def handle_exit(self):
        game = await self.get_game()
        resigning_player = self.scope['user']

        if not resigning_player.is_authenticated:
            await self.send(text_data=json.dumps({'action': 'error', 'message': 'User not authenticated'}))
            return

        if resigning_player == game.player1:
            winner = game.player2
            game.game_status = f"{game.player1.username} has resigned. {game.player2.username} wins!"
        elif resigning_player == game.player2:
            winner = game.player1
            game.game_status = f"{game.player2.username} has resigned. {game.player1.username} wins!"
        else:
            await self.send(text_data=json.dumps({'action': 'error', 'message': 'You are not a player in this game'}))
            return

        game.is_active = False
        game.current_turn = None  
        await sync_to_async(game.save)()

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'game_status',
                'message': game.game_status,
            }
        )


    async def game_status(self, event):
        await self.send(text_data=json.dumps({
            'action': 'game_status',
            'message': event['message'],
        }))



class LobbyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add('lobby', self.channel_name)
        await self.channel_layer.group_add(f'user_{self.user.id}', self.channel_name)
        await self.accept()

        await self.channel_layer.group_send('lobby', {
            'type': 'user_update',
            'action': 'join',
            'user_id': self.user.id,
            'username': self.user.username,
        })

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('lobby', self.channel_name)
        await self.channel_layer.group_discard(f'user_{self.user.id}', self.channel_name)

        await self.channel_layer.group_send('lobby', {
            'type': 'user_update',
            'action': 'leave',
            'user_id': self.user.id,
            'username': self.user.username,
        })

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'fetch_active_users':
            await self.send_active_users()
        elif action == 'send_invite':
            await self.handle_send_invite(data)
        elif action == 'respond_invite':
            await self.handle_respond_invite(data)
        elif action == 'check_game_status':
            await self.check_game_status()
        else:
            await self.send(text_data=json.dumps({'error': 'Invalid action'}))

    async def send_active_users(self):
        active_users = await self.get_active_users()
        await self.send(text_data=json.dumps({
            'action': 'active_users',
            'active_users': active_users,
        }))

    async def handle_send_invite(self, data):
        user_id = data.get('user_id')
        if not user_id:
            await self.send(text_data=json.dumps({'error': 'User ID is required'}))
            return

        def fetch_receiver_and_check():
            try:
                receiver = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return None, 'User does not exist'

            existing_game = ChessGame.objects.filter(
                (Q(player1=self.user, player2=receiver) | Q(player1=receiver, player2=self.user)) & Q(is_active=True)
            ).exists()
            if existing_game:
                return None, 'You are already playing a game with this user.'
                
            return receiver, None

        receiver, error = await sync_to_async(fetch_receiver_and_check)()
        if error:
            await self.send(text_data=json.dumps({'error': error}))
            return

        def create_invite():
            invite = GameInvite.objects.create(sender=self.user, receiver=receiver)
            return invite.id

        invite_id = await sync_to_async(create_invite)()

        await self.channel_layer.group_send(f'user_{receiver.id}', {
            'type': 'receive_invite',
            'invite_id': invite_id,
            'sender': self.user.username,
        })

        await self.send(text_data=json.dumps({
            'action': 'invite_sent',
            'message': f'Invite sent to {receiver.username}.',
        }))

    async def handle_respond_invite(self, data):
        invite_id = data.get('invite_id')
        response = data.get('response')
        if not invite_id or not response:
            await self.send(text_data=json.dumps({'error': 'Invite ID and response are required'}))
            return

        def get_invite_and_check():
            try:
                invite = GameInvite.objects.select_related('sender', 'receiver').get(id=invite_id)
            except GameInvite.DoesNotExist:
                return None, None, None, 'Invite does not exist'
            if invite.receiver_id != self.user.id:
                return None, None, None, 'Invalid invite'
            return invite, invite.sender.id, invite.receiver.username, None

        invite, sender_id, receiver_username, error = await sync_to_async(get_invite_and_check)()
        if error:
            await self.send(text_data=json.dumps({'error': error}))
            return

        if response == 'accept':
            def accept_invite():
                invite.status = 'accepted'
                game = ChessGame.objects.create(
                    player1=invite.sender,
                    player2=invite.receiver,
                    is_active=True
                )
                invite.game = game
                invite.save()
                return game.id, invite.sender.id, invite.receiver.id

            game_id, sender_id, receiver_id = await sync_to_async(accept_invite)()

            for user_id in [sender_id, receiver_id]:
                await self.channel_layer.group_send(f'user_{user_id}', {
                    'type': 'start_game',
                    'game_id': game_id,
                })
        elif response == 'decline':
            def decline_invite():
                invite.status = 'declined'
                invite.save()
                return invite.sender.id

            sender_id = await sync_to_async(decline_invite)()

            await self.channel_layer.group_send(f'user_{sender_id}', {
                'type': 'invite_declined',
                'receiver': self.user.username,
            })
        else:
            await self.send(text_data=json.dumps({'error': 'Invalid response'}))

    async def check_game_status(self):
        game = await sync_to_async(ChessGame.objects.filter)(
            (Q(player1=self.user) | Q(player2=self.user)) & Q(is_active=True)
        )
        game = await sync_to_async(game.first)()
        if game:
            await self.send(text_data=json.dumps({
                'action': 'game_status',
                'status': 'active',
                'game_id': game.id,
            }))
        else:
            await self.send(text_data=json.dumps({
                'action': 'game_status',
                'status': 'inactive',
            }))

    async def user_update(self, event):
        await self.send_active_users()

    async def receive_invite(self, event):
        await self.send(text_data=json.dumps({
            'action': 'receive_invite',
            'invite_id': event['invite_id'],
            'sender': event['sender'],
        }))

    async def start_game(self, event):
        await self.send(text_data=json.dumps({
            'action': 'start_game',
            'game_id': event['game_id'],
        }))

    async def invite_declined(self, event):
        await self.send(text_data=json.dumps({
            'action': 'invite_declined',
            'receiver': event['receiver'],
        }))

    async def get_active_users(self):
        def fetch_active_users():
            sessions = Session.objects.filter(expire_date__gte=timezone.now())
            user_ids = []
            for session in sessions:
                data = session.get_decoded()
                user_id = data.get('_auth_user_id')
                if user_id:
                    user_ids.append(int(user_id))
            active_games = ChessGame.objects.filter(is_active=True).values_list('player1', 'player2')
            active_game_user_ids = set([uid for pair in active_games for uid in pair if uid])
            available_user_ids = set(user_ids) - active_game_user_ids - {self.user.id}
            active_users = User.objects.filter(id__in=available_user_ids).values('id', 'username')
            return list(active_users)
        
        active_users_list = await sync_to_async(fetch_active_users)()
        return active_users_list

