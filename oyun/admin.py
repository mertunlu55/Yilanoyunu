from django.contrib import admin
from .models import Player, Score


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("username", "created_at")
    search_fields = ("username",)


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("player", "value", "created_at")
    list_filter = ("created_at",)
    search_fields = ("player__username",)
