from django.db import models, transaction
from services.games.models import GameInstance, Game
from services.users.models import User
from datetime import timedelta
from django.utils.timezone import now as tznow
from .track import stat_value, achievement_status

# Stat and its value for a user with updates
class Stat(models.Model):
    name = models.CharField(max_length=500)
    displayname = models.CharField(max_length=500, null=True, blank=True)
    instance = models.ForeignKey(GameInstance, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} for {self.instance.game.name} on {self.instance.platform.name}"
    

class StatValue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stat = models.ForeignKey(Stat, on_delete=models.CASCADE)
    value = models.FloatField(blank=True, null=True)
    refresh = models.DateTimeField(default=tznow, blank=True, null=True)

    def expired(self):
        return self.refresh < tznow()
    
    def update(self):
        with transaction.atomic():
            self.refresh = tznow() + timedelta(minutes=30)
            self.value = stat_value(self)
            self.save()

    def __str__(self):
        return f"{self.stat.name} for {self.user.username} on {self.stat.instance.game.name} on {self.stat.instance.platform.name}"


# Achievement and its value for a user with updates
class Achievement(models.Model):
    name = models.CharField(max_length=500)
    displayname = models.CharField(max_length=500, null=True, blank=True)
    instance = models.ForeignKey(GameInstance, on_delete=models.CASCADE)
    icon = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} for {self.instance.game.name} on {self.instance.platform.name}"


class AchievementStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    refresh = models.DateTimeField(default=tznow, blank=True, null=True)

    def expired(self):
        return self.refresh < tznow()
    
    def update(self):
        with transaction.atomic():
            self.refresh = tznow() + timedelta(minutes=30)
            self.status = achievement_status(self)
            self.save()


# Completion and its percentage for a user, updates if at least 50% of achievement statuses expired
class InstanceCompletion(models.Model):
    instance = models.ForeignKey(GameInstance, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    percentage = models.FloatField(default=0, blank=True, null=True)
    refresh = models.DateTimeField(default=tznow, blank=True, null=True)

    def expired(self):
        return self.refresh < tznow()
    
    def update(self):
        with transaction.atomic():
            self.refresh = tznow() + timedelta(minutes=30)

            available = Achievement.objects.filter(instance=self.instance)
            total_achievements = available.count()

            if total_achievements == 0:
                self.percentage = 0
                self.save()
                return

            expired_statuses = AchievementStatus.objects.filter(
                achievement__in=available, user=self.user, refresh__lt=tznow()
            )
            expired_count = expired_statuses.count()

            if expired_count > total_achievements / 2:
                for status in expired_statuses:
                    status.update()

            achieved_count = AchievementStatus.objects.filter(
                achievement__in=available, user=self.user, status=True
            ).count()

            self.percentage = (achieved_count / total_achievements) * 100
            self.save()

# Completion for a game accross instances
class GameCompletion(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    percentage = models.FloatField(default=0, blank=True, null=True)
    refresh = models.DateTimeField(default=tznow, blank=True, null=True)

    def expired(self):
        return self.refresh < tznow()

    def update(self):
        with transaction.atomic():
            instance_completions = InstanceCompletion.objects.filter(instance__game=self.game)
            if not instance_completions.exists():
                self.percentage = 0
                self.save()
                return

            total_percentage = sum([completion.percentage for completion in instance_completions])
            total_instances = instance_completions.count()

            self.percentage = total_percentage / total_instances
            self.refresh = tznow() + timedelta(minutes=30)
            self.save()

    def __str__(self):
        return f"{self.game.name} Completion: {self.percentage}%"