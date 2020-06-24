from helpers import *

def migrate():
  script = '''CREATE TABLE `notifications` (`Id` int NOT NULL, `Type` int NOT NULL, `Data` text CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL, `Sent` int NOT NULL DEFAULT '0' ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
ALTER TABLE `notifications` ADD PRIMARY KEY (`Id`);
ALTER TABLE `notifications` MODIFY `Id` int NOT NULL AUTO_INCREMENT;
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
SET time_zone = "+00:00";
CREATE TABLE `errors` (`Id` int NOT NULL, `Error` text NOT NULL, `Time` bigint NOT NULL, `UserDiscordId` bigint NOT NULL, `ChannelDiscordId` bigint NOT NULL, `GuildDiscordId` bigint DEFAULT NULL, `Message` text NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8;
ALTER TABLE `errors` ADD PRIMARY KEY (`Id`);
ALTER TABLE `errors` MODIFY `Id` int NOT NULL AUTO_INCREMENT;
CREATE TABLE `servers` (`Id` int NOT NULL, `Ip` text NOT NULL, `Port` int NOT NULL, `Address` text CHARACTER SET utf8 COLLATE utf8_general_ci, `ServerObj` text NOT NULL, `PlayersObj` text NOT NULL, `LastOnline` int NOT NULL DEFAULT '1', `OfflineTrys` int NOT NULL DEFAULT '0') ENGINE=InnoDB DEFAULT CHARSET=utf8;
ALTER TABLE `servers` ADD PRIMARY KEY (`Id`);
ALTER TABLE `servers` MODIFY `Id` int NOT NULL AUTO_INCREMENT;
CREATE TABLE `settings` (`Id` int NOT NULL, `GuildId` bigint NOT NULL, `Prefix` text CHARACTER SET utf8 COLLATE utf8_general_ci, `ServersId` text CHARACTER SET utf8 COLLATE utf8_general_ci, `Admins` text CHARACTER SET utf8 COLLATE utf8_general_ci, `Type` int NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8;
ALTER TABLE `settings` ADD PRIMARY KEY (`Id`);
ALTER TABLE `settings` MODIFY `Id` int NOT NULL AUTO_INCREMENT;
CREATE TABLE `users` (`Id` int NOT NULL, `Name` text NOT NULL, `DiscordId` int NOT NULL, `DiscordDMId` int NOT NULL, `Data` text NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8;
ALTER TABLE `users` ADD PRIMARY KEY (`Id`);
ALTER TABLE `users` MODIFY `Id` int NOT NULL AUTO_INCREMENT;'''

  for line in script:
    if '--' in line: 
      return
    else:
	    makeRequest(line)
