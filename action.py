import math
import datetime
import database as db
from database import User, DayAction
from studip import get_points

def calc_action_number(current_points, previous_points):
    gained = current_points - previous_points

    if gained >= 100:
        vals = [(1/(2**n))*100 for n in range(0, 12)]
        for i in range(1, len(vals)):
            vals[i] = vals[i] + vals[i-1]

        index = 0
        for i in range(0, len(vals)):
            if gained >= vals[i]:
                index = i

        first = math.fabs(gained - vals[index])
        second = math.fabs(gained - vals[index+1])

        if first < second:
            return index + 1
        else:
            return index + 2
    else:
        return 0


if __name__ == '__main__':
    db.DATABASE.connect()

    for user in User.select():
        points = user.points
        new_points = get_points(user.username)
        if points is not None and new_points is not None and new_points > 0:
            actions = calc_action_number(new_points, points)

            dayaction, created = DayAction.get_or_create(user=user, date=datetime.date.today())
            dayaction.actions += actions
            dayaction.save()

            user.points = new_points
            user.save()

    db.DATABASE.close()

