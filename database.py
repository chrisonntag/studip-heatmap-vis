from peewee import *
import datetime


db = SqliteDatabase('heatmap_database.db')


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    username = CharField(unique=True)
    key = UUIDField(unique=True)
    points = IntegerField()
    rank = IntegerField()


class DayAction(BaseModel):
    user = ForeignKeyField(User, backref='actions')
    actions = IntegerField()
    date = DateTimeField(default=datetime.datetime.now)


def create_tables():
    with db:
        db.create_tables([User, DayAction])



def get_user(username):
    return None

def register(username, key):
    return True

