MUST be cleared after pathnotes are released in discord !
Internal :
patched asyncio loop to accept new loops to run async code in !repl command
patched updater to use aiomysql pool but no spped increase (will test on production)
MUCH MUCH faster updater! (Finally!!)
Added BattleMetricsAPI class (useless if honest)
Added updateOffline method to ARKServer class
Removed discord-ext-menus 
Rewrote huge part of !server info command
Added comments to the code
Fixed rare (very) bug in /setMessage command (admin cog)

External :
Added !campfire command
!campfire - just output campfire rates
!campfire <meat count> - calculate how much time and fuel would you need to cooks so much meat or fish (yeah I know about different rates for mutton but I'm too lazy)
!campfire <meat count> <campfire count> - same as above but now we have servial campfires so it would be faster
Reworked !server info command to use embeds
Added battlemetrics url to embed in !server info command