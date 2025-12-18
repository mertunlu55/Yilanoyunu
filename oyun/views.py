from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Player, Score


def index(request):
    return render(request, "oyun/index.html")


@csrf_exempt
def submit_score(request):
    """
    POST /api/score/submit/
    body: {"username": "Mert", "score": 25}
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required", "message": "POST metodu gerekli"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON", "message": "Geçersiz JSON"}, status=400)

    username = (data.get("username") or "").strip()
    score_value = data.get("score")

    # Basit validasyon
    if not username:
        return JsonResponse({"ok": False, "error": "username_required", "message": "Kullanıcı adı gerekli"}, status=400)

    try:
        score_value = int(score_value)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "invalid_score", "message": "Geçersiz skor"}, status=400)

    if score_value <= 0:
        return JsonResponse({"ok": False, "error": "score_must_be_positive", "message": "Skor pozitif olmalı"}, status=400)

    # Oyuncuyu bul / oluştur
    try:
        player, _created = Player.objects.get_or_create(username=username[:32])
    except Exception as e:
        return JsonResponse({"ok": False, "error": "player_creation_failed", "message": f"Oyuncu oluşturulamadı: {str(e)}"}, status=500)

    # Skoru kaydet
    try:
        Score.objects.create(player=player, value=score_value)
        return JsonResponse({"ok": True, "message": "Skor başarıyla kaydedildi"})
    except Exception as e:
        return JsonResponse({"ok": False, "error": "score_creation_failed", "message": f"Skor kaydedilemedi: {str(e)}"}, status=500)


def top_scores(request):
    """
    GET /api/score/top/?limit=10
    Her oyuncunun sadece en yüksek skorunu döndürür
    """
    try:
        limit = int(request.GET.get("limit", 10))
    except ValueError:
        limit = 10

    limit = max(1, min(limit, 50))  # 1–50 arası
    
    # Her oyuncunun en yüksek skorunu al
    from django.db.models import Max
    
    # Her oyuncu için en yüksek skor
    best_scores_per_player = (
        Score.objects
        .values('player__username')
        .annotate(best_score=Max('value'))
        .order_by('-best_score', 'player__username')
        [:limit]
    )
    
    # Her oyuncunun en yüksek skorunu içeren ilk kaydı al
    results = []
    for item in best_scores_per_player:
        username = item['player__username']
        best_score = item['best_score']
        
        # Bu skorun ilk kaydını al (tarih için)
        first_score = Score.objects.filter(
            player__username=username,
            value=best_score
        ).order_by('created_at').first()
        
        if first_score:
            results.append({
                "username": username,
                "score": best_score,
                "created": first_score.created_at.isoformat(timespec="seconds"),
            })

    return JsonResponse({"results": results})


@csrf_exempt
def register_user(request):
    """
    POST /api/auth/register/
    body: {"username": "test", "password": "123"}
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "message": "Invalid JSON"}, status=400)

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username:
        return JsonResponse({"ok": False, "message": "Kullanıcı adı girin"}, status=400)

    if not password:
        return JsonResponse({"ok": False, "message": "Şifre girin"}, status=400)

    if len(username) > 32:
        return JsonResponse({"ok": False, "message": "Kullanıcı adı çok uzun"}, status=400)

    # Kullanıcı adı kontrolü
    if Player.objects.filter(username=username).exists():
        return JsonResponse({"ok": False, "message": "Bu kullanıcı adı zaten kullanılıyor"}, status=400)

    # Yeni kullanıcı oluştur
    Player.objects.create(username=username, password=password)

    return JsonResponse({"ok": True, "message": "Kullanıcı başarıyla kaydedildi"})


@csrf_exempt
def login_user(request):
    """
    POST /api/auth/login/
    body: {"username": "test", "password": "123"}
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "message": "Invalid JSON"}, status=400)

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return JsonResponse({"ok": False, "message": "Kullanıcı adı ve şifre girin"}, status=400)

    try:
        player = Player.objects.get(username=username, password=password)
        return JsonResponse({"ok": True, "message": "Giriş başarılı"})
    except Player.DoesNotExist:
        return JsonResponse({"ok": False, "message": "Kullanıcı adı veya şifre hatalı"}, status=400)


@csrf_exempt
def get_profile(request):
    """
    GET /api/profile/?username=test
    veya
    POST /api/profile/
    body: {"username": "test"}
    """
    username = None
    
    if request.method == "GET":
        username = request.GET.get("username", "").strip()
    elif request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            username = (data.get("username") or "").strip()
        except json.JSONDecodeError:
            return JsonResponse({"ok": False, "message": "Invalid JSON"}, status=400)
    else:
        return JsonResponse({"error": "GET or POST required"}, status=405)

    if not username:
        return JsonResponse({"ok": False, "message": "Kullanıcı adı gerekli"}, status=400)

    try:
        player = Player.objects.get(username=username)
        
        # Son 10 skoru al
        recent_scores = list(
            player.scores.order_by("-created_at")[:10].values(
                "value", "created_at"
            )
        )
        
        # Tarihleri formatla
        for score in recent_scores:
            score["created_at"] = score["created_at"].isoformat(timespec="seconds")
        
        return JsonResponse({
            "ok": True,
            "profile": {
                "username": player.username,
                "avatar": player.avatar,
                "highest_score": player.get_highest_score(),
                "total_games": player.get_total_games(),
                "average_score": player.get_average_score(),
                "created_at": player.created_at.isoformat(timespec="seconds"),
                "recent_scores": recent_scores,
            }
        })
    except Player.DoesNotExist:
        return JsonResponse({"ok": False, "message": "Kullanıcı bulunamadı"}, status=404)


@csrf_exempt
def update_avatar(request):
    """
    POST /api/profile/avatar/
    body: {"username": "test", "avatar": "🐍"}
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "message": "Invalid JSON"}, status=400)

    username = (data.get("username") or "").strip()
    avatar = (data.get("avatar") or "🐍").strip()[:10]  # Max 10 karakter

    if not username:
        return JsonResponse({"ok": False, "message": "Kullanıcı adı gerekli"}, status=400)

    try:
        player = Player.objects.get(username=username)
        player.avatar = avatar
        player.save()
        return JsonResponse({"ok": True, "message": "Avatar güncellendi", "avatar": avatar})
    except Player.DoesNotExist:
        return JsonResponse({"ok": False, "message": "Kullanıcı bulunamadı"}, status=404)