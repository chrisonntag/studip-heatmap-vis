from peewee import *
import datetime


DATABASE = SqliteDatabase('heatmap_database.db')


class BaseModel(Model):
    class Meta:
        database = DATABASE


class User(BaseModel):
    username = CharField(unique=True)
    key = UUIDField(unique=True)
    points = IntegerField(null=True)
    rank = IntegerField(null=True)


class DayAction(BaseModel):
    user = ForeignKeyField(User, backref='actions')
    actions = IntegerField()
    date = DateField(default=datetime.date.today())


def create_tables():
    with DATABASE:
        DATABASE.create_tables([User, DayAction])


def user_exists(username, key):
    try:
        user = User.get(User.username == username, User.key == key)
    except User.DoesNotExist:
        return False

    return True


def create_user(username, key, points, rank):
    try:
        with DATABASE.atomic():
            # Attempt to create the user. If the username is taken, due to the
            # unique constraint, the database will raise an IntegrityError.
            user = User.create(
                username=username,
                key=key,
                points=points,
                rank=rank)
    except IntegrityError:
        raise IntegrityError


def create_dayaction(username, actions):
    try:
        with DATABASE.atomic():
            # Attempt to create the user. If the username is taken, due to the
            # unique constraint, the database will raise an IntegrityError.
            user = User.get(User.username == username)
            dayaction = DayAction.create(
                user=user,
                actions=actions)
    except User.DoesNotExist:
        return False

    return True


