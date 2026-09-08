/*
 Navicat Premium Dump SQL

 Source Server         : mac-mysql
 Source Server Type    : MySQL
 Source Server Version : 90600 (9.6.0)
 Source Host           : IP+端口
 Source Schema         : rili

 Target Server Type    : MySQL
 Target Server Version : 90600 (9.6.0)
 File Encoding         : 65001

 Date: 31/01/2026 13:07:11
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for hitokoto
-- ----------------------------
DROP TABLE IF EXISTS `hitokoto`;
CREATE TABLE `hitokoto` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `hitokoto` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `from` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Table structure for rlibiao
-- ----------------------------
DROP TABLE IF EXISTS `rlibiao`;
CREATE TABLE `rlibiao` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '几月几号 2026-01-01',
  `weekDay` tinyint unsigned NOT NULL COMMENT '周几',
  `lunarCalendar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '农历',
  `typeDes` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '节日',
  `type` tinyint unsigned NOT NULL COMMENT '上班还是休',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=311 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Table structure for today
-- ----------------------------
DROP TABLE IF EXISTS `today`;
CREATE TABLE `today` (
  `id` int NOT NULL AUTO_INCREMENT,
  `today` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '今天的日期是几号 2025-10-11',
  `typeDes` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '节日',
  `yearTips` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '乙巳[蛇]年',
  `weekDay` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '周几',
  `lunarCalendar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '今天的农历日期',
  `suit` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '黄历-宜',
  `avoid` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '黄历-忌',
  `uptime` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=435 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Table structure for weather
-- ----------------------------
DROP TABLE IF EXISTS `weather`;
CREATE TABLE `weather` (
  `id` int NOT NULL AUTO_INCREMENT,
  `weekDay` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '周几',
  `date` date DEFAULT NULL,
  `tempMin` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `iconDay` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `tempMax` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `temp` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `feelsLike` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `icon` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `textDay` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `text` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `windDir` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `windScale` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `humidity` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `obsTime` datetime DEFAULT NULL,
  `updateTime` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=54 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

SET FOREIGN_KEY_CHECKS = 1;
