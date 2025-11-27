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
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    username = (data.get("username") or "").strip()
    score_value = data.get("score")

    # Basit validasyon
    if not username:
        return JsonResponse({"error": "username_required"}, status=400)

    try:
        score_value = int(score_value)
    except (TypeError, ValueError):
        return JsonResponse({"error": "invalid_score"}, status=400)

    if score_value <= 0:
        return JsonResponse({"error": "score_must_be_positive"}, status=400)

    # Oyuncuyu bul / oluştur
    player, _created = Player.objects.get_or_create(username=username[:32])

    # Skoru kaydet
    Score.objects.create(player=player, value=score_value)

    return JsonResponse({"ok": True})


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