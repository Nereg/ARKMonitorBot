-- phpMyAdmin SQL Dump
-- version 5.1.0
-- https://www.phpmyadmin.net/
--
-- Host: db
-- Generation Time: Apr 09, 2021 at 05:44 PM
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

--
-- Dumping data for table `commandsused`
--

INSERT INTO `commandsused` (`Id`, `Name`, `Uses`) VALUES
(1, 'info', 1),
(2, 'prefix', 1);

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
  `Data` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `servers`
--

CREATE TABLE `servers` (
  `Id` int NOT NULL,
  `Ip` text NOT NULL,
  `Port` int DEFAULT NULL,
  `Address` text CHARACTER SET utf8 COLLATE utf8_general_ci,
  `ServerObj` text NOT NULL,
  `PlayersObj` text NOT NULL,
  `LastOnline` int NOT NULL DEFAULT '1',
  `OfflineTrys` int NOT NULL DEFAULT '0'
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
  MODIFY `Id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

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
-- AUTO_INCREMENT for table `servers`
--
ALTER TABLE `servers`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `settings`
--
ALTER TABLE `settings`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
