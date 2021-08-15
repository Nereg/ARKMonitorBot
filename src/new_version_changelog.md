MUST be cleared after pathnotes are released in discord !
Internal :
Added check for <> in ips
Added new //purgeServers command to reduce number os servers in DB
Added a check in sendToMe function is bot isn't ready (and won't send anything to me)
Tryig to use native C implementation of asyncio instead of nest_asyncio Python one
Updated requirements.txt and bot.sql 
Changed stripVersion to accept and work with bare names
Updated discord.py to 1.7.3
Fixed requirements conflicts
Altered server table definition:
```sql
ALTER TABLE `servers` ADD `Info` TEXT NOT NULL COMMENT 'Additional JSON info about server' AFTER `OfflineTrys`, ADD `LastUpdated` TIMESTAMP on update CURRENT_TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Timestamp that updates every time the record is updated' AFTER `Info`; 
ALTER TABLE `servers` CHANGE `Info` `Info` TEXT CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL DEFAULT ('{}') COMMENT 'Additional JSON info about server'; 
```
Altered notifications table definition:
```sql
ALTER TABLE `notifications` ADD `GuildId` BIGINT NOT NULL DEFAULT '0' COMMENT 'Discord guild id. ' AFTER `Data`; 
```
Now sendToMe is sending messages to a guild channel not in DM's
(thanks intents)
External :
#This is a comment (won't be included in discord patchnotes)
#Added !campfire command
#!campfire - just output campfire rates
#!campfire <meat count> - calculate how much time and fuel would you need to cooks so much meat or fish (yeah I know about different rates for mutton but I'm too lazy)
#!campfire <meat count> <campfire count> - same as above but now we have servial campfires so it would be faster

Added typing indicator to !ipfix command
Integrated !ipfix command into !server add command (it now can change game port for query port using steam API)
Added typing indicator to !server add command