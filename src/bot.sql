-- phpMyAdmin SQL Dump
-- version 5.0.1
-- https://www.phpmyadmin.net/
--
-- Host: mysql-server
-- Generation Time: Jun 23, 2020 at 07:09 PM
-- Server version: 8.0.19
-- PHP Version: 7.4.1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
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
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` ( `Id` INT NOT NULL AUTO_INCREMENT , `DiscordChannelId` BIGINT NOT NULL , `Type` INT NOT NULL , `Sent` INT NOT NULL , `ServersIds` TEXT NOT NULL , `Data` TEXT NOT NULL , PRIMARY KEY (`Id`)) ENGINE = InnoDB; 

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

-- --------------------------------------------------------

--
-- Table structure for table `users`
--
DROP TABLE users;
CREATE TABLE `bot`.`users` ( `Id` INT NOT NULL AUTO_INCREMENT , `DiscordId` BIGINT NOT NULL , `RefreshToken` TEXT NOT NULL , `Locale` TEXT NOT NULL , `DiscordName` TEXT NOT NULL , PRIMARY KEY (`Id`)) ENGINE = InnoDB;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `errors`
--
ALTER TABLE `errors`
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
-- AUTO_INCREMENT for table `errors`
--
ALTER TABLE `errors`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT;
COMMIT;
--
-- AUTO_INCREMENT for table `servers`
--
ALTER TABLE `servers`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT;
COMMIT;
--
-- AUTO_INCREMENT for table `settings`
--
ALTER TABLE `settings`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT;
COMMIT;
--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `Id` int NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
