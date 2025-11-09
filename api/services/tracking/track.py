import requests
from services.games.models import Platform

STEAM_KEY = "40414F4976621E15EBC72CD08991C04C"
STEAM_BASE_URL = "https://api.steampowered.com/"
STEAM_STATS_URL = "/ISteamUserStats/"

# All available stats for an instance
def stats_schema(instance):
    if instance.platform == Platform.objects.get(name="Steam"):
        # Fetch schema from Steam
        response = requests.get(f"{STEAM_BASE_URL}{STEAM_STATS_URL}GetSchemaForGame/v2?key={STEAM_KEY}&appid={instance.uid}")
        game_data = response.json().get('game', {})
        available_stats = game_data.get('availableGameStats', {}).get('stats', [])
        return [{'displayname': stat.get('displayName'), 'name': stat.get('name')} for stat in available_stats]

# Singular stat 
def stat_value(statv, account):

    if not account:
        return None

    if statv.stat.instance.platform == Platform.objects.get(name="Steam"):
        response = requests.get(f"{STEAM_BASE_URL}{STEAM_STATS_URL}GetUserStatsForGame/v2?key={STEAM_KEY}&appid={statv.stat.instance.uid}&steamid={account.uid}")
        stats = response.json().get('playerstats', {}).get('stats', [])
        stats_dict = {item['name']: item['value'] for item in stats}
        return float(stats_dict.get(statv.stat.name))

# All available stat values
def stat_values(instance, account):
    if not account:
        return None

    if instance.platform == Platform.objects.get(name="Steam"): 
        response = requests.get(f"{STEAM_BASE_URL}{STEAM_STATS_URL}GetUserStatsForGame/v2?key={STEAM_KEY}&appid={instance.uid}&steamid={account.uid}")
        stats = response.json().get('playerstats', {}).get('stats', [])
        return {item['name']: float(item['value']) for item in stats}

# Available achievements
def achievements_schema(instance):
    if instance.platform == Platform.objects.get(name="Steam"):
        response = requests.get(f"{STEAM_BASE_URL}{STEAM_STATS_URL}GetSchemaForGame/v2?key={STEAM_KEY}&appid={instance.uid}")
        game_data = response.json().get('game', {})
        available_achievements = game_data.get('availableGameStats', {}).get('achievements', [])
        return [{'name': ach.get('name'), 'displayname': ach.get('displayName'), 'icon': ach.get('icon')} for ach in available_achievements]

# Singular achievement status
def achievement_status(achv, account):

    if not account:
        return None

    if achv.instance.platform == Platform.objects.get(name="Steam"):
        response = requests.get(f"{STEAM_BASE_URL}{STEAM_STATS_URL}GetUserStatsForGame/v2?key={STEAM_KEY}&appid={achv.instance.uid}&steamid={account.uid}")
        achievements = response.json().get('playerstats', {}).get('achievements', [])
        achievement = next((item for item in achievements if item['name'] == achv.name), None)
        return bool(achievement.get('achieved')) if achievement else False

# All achievement statuses
def achievement_statuses(instance, account):

    if not account:
        return None

    if instance.platform == Platform.objects.get(name="Steam"):
        response = requests.get(f"{STEAM_BASE_URL}{STEAM_STATS_URL}GetUserStatsForGame/v2?key={STEAM_KEY}&appid={instance.uid}&steamid={account.uid}")
        achievements = response.json().get('playerstats', {}).get('achievements', [])
        return {item['name']: bool(item['achieved']) for item in achievements}
