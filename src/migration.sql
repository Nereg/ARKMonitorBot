-- DB Generation SQL script
-- Database: `bot`

--
-- Table `notifications`
--
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
SET time_zone = "+00:00";

-- Table structure for table `notifications`

CREATE TABLE `notifications` (`Id` int NOT NULL, `Type` int NOT NULL, `Data` text CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL, `Sent` int NOT NULL DEFAULT '0' ) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Indexes for table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`Id`);

--
-- AUTO_INCREMENT for table `notifications`
--
ALTER TABLE `notifications` MODIFY `Id` int NOT NULL AUTO_INCREMENT;



--
-- Table `errors`
--
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
SET time_zone = "+00:00";

--
-- Table structure for table `errors`
--

CREATE TABLE `errors` (`Id` int NOT NULL, `Error` text NOT NULL, `Time` bigint NOT NULL, `UserDiscordId` bigint NOT NULL, `ChannelDiscordId` bigint NOT NULL, `GuildDiscordId` bigint DEFAULT NULL, `Message` text NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Indexes for table `errors`
--

ALTER TABLE `errors` ADD PRIMARY KEY (`Id`);

--
-- AUTO_INCREMENT for table `errors`
--

ALTER TABLE `errors` MODIFY `Id` int NOT NULL AUTO_INCREMENT;




--
-- Table structure for table `servers`
--

CREATE TABLE `servers` (`Id` int NOT NULL, `Ip` text NOT NULL, `Port` int NOT NULL, `Address` text CHARACTER SET utf8 COLLATE utf8_general_ci, `ServerObj` text NOT NULL, `PlayersObj` text NOT NULL, `LastOnline` int NOT NULL DEFAULT '1', `OfflineTrys` int NOT NULL DEFAULT '0') ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Indexes for table `servers`
--

ALTER TABLE `servers` ADD PRIMARY KEY (`Id`);

--
-- AUTO_INCREMENT for table `servers`
--

ALTER TABLE `servers` MODIFY `Id` int NOT NULL AUTO_INCREMENT;




--
-- Table structure for table `settings`
--

CREATE TABLE `settings` (`Id` int NOT NULL, `GuildId` bigint NOT NULL, `Prefix` text CHARACTER SET utf8 COLLATE utf8_general_ci, `ServersId` text CHARACTER SET utf8 COLLATE utf8_general_ci, `Admins` text CHARACTER SET utf8 COLLATE utf8_general_ci, `Type` int NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Indexes for table `settings`
--

ALTER TABLE `settings` ADD PRIMARY KEY (`Id`);

--
-- AUTO_INCREMENT for table `settings`
--
ALTER TABLE `settings` MODIFY `Id` int NOT NULL AUTO_INCREMENT;



--
-- Table structure for table `users`
--

CREATE TABLE `users` (`Id` int NOT NULL, `Name` text NOT NULL, `DiscordId` int NOT NULL, `DiscordDMId` int NOT NULL, `Data` text NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Indexes for table `users`
--
ALTER TABLE `users` ADD PRIMARY KEY (`Id`);

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users` MODIFY `Id` int NOT NULL AUTO_INCREMENT;