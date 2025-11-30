from django.db import models


class Player(models.Model):
    username = models.CharField(max_length=32, unique=True)
    password = models.CharField(max_length=255, default="")  # Basit şifre saklama (production'da hash kullanılmalı)
    avatar = models.CharField(max_length=10, default="🐍")  # Emoji veya avatar kodu
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
    
    def get_highest_score(self):
        """Oyuncunun en yüksek skorunu döndürür"""
        from django.db.models import Max
        result = self.scores.aggregate(Max('value'))
        return result.get('value__max') or 0
    
    def get_total_games(self):
        """Oyuncunun toplam oyun sayısını döndürür"""
        return self.scores.count()
    
    def get_average_score(self):
        """Oyuncunun ortalama skorunu döndürür"""
        from django.db.models import Avg
        result = self.scores.aggregate(Avg('value'))
        return round(result.get('value__avg') or 0, 1)


class Score(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="scores")
    value = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-value", "-created_at"]

    def __str__(self):
        return f"{self.player.username} - {self.value}"
