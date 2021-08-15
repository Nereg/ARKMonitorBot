-- phpMyAdmin SQL Dump
-- version 5.1.0
-- https://www.phpmyadmin.net/
--
-- Host: db
-- Generation Time: Aug 15, 2021 at 03:48 PM
-- Server version: 8.0.19
-- PHP Version: 7.4.16

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `bot`
--

-- --------------------------------------------------------

--
-- Table structure for table `automessages`
--

CREATE TABLE `automessages` (
  `Id` int NOT NULL,
  `DiscordChannelId` bigint NOT NULL,
  `DiscordMsgId` bigint NOT NULL,
  `ServerId` bigint NOT NULL,
  `Comment` text,
  `DiscordGuildId` bigint NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `commandsused`
--

CREATE TABLE `commandsused` (
  `Id` int NOT NULL,
  `Name` varchar(100) NOT NULL,
  `Uses` int NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `errors`
--

CREATE TABLE `errors` (
  `Id` int NOT NULL,
  `Error` text NOT NULL,
  `Time` bigint NOT NULL,
  `UserDiscordId` bigint NOT NULL,
  `ChannelDiscordId` bigint NOT NULL,
  `GuildDiscordId` bigint DEFAULT NULL,
  `Message` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `manager`
--

CREATE TABLE `manager` (
  `Id` int NOT NULL,
  `Type` int NOT NULL,
  `Data` varchar(9999) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` (
  `Id` int NOT NULL,
  `DiscordChannelId` bigint NOT NULL,
  `Type` int NOT NULL,
  `Sent` int NOT NULL,
  `ServersIds` text NOT NULL,
  `Data` text NOT NULL,
  `GuildId` bigint NOT NULL DEFAULT '0' COMMENT 'Discord guild id. '
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `officialServers`
--

CREATE TABLE `officialServers` (
  `Id` int NOT NULL,
  `Name` varchar(59) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `Ip` varchar(14) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `Query port` int DEFAULT NULL,
  `Port` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `servers`
--

CREATE TABLE `servers` (
  `Id` int NOT NULL COMMENT 'Id of a server. Auto invreases',
  `Ip` text CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'Ip of a server in format: IP:Query port',
  `Port` int DEFAULT NULL COMMENT 'Query port of a server',
  `Address` text CHARACTER SET utf8 COLLATE utf8_general_ci COMMENT 'Ip of a server',
  `ServerObj` text CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'JSON dump of server object. See: /src/classes.py:72',
  `PlayersObj` text CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'JSON dump of players object. See: /src/classes.py:268',
  `LastOnline` int NOT NULL DEFAULT '1' COMMENT '0 or 1 indicating if the server was online or not last time we checked it.',
  `OfflineTrys` int NOT NULL DEFAULT '0' COMMENT 'Counts how many attempts were made to reach server.',
  `Info` text CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL DEFAULT (_utf8mb4'{}') COMMENT 'Additional JSON info about server',
  `LastUpdated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Timestamp that updates every time the record is updated'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `settings`
--

CREATE TABLE `settings` (
  `Id` int NOT NULL,
  `GuildId` bigint NOT NULL,
  `Prefix` text CHARACTER SET utf8 COLLATE utf8_general_ci,
  `ServersId` text CHARACTER SET utf8 COLLATE utf8_general_ci,
  `Admins` text CHARACTER SET utf8 COLLATE utf8_general_ci,
  `Type` int NOT NULL,
  `Aliases` text CHARACTER SET utf8 COLLATE utf8_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `Id` int NOT NULL,
  `DiscordId` bigint NOT NULL,
  `RefreshToken` text NOT NULL,
  `Locale` text NOT NULL,
  `DiscordName` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `automessages`
--
ALTER TABLE `automessages`
  ADD PRIMARY KEY (`Id`);

--
-- Indexes for table `commandsused`
--
ALTER TABLE `commandsused`
  ADD PRIMARY KEY (`Id`),
  ADD UNIQUE KEY `Id` (`Name`);

--
-- Indexes for table `errors`
--
ALTER TABLE `errors`
  ADD PRIMARY KEY (`Id`);

--
-- Indexes for table `manager`
--
ALTER TABLE `manager`
  ADD PRIMARY KEY (`Id`);

--
-- Indexes for table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`Id`);

--
-- Indexes for table `officialServers`
--
ALTER TABLE `officialServers`
  ADD PRIMARY KEY (`Id`);

--
-- Indexes for table `servers`
--
ALTER TABLE `servers`
  ADD PRIMARY KEY (`Id`);

--
-- Indexes for table `settings`
--
ALTER TABLE `settings`
  ADD PRIMARY KEY (`Id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`Id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `automessages`
--
ALTER TABLE `automessages`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `commandsused`
--
ALTER TABLE `commandsused`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `errors`
--
ALTER TABLE `errors`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `manager`
--
ALTER TABLE `manager`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `notifications`
--
ALTER TABLE `notifications`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `officialServers`
--
ALTER TABLE `officialServers`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `servers`
--
ALTER TABLE `servers`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT COMMENT 'Id of a server. Auto invreases';

--
-- AUTO_INCREMENT for table `settings`
--
ALTER TABLE `settings`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
