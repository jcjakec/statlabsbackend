
from django.core.management.base import BaseCommand
import requests
from services.games.models import Platform, GameInstance
from services.users.models import Account, User


class Command(BaseCommand):
    help = 'test'

    def handle(self, *args, **kwargs):

        STEAM_KEY = "40414F4976621E15EBC72CD08991C04C"
        STEAM_BASE_URL = "https://api.steampowered.com/"
        STEAM_STATS_URL = "/ISteamUserStats/"
        mysteamid = "992698250"


        # All available stats for an instance
        def stat_schema(instance):
            if instance.platform == Platform.objects.get(name="Steam"):
                # Fetch schema from steam & append
                response = requests.get(STEAM_BASE_URL + STEAM_STATS_URL + f"GetSchemaForGame/v2?key={STEAM_KEY}&appid={instance.uid}")
                stats = response.json().get('game').get('availableGameStats').get('stats')
                stats = [stat.get('name') for stat in stats]
                return stats
                        

        # Singular stat 
        def stat_value(statv):
            account = Account.objects.all().filter(user=statv.user).filter(platform=statv.stat.instance.platform)[0]

            # STEAM
            if statv.stat.instance.platform == Platform.objects.get(name="Steam"):
                # Fetch stats from steam, select required value
                response = requests.get(STEAM_BASE_URL + STEAM_STATS_URL + f"GetUserStatsForGame/v2?key={STEAM_KEY}&appid={statv.stat.instance.uid}&steamid={account.uid}")
                stats = response.json().get('playerstats').get('stats')
                stats = {item['name']: item['value'] for item in stats}
                value = stats.get(statv.stat.name)
                return value


        # All available stat values
        def stat_values(instance, user):
            account = Account.objects.all().filter(user=user).filter(platform=instance.platform)[0]

            # STEAM
            if instance.platform == Platform.objects.get(name="Steam"): 
                response = requests.get(STEAM_BASE_URL + STEAM_STATS_URL + f"GetUserStatsForGame/v2?key={STEAM_KEY}&appid={instance.uid}&steamid={account.uid}")
                stats = response.json().get('playerstats', {}).get('stats', [])
                stats = {item['name']: item['value'] for item in stats}
                return stats



        # Available achievements
        def achievement_schema(instance):
            if instance.platform == Platform.objects.get(name="Steam"):
                # Fetch schema from steam & append
                response = requests.get(STEAM_BASE_URL + STEAM_STATS_URL + f"GetSchemaForGame/v2?key={STEAM_KEY}&appid={instance.uid}")
                achievements = response.json().get('game').get('availableGameStats').get('achievements')
                achievements = [{'name': ach.get('name'), 'displayname': ach.get('displayName'), 'icon': ach.get('icon')} for ach in achievements]
                return achievements
            
        # Singular achievement status
        def achievement_status(achv):
            account = Account.objects.all().filter(user=achv.user).filter(platform=achv.instance.platform)[0]

            # STEAM
            if achv.instance.platform == Platform.objects.get(name="Steam"):
                # Fetch stats from steam, select required value
                response = requests.get(STEAM_BASE_URL + STEAM_STATS_URL + f"GetUserStatsForGame/v2?key={STEAM_KEY}&appid={achv.instance.uid}&steamid={account.uid}")
                achievements = response.json().get('playerstats').get('achievements')
                status = bool(achievements.get(achv.name).get('achieved'))
                return achievements
            
        # All achievement statuses
        def achievement_status(instance, user):
            account = Account.objects.all().filter(user=user).filter(platform=instance.platform)[0]

            # STEAM
            if instance.platform == Platform.objects.get(name="Steam"):
                # Fetch stats from steam, select required value
                response = requests.get(STEAM_BASE_URL + STEAM_STATS_URL + f"GetUserStatsForGame/v2?key={STEAM_KEY}&appid={instance.uid}&steamid={account.uid}")
                achievements = response.json().get('playerstats').get('achievements')
                achievements = {item['name']: bool(item['achieved']) for item in achievements}
                return achievements
            

        print(achievement_status(GameInstance.objects.get(uid=730), User.objects.get(id=1)))