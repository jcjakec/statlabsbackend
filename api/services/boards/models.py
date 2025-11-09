from django.db import models
from services.games.models import Game, Platform, GameInstance
from services.users.models import User
from services.tracking.models import Stat, StatValue, Achievement, AchievementStatus, InstanceCompletion
from django.utils.timezone import now as tznow
from datetime import timedelta
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction


# Stat Boards
class StatBoard(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="statboards")
    name = models.CharField(max_length=550)
    statname = models.CharField(max_length=255)
    stats = models.ManyToManyField(Stat, related_name="statboards", blank=True)
    refresh = models.DateTimeField(default=tznow, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)  

    def join(self, user, platform, password=None):
        if self.password and not check_password(password, self.password):
            return False  

        if platform not in [stat.instance.platform for stat in self.stats.all()]:
            return False 

        player, created = StatBoardPlayer.objects.get_or_create(board=self, user=user, platform=platform)
        return created  

    def leave(self, user):
        return StatBoardPlayer.objects.filter(board=self, user=user).delete()[0] > 0 

    def expired(self):
        return self.refresh < tznow()  

    def update(self):
        self.refresh = tznow() + timedelta(minutes=15)  

        players = StatBoardPlayer.objects.filter(board=self)
        for player in players:
            for stat in self.stats.all():
                if player.platform == stat.instance.platform:
                    statv, created = StatValue.objects.get_or_create(stat=stat, user=player.user)
                    statv.update() 
        self.save()

    def __str__(self):
        return f"{self.name} - ({self.game.name}): {[stat.instance.platform.name for stat in self.stats.all()]}"

    @classmethod
    def create(cls, name, game, statname, stats, password=None):
        hashed_password = make_password(password) if password else None
        board = cls.objects.create(
            name=name,
            game=game,
            statname=statname,
            password=hashed_password,
        )

        valid_stats = [stat for stat in stats if isinstance(stat, Stat)]
        if not valid_stats:
            board.delete()
            return None

        board.stats.add(*valid_stats) 
        board.update()
        
        return board



# Stat Board player and the platform they joined on
class StatBoardPlayer(models.Model):
    board = models.ForeignKey(StatBoard, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("board", "user")  

    def __str__(self):
        return f"For {self.board.name}, {self.user.username} joined on {self.platform.name}"




# Achievement Boards
class AchievementBoard(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="achievementboards")
    name = models.CharField(max_length=550)
    achievements = models.ManyToManyField(Achievement, related_name="achievementboards", blank=True)
    refresh = models.DateTimeField(default=tznow, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)  

    def join(self, user, platform, password=None):
        if self.password and not check_password(password, self.password):
            return False  

        if platform not in [ach.instance.platform for ach in self.achievements.all()]:
            return False  

        with transaction.atomic():
            player, created = AchievementBoardPlayer.objects.get_or_create(board=self, user=user, platform=platform)
            return created  

    def leave(self, user):
        return AchievementBoardPlayer.objects.filter(board=self, user=user).delete()[0] > 0 

    def expired(self):
        return self.refresh < tznow() 
    
    def update(self):
        self.refresh = tznow() + timedelta(minutes=15)  

        with transaction.atomic():
            self.save()

            players = AchievementBoardPlayer.objects.filter(board=self)
            for player in players:
                for achievement in self.achievements.all():
                    if player.platform == achievement.instance.platform:
                        status, created = AchievementStatus.objects.get_or_create(achievement=achievement, user=player.user)
                        status.update()

    def __str__(self):
        return f"{self.name} - ({self.game.name}): {[ach.instance.platform.name for ach in self.achievements.all()]}"

    @classmethod
    def create(cls, name, game, achievements, password=None):
        hashed_password = make_password(password) if password else None
        board = cls.objects.create(
            name=name,
            game=game,
            password=hashed_password,
        )

        valid_achs = [ach for ach in achievements if isinstance(ach, Achievement)]
        if not valid_achs:
            board.delete()
            return None

        board.achievements.add(*valid_achs) 
        board.update()
        
        return board


# Player in the achievement board and the platform they have joined on
class AchievementBoardPlayer(models.Model):
    board = models.ForeignKey(AchievementBoard, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("board", "user")  

    def __str__(self):
        return f"For {self.board.name}, {self.user.username} joined on {self.platform.name}"


# Completion board
class CompletionBoard(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="completionboards")
    name = models.CharField(max_length=550)
    instances = models.ManyToManyField(GameInstance, related_name="completionboards", blank=True)
    refresh = models.DateTimeField(default=tznow, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)

    def join(self, user, platform, password=None):
        if self.password and not check_password(password, self.password):
            return False

        if not self.instances.filter(platform=platform).exists():
            return False

        player, created = CompletionBoardPlayer.objects.get_or_create(board=self, user=user, platform=platform)
        return created

    def leave(self, user):
        return CompletionBoardPlayer.objects.filter(board=self, user=user).delete()[0] > 0
    
    def expired(self):
        return self.refresh < tznow()

    def update(self):
        self.refresh = tznow() + timedelta(minutes=15)
        self.save()

        with transaction.atomic():
            for player in CompletionBoardPlayer.objects.filter(board=self):
                for instance in self.instances.filter(platform=player.platform):
                    comp, created = InstanceCompletion.objects.get_or_create(instance=instance, user=player.user)
                    comp.update()

    def __str__(self):
        return f"{self.name} - ({self.game.name}): {[instance.platform.name for instance in self.instances.all()]}"

    @classmethod
    def create(cls, name, game, instances, password=None):
        hashed_password = make_password(password) if password else None
        board = cls.objects.create(
            name=name,
            game=game,
            password=hashed_password,
        )

        if instances:
            valid_instances = [instance for instance in instances if isinstance(instance, GameInstance)]
            if valid_instances:
                board.instances.add(*valid_instances)

        board.update()
        return board
    

class CompletionBoardPlayer(models.Model):
    board = models.ForeignKey(CompletionBoard, on_delete=models.CASCADE, related_name="players")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("board", "user", "platform")

    def __str__(self):
        return f"For {self.board.name}, {self.user.username} joined on {self.platform.name}"
