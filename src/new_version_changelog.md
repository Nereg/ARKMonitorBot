MUST be cleared after pathnotes are released in discord !
Internal :
Added check for <> in ips
Added new //purgeServers command to reduce number os servers in DB
Added a check in sendToMe function is bot isn't ready (and won't send anything to me)
Tryig to use native C implementation of asyncio instead of nest_asyncio Python one
Updated requirements.txt and bot.sql 
Changed stripVersion to accept and work with bare names
External :
#This is a comment (won't be included in discord patchnotes)
#Added !campfire command
#!campfire - just output campfire rates
#!campfire <meat count> - calculate how much time and fuel would you need to cooks so much meat or fish (yeah I know about different rates for mutton but I'm too lazy)
#!campfire <meat count> <campfire count> - same as above but now we have servial campfires so it would be faster

Added typing indicator to !ipfix command
