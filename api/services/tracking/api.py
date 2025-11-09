from ninja import Router
from django.shortcuts import get_object_or_404
from utils.schemas import ErrorOut
from .schemas import (
    StatSchema, StatValueSchema, AchievementSchema, AchievementStatusSchema, 
    FullAchievementSchema, FullStatSchema, CompletionSchema,
)
from django.db.models import Avg, Count
from services.games.models import GameInstance, Game
from services.users.models import Account, User
from .models import Stat, StatValue, Achievement, AchievementStatus, InstanceCompletion, GameCompletion
from django.utils.timezone import now as tznow
from .track import stats_schema, stat_values, achievements_schema, achievement_statuses
from datetime import timedelta
from django.db import transaction

router = Router()



# STATS

# Schema - all stats
@router.get("/stats/{instance_id}", response={200: list[StatSchema], 404: ErrorOut})
def stat_schema(request, instance_id: int):
    instance = get_object_or_404(GameInstance, id=instance_id)
    stats = Stat.objects.filter(instance=instance)
    if stats.exists():
        return stats
    
    stats_data = stats_schema(instance)
    if not stats_data:
        return 404, {"message": "No stats available."}
    
    to_add = [Stat(instance=instance, name=stat['name'], displayname=stat['displayname']) for stat in stats_data]
    Stat.objects.bulk_create(to_add)
    return Stat.objects.filter(instance=instance)


# One stat
@router.get("/stat/{stat_id}", response={200: FullStatSchema, 404: ErrorOut})
def one_stat(request, stat_id: int):
    stat = get_object_or_404(Stat, id=stat_id)
    return stat


# All stat values
@router.get("/stats/{instance_id}/user/{user_id}", response={200: list[StatValueSchema], 400: ErrorOut, 404: ErrorOut})
def all_stat_values(request, instance_id: int, user_id: int):
    instance = get_object_or_404(GameInstance, id=instance_id)
    if user_id: 
        user = get_object_or_404(User, id=user_id)
    else:
        user = request.auth
    
    stats = Stat.objects.filter(instance=instance)
    if not stats.exists():
        return 404, {"message": "No stats available."}
    
    statvs = StatValue.objects.filter(stat__in=stats, user=user)
    
    account = Account.objects.filter(user=user, platform=instance.platform).first()
    if not account:
        return 400, {"message": "No linked account."}
    
    stats_data = stat_values(instance, account)
    
    missing = [StatValue(user=user, stat=stat, refresh=tznow()) for stat in stats if stat.id not in statvs.values_list('stat_id', flat=True)]
    StatValue.objects.bulk_create(missing)
    statvs = list(statvs) + missing
    
    toupdate = []
    for statv in statvs:
        if statv.expired():
            statv.refresh = tznow() + timedelta(minutes=30)
            statv.value = stats_data.get(statv.stat.name)
            toupdate.append(statv)
    
    StatValue.objects.bulk_update(toupdate, ['refresh', 'value'])
    return statvs


# One stat value    
@router.get("/stat/{stat_id}/user/{user_id}", response={200: StatValueSchema, 404: ErrorOut})
def one_stat_value(request, stat_id: int, user_id: int):
    if user_id: 
        user = get_object_or_404(User, id=user_id)
    else:
        user = request.auth
    statv = get_object_or_404(StatValue, stat=stat_id, user=user)
    return statv




# ACHIEVEMENTS

# Schema - all achievements
@router.get("/achievements/{instance_id}", response={200: list[AchievementSchema], 400: ErrorOut})
def achievement_schema(request, instance_id: int):
    instance = get_object_or_404(GameInstance, id=instance_id)
    achievements = Achievement.objects.filter(instance=instance)
    if achievements.exists():
        return achievements
    
    achievements_data = achievements_schema(instance)
    if not achievements_data:
        return 400, {"message": "No achievements available."}
    
    to_add = [Achievement(instance=instance, name=ach['name'], displayname=ach['displayname'], icon=ach['icon']) for ach in achievements_data]
    Achievement.objects.bulk_create(to_add)
    return Achievement.objects.filter(instance=instance)


# One achievement
@router.get("/achievement/{achievement_id}", response={200: FullAchievementSchema, 404: ErrorOut})
def one_achievement(request, achievement_id: int):
    achievement = get_object_or_404(Achievement, id=achievement_id)
    return achievement


# All achievement statuses
@router.get("/achievements/{instance_id}/user/{user_id}", response={200: list[AchievementStatusSchema], 400: ErrorOut, 404: ErrorOut})
def all_achievement_statuses(request, instance_id: int, user_id: int):
    instance = get_object_or_404(GameInstance, id=instance_id)
    if user_id: 
        user = get_object_or_404(User, id=user_id)
    else:
        user = request.auth
    
    achievements = Achievement.objects.filter(instance=instance)
    if not achievements.exists():
        return 404, {"message": "No achievements available."}
    
    achvs = AchievementStatus.objects.filter(achievement__in=achievements, user=user)
    
    account = Account.objects.filter(user=user, platform=instance.platform).first()
    if not account:
        return 400, {"message": "No linked account."}
    
    statuses = achievement_statuses(instance, account)
    
    missing = [AchievementStatus(user=user, achievement=ach, refresh=tznow()) for ach in achievements if ach.id not in achvs.values_list('achievement_id', flat=True)]
    AchievementStatus.objects.bulk_create(missing)
    achvs = list(achvs) + missing
    
    toupdate = []
    for achv in achvs:
        if achv.expired():
            achv.refresh = tznow() + timedelta(minutes=30)
            achv.status = statuses.get(achv.achievement.name, False)
            toupdate.append(achv)
    
    AchievementStatus.objects.bulk_update(toupdate, ['refresh', 'status'])
    return achvs

# One achievement status
@router.get("/achievement/{achievement_id}/user/{user_id}", response={200: AchievementStatusSchema, 404: ErrorOut})
def one_achievement_status(request, achievement_id: int, user_id: int):
    if user_id: 
        user = get_object_or_404(User, id=user_id)
    else:
        user = request.auth
    return get_object_or_404(AchievementStatus, user=user, achievement=achievement_id)



# COMPLETION

# Global completion percentage for instance
@router.get("/completion/{instance_id}", response={200: CompletionSchema, 404: ErrorOut})
def get_global_completion(request, instance_id: int):
    instance = get_object_or_404(GameInstance, id=instance_id)

    available_achievements = Achievement.objects.filter(instance=instance)
    total_achievements = available_achievements.count()

    if total_achievements == 0:
        return {"instance": instance.id, "percentage": 0.0} 

    total_achieved = AchievementStatus.objects.filter(
        achievement__in=available_achievements, status=True
    ).count()

    instance_count = InstanceCompletion.objects.filter(instance=instance).count() or 1 
    global_completion = (total_achieved / (total_achievements * instance_count)) * 100

    return 200, {"percentage": round(global_completion, 2)}

# Get a users completion value
@router.get("/completion/{instance_id}/user/{user_id}", response={200: CompletionSchema, 404: ErrorOut})
def get_user_completion(request, instance_id: int, user_id: int):
    instance = get_object_or_404(GameInstance, id=instance_id)
    if user_id: 
        user = get_object_or_404(User, id=user_id)
    else:
        user = request.auth
    completion = InstanceCompletion.objects.filter(instance=instance, user=user).first()

    if not completion or completion.expired():
        if not completion:
            completion = InstanceCompletion(instance=instance, user=user)
            with transaction.atomic():
                completion.save()
        completion.update()

    return 200, completion

# Game completion average across instances
@router.get("/completion/game/{game_id}", response={200: CompletionSchema, 404: ErrorOut})
def get_game_completion(request, game_id: int):
    game = get_object_or_404(Game, id=game_id)

    game_completion = GameCompletion.objects.filter(game=game).first()

    if not game_completion or game_completion.expired():
        if not game_completion:
            game_completion = GameCompletion(game=game)
            with transaction.atomic():
                game_completion.save()

        game_completion.update()

    return 200, game_completion