from django.db import models
from django.contrib.auth.models import User
import chess  

class ChessGame(models.Model):
    player1 = models.ForeignKey(User, related_name='games_as_player1', on_delete=models.CASCADE)
    player2 = models.ForeignKey(User, related_name='games_as_player2', on_delete=models.CASCADE, null=True, blank=True)  
    fen = models.CharField(max_length=100, default=chess.Board().fen())  
    current_turn = models.ForeignKey(User, related_name='current_turn_games', on_delete=models.SET_NULL, null=True, blank=True) 
    is_active = models.BooleanField(default=True)  
    game_status = models.CharField(max_length=20, default='active')
    journal_entry = models.TextField(null=True, blank=True)  
    move_count = models.IntegerField(default=0)
    player1_move_count = models.IntegerField(default=0)
    player2_move_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f'Game {self.id}: {self.player1.username} vs {self.player2.username if self.player2 else "Waiting"}'
    
class GameInvite(models.Model):
    sender = models.ForeignKey(User, related_name="sent_invites", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="received_invites", on_delete=models.CASCADE)
    game = models.ForeignKey(ChessGame, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invite from {self.sender.username} to {self.receiver.username}"
