* !watch command
1. Select server using selector (done)
2. Check if that user already get notifications about this server
2a. If user already get notifications tell him about that and suggest how to unsubscribe form getting notifications
3. Record server ARK id , discord channel id, language , and type of notification to DB
4. Tell user that we are done!
* Notifications types
1. Server went online
2. server went offline
3. Server went online/offline
...
* DB fields
1. Id 
2. DiscordChannelId - id of discord channel id (also wiil be used insted of user id to deturmen if user is already reciving notifications about this server)
3. ServersIds - json list of servers ids
4. Data - json string will be used for additional data for future types of notifications
5. Language - string containig language code of prefered language to deliver notifications on
6. Delivered - bool (0 or 1) must be set to 1 when notification delivered and wiil be resetted to 0 after some time (will be implemented in updater.py) 
* updater.py logic
1. Start loop
2. Start instanse of bot
3. For every server in DB:
3a. Get IP and if anyone is getting notifications about this server
3b. Try to get information
3ba. If failed set LastOnline field in DB to 0 and offlineTrys to += 1 also set local variable wentOflline to true
3bb. If successed get information into DB and if lastOnline field were 0 set local variable wentOnline to true 
3c. Check wentOnline/offline variable 
3d. Read 