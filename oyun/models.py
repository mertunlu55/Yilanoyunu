from django.db import models


class Player(models.Model):
    username = models.CharField(max_length=32, unique=True)
    password = models.CharField(max_length=255, default="")  # Basit şifre saklama (production'da hash kullanılmalı)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


class Score(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="scores")
    value = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-value", "-created_at"]

    def __str__(self):
        return f"{self.player.username} - {self.value}"
