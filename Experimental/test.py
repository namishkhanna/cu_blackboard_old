from datetime import datetime

today = datetime.now()
tempTime = datetime.strptime("3:30 PM", "%I:%M %p")
difference = tempTime - datetime.strptime(f"{today.time()}","%H:%M:%S.%f")

print(datetime.now().time())
print(difference.total_seconds())