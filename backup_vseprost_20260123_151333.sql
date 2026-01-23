-- MySQL Backup
-- Database: vseprost
-- Date: 2026-01-23 15:13:33
-- Host: localhost:3306

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS=0;

DROP DATABASE IF EXISTS `vseprost`;
CREATE DATABASE `vseprost` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `vseprost`;


-- Структура таблицы `category`
DROP TABLE IF EXISTS `category`;
CREATE TABLE `category` (
  `id` int NOT NULL AUTO_INCREMENT,
  `isnew` tinyint(1) DEFAULT '1',
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `modified_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `creator` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `creator` (`creator`),
  CONSTRAINT `category_ibfk_1` FOREIGN KEY (`creator`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Категории проблем';

-- Данные таблицы `category`
LOCK TABLES `category` WRITE;
INSERT INTO `category` (`id`, `isnew`, `name`, `modified_date`, `created_date`, `creator`) VALUES (1, 0, 'Ребенок', '2024-02-01 13:09:00', '2025-07-09 12:09:00', 1);
INSERT INTO `category` (`id`, `isnew`, `name`, `modified_date`, `created_date`, `creator`) VALUES (2, 0, 'Сон', '2024-02-01 13:09:00', '2025-07-09 12:09:00', 1);
INSERT INTO `category` (`id`, `isnew`, `name`, `modified_date`, `created_date`, `creator`) VALUES (3, 0, 'Еда', '2025-02-22 14:27:00', '2025-07-09 12:09:00', 1);
INSERT INTO `category` (`id`, `isnew`, `name`, `modified_date`, `created_date`, `creator`) VALUES (4, 0, 'Здоровье', '2024-02-28 13:09:00', '2025-07-09 12:09:00', 1);
INSERT INTO `category` (`id`, `isnew`, `name`, `modified_date`, `created_date`, `creator`) VALUES (5, 0, 'Работа', '2024-05-23 13:09:00', '2025-07-09 12:09:00', 1);
INSERT INTO `category` (`id`, `isnew`, `name`, `modified_date`, `created_date`, `creator`) VALUES (6, 0, 'Красота', '2024-05-23 13:09:00', '2025-07-09 12:09:00', 1);
INSERT INTO `category` (`id`, `isnew`, `name`, `modified_date`, `created_date`, `creator`) VALUES (7, 0, 'Спорт', '2024-05-23 13:09:00', '2025-07-09 12:09:00', 1);
INSERT INTO `category` (`id`, `isnew`, `name`, `modified_date`, `created_date`, `creator`) VALUES (8, 0, 'Дом', '2024-06-03 13:09:00', '2025-07-09 12:09:00', 1);
INSERT INTO `category` (`id`, `isnew`, `name`, `modified_date`, `created_date`, `creator`) VALUES (9, 0, 'Техника', '2024-07-08 13:09:00', '2025-07-09 12:09:00', 1);
INSERT INTO `category` (`id`, `isnew`, `name`, `modified_date`, `created_date`, `creator`) VALUES (30, 1, 'Ёмка', '2025-10-09 14:23:01', '2025-10-09 14:23:01', 16);
UNLOCK TABLES;


-- Структура таблицы `comment_solution`
DROP TABLE IF EXISTS `comment_solution`;
CREATE TABLE `comment_solution` (
  `id` int NOT NULL AUTO_INCREMENT,
  `isnew` tinyint(1) DEFAULT '1',
  `likecount` int DEFAULT '0',
  `notlikecount` int DEFAULT '0',
  `solution_id` int NOT NULL,
  `text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `creator` int NOT NULL,
  `modified_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `solution_id` (`solution_id`),
  KEY `creator` (`creator`),
  CONSTRAINT `comment_solution_ibfk_1` FOREIGN KEY (`solution_id`) REFERENCES `solution` (`id`),
  CONSTRAINT `comment_solution_ibfk_2` FOREIGN KEY (`creator`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Структура таблицы `commentsolution`
DROP TABLE IF EXISTS `commentsolution`;
CREATE TABLE `commentsolution` (
  `id` int NOT NULL AUTO_INCREMENT,
  `isnew` tinyint(1) DEFAULT '1',
  `likecount` int DEFAULT '0',
  `notlikecount` int DEFAULT '0',
  `solution_id` int NOT NULL,
  `text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `creator` int NOT NULL,
  `modified_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `solution_id` (`solution_id`),
  KEY `creator` (`creator`),
  CONSTRAINT `commentsolution_ibfk_1` FOREIGN KEY (`solution_id`) REFERENCES `solution` (`id`),
  CONSTRAINT `commentsolution_ibfk_2` FOREIGN KEY (`creator`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Структура таблицы `favourite_problem`
DROP TABLE IF EXISTS `favourite_problem`;
CREATE TABLE `favourite_problem` (
  `problem_id` int NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`problem_id`,`user_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `favourite_problem_ibfk_1` FOREIGN KEY (`problem_id`) REFERENCES `problem` (`id`) ON DELETE CASCADE,
  CONSTRAINT `favourite_problem_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Данные таблицы `favourite_problem`
LOCK TABLES `favourite_problem` WRITE;
INSERT INTO `favourite_problem` (`problem_id`, `user_id`) VALUES (10, 1);
UNLOCK TABLES;


-- Структура таблицы `favourite_solution`
DROP TABLE IF EXISTS `favourite_solution`;
CREATE TABLE `favourite_solution` (
  `solution_id` int NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`solution_id`,`user_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `favourite_solution_ibfk_1` FOREIGN KEY (`solution_id`) REFERENCES `solution` (`id`) ON DELETE CASCADE,
  CONSTRAINT `favourite_solution_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Данные таблицы `favourite_solution`
LOCK TABLES `favourite_solution` WRITE;
INSERT INTO `favourite_solution` (`solution_id`, `user_id`) VALUES (3, 1);
UNLOCK TABLES;


-- Структура таблицы `hashtag`
DROP TABLE IF EXISTS `hashtag`;
CREATE TABLE `hashtag` (
  `id` int NOT NULL AUTO_INCREMENT,
  `isnew` tinyint(1) DEFAULT '1',
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `show` int DEFAULT '0',
  `creator` int NOT NULL,
  `modified_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `creator` (`creator`),
  CONSTRAINT `hashtag_ibfk_1` FOREIGN KEY (`creator`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Хэштеги для тегов';

-- Данные таблицы `hashtag`
LOCK TABLES `hashtag` WRITE;
INSERT INTO `hashtag` (`id`, `isnew`, `name`, `show`, `creator`, `modified_date`, `created_date`) VALUES (2, 0, 'ребенок', 0, 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00');
INSERT INTO `hashtag` (`id`, `isnew`, `name`, `show`, `creator`, `modified_date`, `created_date`) VALUES (3, 0, 'сон', 0, 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00');
INSERT INTO `hashtag` (`id`, `isnew`, `name`, `show`, `creator`, `modified_date`, `created_date`) VALUES (4, 0, 'продукт', 0, 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00');
INSERT INTO `hashtag` (`id`, `isnew`, `name`, `show`, `creator`, `modified_date`, `created_date`) VALUES (5, 0, 'мозг', 0, 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00');
INSERT INTO `hashtag` (`id`, `isnew`, `name`, `show`, `creator`, `modified_date`, `created_date`) VALUES (6, 0, 'Акне', 0, 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00');
INSERT INTO `hashtag` (`id`, `isnew`, `name`, `show`, `creator`, `modified_date`, `created_date`) VALUES (7, 1, 'Лицо', 0, 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00');
INSERT INTO `hashtag` (`id`, `isnew`, `name`, `show`, `creator`, `modified_date`, `created_date`) VALUES (8, 1, 'коллаген', 0, 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00');
INSERT INTO `hashtag` (`id`, `isnew`, `name`, `show`, `creator`, `modified_date`, `created_date`) VALUES (9, 1, 'косметика', 0, 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00');
INSERT INTO `hashtag` (`id`, `isnew`, `name`, `show`, `creator`, `modified_date`, `created_date`) VALUES (10, 1, 'упражнения', 0, 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00');
INSERT INTO `hashtag` (`id`, `isnew`, `name`, `show`, `creator`, `modified_date`, `created_date`) VALUES (11, 1, 'депрессия', 0, 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00');
INSERT INTO `hashtag` (`id`, `isnew`, `name`, `show`, `creator`, `modified_date`, `created_date`) VALUES (12, 0, 'ghdfhfgh', 0, 16, '0000-00-00 00:00:00', '0000-00-00 00:00:00');
INSERT INTO `hashtag` (`id`, `isnew`, `name`, `show`, `creator`, `modified_date`, `created_date`) VALUES (13, 0, 'варвар', 0, 16, '0000-00-00 00:00:00', '0000-00-00 00:00:00');
INSERT INTO `hashtag` (`id`, `isnew`, `name`, `show`, `creator`, `modified_date`, `created_date`) VALUES (14, 0, 'апрвар', 0, 16, '0000-00-00 00:00:00', '0000-00-00 00:00:00');
UNLOCK TABLES;


-- Структура таблицы `hashtag_problem`
DROP TABLE IF EXISTS `hashtag_problem`;
CREATE TABLE `hashtag_problem` (
  `problem_id` int NOT NULL,
  `hashtag_id` int NOT NULL,
  PRIMARY KEY (`problem_id`,`hashtag_id`),
  KEY `hashtag_id` (`hashtag_id`),
  CONSTRAINT `hashtag_problem_ibfk_1` FOREIGN KEY (`problem_id`) REFERENCES `problem` (`id`) ON DELETE CASCADE,
  CONSTRAINT `hashtag_problem_ibfk_2` FOREIGN KEY (`hashtag_id`) REFERENCES `hashtag` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Данные таблицы `hashtag_problem`
LOCK TABLES `hashtag_problem` WRITE;
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (8, 2);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (12, 2);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (13, 2);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (14, 2);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (8, 3);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (12, 3);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (13, 3);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (8, 4);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (11, 4);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (12, 4);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (13, 4);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (15, 4);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (11, 5);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (11, 6);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (9, 7);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (9, 8);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (10, 8);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (15, 8);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (9, 9);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (10, 9);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (10, 10);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (8, 11);
INSERT INTO `hashtag_problem` (`problem_id`, `hashtag_id`) VALUES (12, 11);
UNLOCK TABLES;


-- Структура таблицы `problem`
DROP TABLE IF EXISTS `problem`;
CREATE TABLE `problem` (
  `id` int NOT NULL AUTO_INCREMENT,
  `category` int NOT NULL,
  `describe` text COLLATE utf8mb4_unicode_ci,
  `favourite` int DEFAULT '0',
  `fromauthor` tinyint(1) DEFAULT '0',
  `isnew` tinyint(1) DEFAULT '1',
  `creator` int NOT NULL,
  `modified_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `image` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `reply` int DEFAULT NULL,
  `show` int DEFAULT NULL,
  `topic` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `category` (`category`),
  KEY `creator` (`creator`),
  KEY `topic` (`topic`),
  CONSTRAINT `problem_ibfk_1` FOREIGN KEY (`category`) REFERENCES `category` (`id`),
  CONSTRAINT `problem_ibfk_2` FOREIGN KEY (`creator`) REFERENCES `user` (`id`),
  CONSTRAINT `problem_ibfk_3` FOREIGN KEY (`topic`) REFERENCES `topic` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Данные таблицы `problem`
LOCK TABLES `problem` WRITE;
INSERT INTO `problem` (`id`, `category`, `describe`, `favourite`, `fromauthor`, `isnew`, `creator`, `modified_date`, `created_date`, `image`, `name`, `reply`, `show`, `topic`) VALUES (8, 1, NULL, 2, 1, 0, 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00', 'https://storage.yandexcloud.net/problem/1662812101_a.jpg', 'Как повысить работоспособность мозга', 15, 298, 1);
INSERT INTO `problem` (`id`, `category`, `describe`, `favourite`, `fromauthor`, `isnew`, `creator`, `modified_date`, `created_date`, `image`, `name`, `reply`, `show`, `topic`) VALUES (9, 2, 'Медленно', 1, 1, 0, 1, '2026-01-07 00:34:45', '2024-02-01 13:09:00', 'https://storage.yandexcloud.net/problem/460ponyatie_novorojdenny_y_rebenok_predlagaetsya_zakrepit__na_zakonodatel_nom_urovne.jpg', 'Как чистить картошку', 15, 300, 1);
INSERT INTO `problem` (`id`, `category`, `describe`, `favourite`, `fromauthor`, `isnew`, `creator`, `modified_date`, `created_date`, `image`, `name`, `reply`, `show`, `topic`) VALUES (10, 3, 'На какие активные вещества смотреть в составе кремов и других препаратах от акне', 2, 1, 0, 1, '2026-01-07 01:24:30', '2024-02-01 13:09:00', 'https://storage.yandexcloud.net/problem/728x546_1_b03ebb12cefeddcab14c23fccf5e83b6%401706x1280_0xac120003_20080148761652287650.jpeg', 'Какие активные вещества помогают от акне', 15, 327, 1);
INSERT INTO `problem` (`id`, `category`, `describe`, `favourite`, `fromauthor`, `isnew`, `creator`, `modified_date`, `created_date`, `image`, `name`, `reply`, `show`, `topic`) VALUES (11, 2, NULL, 1, 1, 0, 1, '2026-01-06 23:02:27', '2024-02-01 13:09:00', 'https://storage.yandexcloud.net/problem/Big_e4b3324181424fd178949e2f6a262c.0%20(1).jpg', '234', 15, 299, 1);
INSERT INTO `problem` (`id`, `category`, `describe`, `favourite`, `fromauthor`, `isnew`, `creator`, `modified_date`, `created_date`, `image`, `name`, `reply`, `show`, `topic`) VALUES (12, 4, NULL, 1, 1, 0, 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00', 'https://storage.yandexcloud.net/problem/COVWsT5mdTpe1ebtvs9cF7aKeSOaG3q2t7Mckdnl-preview_3_2.jpg', 'Какие продукты употреблять для повышения коллагена в организме', 15, 298, 1);
INSERT INTO `problem` (`id`, `category`, `describe`, `favourite`, `fromauthor`, `isnew`, `creator`, `modified_date`, `created_date`, `image`, `name`, `reply`, `show`, `topic`) VALUES (13, 5, NULL, 1, 1, 0, 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00', 'https://storage.yandexcloud.net/problem/be3c0f86.jpg', 'Какие средства использовать для повышения коллагена в организме', 15, 298, 1);
INSERT INTO `problem` (`id`, `category`, `describe`, `favourite`, `fromauthor`, `isnew`, `creator`, `modified_date`, `created_date`, `image`, `name`, `reply`, `show`, `topic`) VALUES (14, 2, 'Продукты, которые помогают при депрессии', 1, 1, 0, 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00', 'https://storage.yandexcloud.net/problem/d629cac6a4dbb436c2d8018c7d7938eb.jpg', 'Продукты помогающие от депрессии', 15, 298, 1);
INSERT INTO `problem` (`id`, `category`, `describe`, `favourite`, `fromauthor`, `isnew`, `creator`, `modified_date`, `created_date`, `image`, `name`, `reply`, `show`, `topic`) VALUES (15, 3, NULL, 1, 1, 0, 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00', 'https://storage.yandexcloud.net/problem/e7a19efb990c73f03582fc58c3866b14.jpeg', 'Как повысить коллаген упражнениями', 15, 298, 1);
UNLOCK TABLES;


-- Структура таблицы `problem_link_problem`
DROP TABLE IF EXISTS `problem_link_problem`;
CREATE TABLE `problem_link_problem` (
  `problem_id` int NOT NULL,
  `problem_link_id` int NOT NULL,
  PRIMARY KEY (`problem_id`,`problem_link_id`),
  KEY `problem_link_id` (`problem_link_id`),
  CONSTRAINT `problem_link_problem_ibfk_1` FOREIGN KEY (`problem_id`) REFERENCES `problem` (`id`) ON DELETE CASCADE,
  CONSTRAINT `problem_link_problem_ibfk_2` FOREIGN KEY (`problem_link_id`) REFERENCES `problem` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Данные таблицы `problem_link_problem`
LOCK TABLES `problem_link_problem` WRITE;
INSERT INTO `problem_link_problem` (`problem_id`, `problem_link_id`) VALUES (10, 8);
INSERT INTO `problem_link_problem` (`problem_id`, `problem_link_id`) VALUES (10, 9);
UNLOCK TABLES;


-- Структура таблицы `refresh_token`
DROP TABLE IF EXISTS `refresh_token`;
CREATE TABLE `refresh_token` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `token` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` timestamp NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token` (`token`),
  KEY `idx_refreshtoken_user` (`user_id`),
  KEY `idx_refreshtoken_token` (`token`),
  CONSTRAINT `refresh_token_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=152 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Токены обновления для аутентификации';

-- Данные таблицы `refresh_token`
LOCK TABLES `refresh_token` WRITE;
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (134, 18, 'refresh_token_7qdqH6P8lv4oMfWs4vq0ZiWXzNR7y8XA828kUCq9Xhk', '2025-12-10 11:34:19', '2026-01-09 11:34:19');
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (135, 19, 'refresh_token_tYsh3qNCIPUnIzvmwYELCw4oW_TR1zdjathIaWx_qro', '2025-12-10 11:38:51', '2026-01-09 11:38:51');
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (136, 19, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOjE5LCJleHAiOjE3Njc5NTg3MzV9.oO6bfeQnPKlWndxRt-lFVN5bRmlhv9-j_N5mMo9otgE', '2025-12-10 11:38:56', '2026-01-09 11:38:56');
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (137, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOjEsImV4cCI6MTc2Nzk1OTQ3NX0.HJ3jEKwm6pLBY__cVMYJAly7Wn_Y874oFWZJ1JViA_Q', '2025-12-10 11:51:15', '2026-01-09 11:51:15');
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (138, 16, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOjE2LCJleHAiOjE3Njc5NTk1MDR9.zNCKfaciKNCruzAhzeSU-JyFuwdUkC20kxJaQIu01o0', '2025-12-10 11:51:44', '2026-01-09 11:51:44');
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (139, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOjEsImV4cCI6MTc3MDE0OTI0M30.390Ydm3Gaovq-VuX-TDz-o9oES4ejiJriaJF4PKz9UY', '2026-01-04 20:07:23', '2026-02-03 20:07:23');
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (140, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOjEsImV4cCI6MTc3MDE1MDQ1NX0.uBCg6d9tGNKfT3hfQTjdnglJFs6EtpqjQskbXN6zPD0', '2026-01-04 20:27:36', '2026-02-03 20:27:36');
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (141, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOjEsImV4cCI6MTc3MDE1MTQxMX0.j-xln--SF7e1sJEDRoLGrKaEwWVMD0EIlF7unmbR1DE', '2026-01-04 20:43:32', '2026-02-03 20:43:32');
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (142, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOjEsImV4cCI6MTc3MDE1MTQyNn0.Rgf-iCEDcFkblzw1iaQpFlbw41Cxc_oCHM-5EONOpzQ', '2026-01-04 20:43:46', '2026-02-03 20:43:46');
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (143, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOjEsImV4cCI6MTc3MDE1MTQ0NX0.fruceRA8plUZq_QEglrcLKeerFuwDVV8EcEDZldUfGY', '2026-01-04 20:44:05', '2026-02-03 20:44:05');
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (145, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOjEsImV4cCI6MTc3MDE1NjA1Mn0.5G2js1e-DYlrYAXHlUI_sZw1p5F9yb9mB6LRHcQFYqU', '2026-01-04 22:00:52', '2026-02-03 22:00:52');
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (146, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOjEsImV4cCI6MTc3MDMyMjMxMn0.b6E2YjGMa7Vvs40nHQ6duIg4IxVC6nvI198axYvNXKo', '2026-01-06 20:11:52', '2026-02-05 20:11:52');
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (147, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOjEsImV4cCI6MTc3MDMyNzUzMn0.McMz5On7nsq6uKWNDgJCa98OLyqv19wcgQl3hgKj9BM', '2026-01-06 21:38:52', '2026-02-05 21:38:52');
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (148, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOjEsImV4cCI6MTc3MDM3MDMzN30.Fw6Ojd6BG_CT-ihCV4KXp4W4uzX8Z5cfShoJqRukDFE', '2026-01-07 09:32:17', '2026-02-06 09:32:17');
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (149, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOjEsImV4cCI6MTc3MDM3MTgxNn0.vS4EY7UPkOmCRzlJfYnE0R1FUkHklNfZvk9yO53f1qk', '2026-01-07 09:56:57', '2026-02-06 09:56:57');
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (150, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOjEsImV4cCI6MTc3MDQxMTcyNH0.Hini8AZExxvAKBEFGYZx3eQ_drusqJ_nNj2u2OhQSE0', '2026-01-07 21:02:04', '2026-02-06 21:02:04');
INSERT INTO `refresh_token` (`id`, `user_id`, `token`, `created_at`, `expires_at`) VALUES (151, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOjEsImV4cCI6MTc3MDQxMTcyOH0.N2Qc-wCKYsZ4yb6pA697WbSjbPHpBmHIczuFX_AUFWM', '2026-01-07 21:02:09', '2026-02-06 21:02:09');
UNLOCK TABLES;


-- Структура таблицы `show_user_solution`
DROP TABLE IF EXISTS `show_user_solution`;
CREATE TABLE `show_user_solution` (
  `solutionid` int NOT NULL,
  `userid` int NOT NULL,
  PRIMARY KEY (`solutionid`,`userid`),
  KEY `userid` (`userid`),
  CONSTRAINT `show_user_solution_ibfk_1` FOREIGN KEY (`solutionid`) REFERENCES `solution` (`id`) ON DELETE CASCADE,
  CONSTRAINT `show_user_solution_ibfk_2` FOREIGN KEY (`userid`) REFERENCES `user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Структура таблицы `solution`
DROP TABLE IF EXISTS `solution`;
CREATE TABLE `solution` (
  `id` int NOT NULL AUTO_INCREMENT,
  `complexity` int DEFAULT NULL,
  `describe` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `efficiency` int DEFAULT NULL,
  `favourite` int DEFAULT '0',
  `fromauthor` tinyint(1) DEFAULT '0',
  `image` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `isbought` tinyint(1) DEFAULT '0',
  `isnew` tinyint(1) DEFAULT '1',
  `israting` tinyint(1) DEFAULT '0',
  `like` int DEFAULT '0',
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `notlike` int DEFAULT '0',
  `price` decimal(10,2) DEFAULT NULL,
  `rating` int DEFAULT '0',
  `reply` int DEFAULT '0',
  `show` int DEFAULT '0',
  `time` int DEFAULT NULL,
  `creator` int NOT NULL,
  `modified_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `attach` json DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_solution_creator` (`creator`),
  CONSTRAINT `solution_ibfk_1` FOREIGN KEY (`creator`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Решения проблем';

-- Данные таблицы `solution`
LOCK TABLES `solution` WRITE;
INSERT INTO `solution` (`id`, `complexity`, `describe`, `efficiency`, `favourite`, `fromauthor`, `image`, `isbought`, `isnew`, `israting`, `like`, `name`, `notlike`, `price`, `rating`, `reply`, `show`, `time`, `creator`, `modified_date`, `created_date`, `attach`) VALUES (1, 4, 'Содержит здоровые жиры, которые помогают улучшить кровообращение и поддерживают функции мозга.', 4, 16, 0, 'https://placehold.co/400x300/667eea/ffffff?text=Solution', 1, 0, 1, 1, 'Яйца', 2, '4.00', 4, 15, 447, 5, 1, '2026-01-07 13:02:32', '2024-02-01 13:09:00', '[1]');
INSERT INTO `solution` (`id`, `complexity`, `describe`, `efficiency`, `favourite`, `fromauthor`, `image`, `isbought`, `isnew`, `israting`, `like`, `name`, `notlike`, `price`, `rating`, `reply`, `show`, `time`, `creator`, `modified_date`, `created_date`, `attach`) VALUES (2, 3, 'Являются хорошим источником витаминов B6 и B12, фолата и холина, которые поддерживают здоровье мозга', 4, 16, 0, 'https://placehold.co/400x300/764ba2/ffffff?text=Solution', 1, 0, 1, 1, 'Авокадо', 2, '4.00', 4, 16, 461, 5, 1, '2026-01-07 13:02:32', '2024-02-01 13:09:00', '[1]');
INSERT INTO `solution` (`id`, `complexity`, `describe`, `efficiency`, `favourite`, `fromauthor`, `image`, `isbought`, `isnew`, `israting`, `like`, `name`, `notlike`, `price`, `rating`, `reply`, `show`, `time`, `creator`, `modified_date`, `created_date`, `attach`) VALUES (3, 2, 'Что нужно есть, чтобы повысить свою работоспособность', 4, 16, 0, 'https://placehold.co/400x300/764ba2/ffffff?text=Solution', 1, 0, 1, 1, 'Шоколад', 2, '4.00', 4, 15, 461, 5, 1, '2026-01-07 13:02:32', '2024-02-01 13:09:00', '[1]');
INSERT INTO `solution` (`id`, `complexity`, `describe`, `efficiency`, `favourite`, `fromauthor`, `image`, `isbought`, `isnew`, `israting`, `like`, `name`, `notlike`, `price`, `rating`, `reply`, `show`, `time`, `creator`, `modified_date`, `created_date`, `attach`) VALUES (4, 5, 'Содержит вещество, повышающий дофамин', 4, 15, 0, 'https://placehold.co/400x300/764ba2/ffffff?text=Solution', 1, 0, 1, 1, 'Какао', 2, '4.00', 4, 15, 447, 5, 1, '2026-01-07 13:02:32', '2024-02-01 13:09:00', '[1]');
INSERT INTO `solution` (`id`, `complexity`, `describe`, `efficiency`, `favourite`, `fromauthor`, `image`, `isbought`, `isnew`, `israting`, `like`, `name`, `notlike`, `price`, `rating`, `reply`, `show`, `time`, `creator`, `modified_date`, `created_date`, `attach`) VALUES (5, 4, 'Повышает дофамин', 4, 15, 0, 'https://placehold.co/400x300/667eea/ffffff?text=Solution', 1, 0, 1, 1, 'Дофамин', 2, '4.00', 4, 15, 447, 5, 1, '2026-01-07 13:02:32', '2024-02-01 13:09:00', '[1]');
INSERT INTO `solution` (`id`, `complexity`, `describe`, `efficiency`, `favourite`, `fromauthor`, `image`, `isbought`, `isnew`, `israting`, `like`, `name`, `notlike`, `price`, `rating`, `reply`, `show`, `time`, `creator`, `modified_date`, `created_date`, `attach`) VALUES (6, 5, 'Как повысить коллаген упражнениями', 4, 15, 0, 'https://placehold.co/400x300/764ba2/ffffff?text=Solution', 1, 0, 1, 1, 'Коллаген', 2, '4.00', 4, 15, 447, 5, 1, '2026-01-07 13:02:32', '2024-02-01 13:09:00', '[1]');
INSERT INTO `solution` (`id`, `complexity`, `describe`, `efficiency`, `favourite`, `fromauthor`, `image`, `isbought`, `isnew`, `israting`, `like`, `name`, `notlike`, `price`, `rating`, `reply`, `show`, `time`, `creator`, `modified_date`, `created_date`, `attach`) VALUES (7, 4, 'Какие средства использовать для повышения коллагена в организме', 4, 15, 0, 'https://placehold.co/400x300/764ba2/ffffff?text=Solution', 1, 0, 1, 1, 'Коллаген', 2, '4.00', 4, 15, 447, 5, 1, '2026-01-07 13:02:32', '2024-02-01 13:09:00', '[1]');
INSERT INTO `solution` (`id`, `complexity`, `describe`, `efficiency`, `favourite`, `fromauthor`, `image`, `isbought`, `isnew`, `israting`, `like`, `name`, `notlike`, `price`, `rating`, `reply`, `show`, `time`, `creator`, `modified_date`, `created_date`, `attach`) VALUES (8, 3, 'Какие продукты употреблять для повышения коллагена в организме', 4, 15, 0, 'https://placehold.co/400x300/764ba2/ffffff?text=Solution', 1, 0, 1, 1, 'Коллаген', 2, '4.00', 4, 15, 447, 5, 1, '2026-01-07 13:02:32', '2024-02-01 13:09:00', '[1]');
INSERT INTO `solution` (`id`, `complexity`, `describe`, `efficiency`, `favourite`, `fromauthor`, `image`, `isbought`, `isnew`, `israting`, `like`, `name`, `notlike`, `price`, `rating`, `reply`, `show`, `time`, `creator`, `modified_date`, `created_date`, `attach`) VALUES (9, 2, 'Как чистить картошку', 4, 15, 0, 'https://placehold.co/400x300/764ba2/ffffff?text=Solution', 1, 0, 1, 1, 'Коллаген', 2, '4.00', 4, 15, 447, 5, 1, '2026-01-07 13:02:32', '2024-02-01 13:09:00', '[1]');
INSERT INTO `solution` (`id`, `complexity`, `describe`, `efficiency`, `favourite`, `fromauthor`, `image`, `isbought`, `isnew`, `israting`, `like`, `name`, `notlike`, `price`, `rating`, `reply`, `show`, `time`, `creator`, `modified_date`, `created_date`, `attach`) VALUES (10, 4, 'Медитации которые помогают при депрессии', 4, 15, 0, 'https://placehold.co/400x300/764ba2/ffffff?text=Solution', 1, 0, 1, 1, 'Коллаген', 2, '4.00', 4, 16, 448, 5, 1, '2026-01-07 13:09:00', '2024-02-01 13:09:00', '[1]');
INSERT INTO `solution` (`id`, `complexity`, `describe`, `efficiency`, `favourite`, `fromauthor`, `image`, `isbought`, `isnew`, `israting`, `like`, `name`, `notlike`, `price`, `rating`, `reply`, `show`, `time`, `creator`, `modified_date`, `created_date`, `attach`) VALUES (11, NULL, 'рчарачп', NULL, 0, 0, 'https://placehold.co/400x300/764ba2/ffffff?text=Solution', 1, 1, 0, 0, 'ачпрачп', 0, NULL, 0, 0, 0, NULL, 1, '2026-01-07 13:02:32', '2025-10-05 14:43:00', NULL);
UNLOCK TABLES;


-- Структура таблицы `solution_link_solution`
DROP TABLE IF EXISTS `solution_link_solution`;
CREATE TABLE `solution_link_solution` (
  `solution_id` int NOT NULL,
  `solution_link_id` int NOT NULL,
  PRIMARY KEY (`solution_id`,`solution_link_id`),
  KEY `solution_link_id` (`solution_link_id`),
  CONSTRAINT `solution_link_solution_ibfk_1` FOREIGN KEY (`solution_id`) REFERENCES `solution` (`id`) ON DELETE CASCADE,
  CONSTRAINT `solution_link_solution_ibfk_2` FOREIGN KEY (`solution_link_id`) REFERENCES `solution` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Данные таблицы `solution_link_solution`
LOCK TABLES `solution_link_solution` WRITE;
INSERT INTO `solution_link_solution` (`solution_id`, `solution_link_id`) VALUES (10, 2);
INSERT INTO `solution_link_solution` (`solution_id`, `solution_link_id`) VALUES (2, 10);
UNLOCK TABLES;


-- Структура таблицы `solution_problems`
DROP TABLE IF EXISTS `solution_problems`;
CREATE TABLE `solution_problems` (
  `problem_id` int NOT NULL,
  `solution_id` int NOT NULL,
  PRIMARY KEY (`problem_id`,`solution_id`),
  KEY `solution_id` (`solution_id`),
  CONSTRAINT `solution_problems_ibfk_1` FOREIGN KEY (`problem_id`) REFERENCES `problem` (`id`) ON DELETE CASCADE,
  CONSTRAINT `solution_problems_ibfk_2` FOREIGN KEY (`solution_id`) REFERENCES `solution` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Данные таблицы `solution_problems`
LOCK TABLES `solution_problems` WRITE;
INSERT INTO `solution_problems` (`problem_id`, `solution_id`) VALUES (10, 1);
INSERT INTO `solution_problems` (`problem_id`, `solution_id`) VALUES (10, 2);
INSERT INTO `solution_problems` (`problem_id`, `solution_id`) VALUES (10, 3);
INSERT INTO `solution_problems` (`problem_id`, `solution_id`) VALUES (10, 4);
INSERT INTO `solution_problems` (`problem_id`, `solution_id`) VALUES (10, 5);
INSERT INTO `solution_problems` (`problem_id`, `solution_id`) VALUES (10, 6);
UNLOCK TABLES;


-- Структура таблицы `solution_rating`
DROP TABLE IF EXISTS `solution_rating`;
CREATE TABLE `solution_rating` (
  `id` int NOT NULL AUTO_INCREMENT,
  `solution_id` int NOT NULL,
  `user_id` int NOT NULL,
  `rating_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rating_value` int NOT NULL,
  `created_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `modified_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_solution_rating_type` (`solution_id`,`user_id`,`rating_type`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `solution_rating_ibfk_1` FOREIGN KEY (`solution_id`) REFERENCES `solution` (`id`) ON DELETE CASCADE,
  CONSTRAINT `solution_rating_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `solution_rating_chk_1` CHECK (((`rating_value` >= 1) and (`rating_value` <= 5)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Структура таблицы `topic`
DROP TABLE IF EXISTS `topic`;
CREATE TABLE `topic` (
  `id` int NOT NULL AUTO_INCREMENT,
  `is_new` tinyint(1) DEFAULT '1',
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `creator` int NOT NULL,
  `modified_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `creator` (`creator`),
  CONSTRAINT `topic_ibfk_1` FOREIGN KEY (`creator`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Темы обсуждений';

-- Данные таблицы `topic`
LOCK TABLES `topic` WRITE;
INSERT INTO `topic` (`id`, `is_new`, `name`, `creator`, `modified_date`, `created_date`) VALUES (1, 0, 'Депрессия', 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00');
INSERT INTO `topic` (`id`, `is_new`, `name`, `creator`, `modified_date`, `created_date`) VALUES (2, 0, 'Дептест', 1, '2024-02-01 13:09:00', '2024-02-01 13:09:00');
INSERT INTO `topic` (`id`, `is_new`, `name`, `creator`, `modified_date`, `created_date`) VALUES (3, 1, 'Sfdgsdfgsdfg', 16, '2025-10-09 16:42:53', '2025-10-09 16:42:53');
INSERT INTO `topic` (`id`, `is_new`, `name`, `creator`, `modified_date`, `created_date`) VALUES (4, 1, 'Sdfgsfdgf', 16, '2025-10-09 16:47:59', '2025-10-09 16:47:59');
UNLOCK TABLES;


-- Структура таблицы `type_user`
DROP TABLE IF EXISTS `type_user`;
CREATE TABLE `type_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `modified_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Типы пользователей';

-- Данные таблицы `type_user`
LOCK TABLES `type_user` WRITE;
INSERT INTO `type_user` (`id`, `name`, `modified_date`, `created_date`) VALUES (2, 'Admin', '2025-08-14 15:45:25', '2025-08-14 15:45:25');
UNLOCK TABLES;


-- Структура таблицы `user`
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `favproblem` tinyint(1) DEFAULT '1',
  `favsolution` tinyint(1) DEFAULT '0',
  `image` text COLLATE utf8mb4_unicode_ci,
  `isactive` tinyint(1) DEFAULT '1',
  `lastlogin` timestamp NULL DEFAULT NULL,
  `username` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `modified_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `notification` json DEFAULT NULL,
  `type` int DEFAULT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `isnew` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  KEY `type` (`type`),
  CONSTRAINT `user_ibfk_1` FOREIGN KEY (`type`) REFERENCES `type_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Пользователи системы';

-- Данные таблицы `user`
LOCK TABLES `user` WRITE;
INSERT INTO `user` (`id`, `favproblem`, `favsolution`, `image`, `isactive`, `lastlogin`, `username`, `email`, `modified_date`, `created_date`, `notification`, `type`, `password_hash`, `isnew`) VALUES (1, 1, 0, NULL, 1, NULL, 'Anna', 'budkina.anna@gmail.com', '2025-12-10 14:45:21', '2025-08-14 15:51:03', NULL, 2, 'scrypt:32768:8:1$JcAfWU8Vd57hEiEb$cf77213586852f7e789e9adcc78f141a90a8cad6aa94a4725d5928c98c9a2e14ce9b6b0eb2877ec850f0c5dbca42927739abee534b592d673b48255a44ba8a23', 1);
INSERT INTO `user` (`id`, `favproblem`, `favsolution`, `image`, `isactive`, `lastlogin`, `username`, `email`, `modified_date`, `created_date`, `notification`, `type`, `password_hash`, `isnew`) VALUES (16, 1, 0, NULL, 1, NULL, 'Admin', 'budkina.ann@gmail.com', '2025-12-10 14:45:21', '2025-09-25 18:19:39', NULL, NULL, 'scrypt:32768:8:1$JcAfWU8Vd57hEiEb$cf77213586852f7e789e9adcc78f141a90a8cad6aa94a4725d5928c98c9a2e14ce9b6b0eb2877ec850f0c5dbca42927739abee534b592d673b48255a44ba8a23', 1);
INSERT INTO `user` (`id`, `favproblem`, `favsolution`, `image`, `isactive`, `lastlogin`, `username`, `email`, `modified_date`, `created_date`, `notification`, `type`, `password_hash`, `isnew`) VALUES (17, 1, 0, NULL, 1, NULL, 'anna1', 'vseprost23@gmail.com', '2025-12-10 14:45:21', '2025-12-10 11:27:13', NULL, NULL, 'scrypt:32768:8:1$JcAfWU8Vd57hEiEb$cf77213586852f7e789e9adcc78f141a90a8cad6aa94a4725d5928c98c9a2e14ce9b6b0eb2877ec850f0c5dbca42927739abee534b592d673b48255a44ba8a23', 1);
INSERT INTO `user` (`id`, `favproblem`, `favsolution`, `image`, `isactive`, `lastlogin`, `username`, `email`, `modified_date`, `created_date`, `notification`, `type`, `password_hash`, `isnew`) VALUES (18, 1, 0, NULL, 1, NULL, 'anna2', 'vseprost234@gmail.com', '2025-12-10 11:34:19', '2025-12-10 11:34:19', NULL, NULL, 'scrypt:32768:8:1$JcAfWU8Vd57hEiEb$cf77213586852f7e789e9adcc78f141a90a8cad6aa94a4725d5928c98c9a2e14ce9b6b0eb2877ec850f0c5dbca42927739abee534b592d673b48255a44ba8a23', 1);
INSERT INTO `user` (`id`, `favproblem`, `favsolution`, `image`, `isactive`, `lastlogin`, `username`, `email`, `modified_date`, `created_date`, `notification`, `type`, `password_hash`, `isnew`) VALUES (19, 1, 0, NULL, 1, NULL, 'anna22', 'vseprost2344@gmail.com', '2025-12-10 14:45:21', '2025-12-10 11:38:51', NULL, NULL, 'scrypt:32768:8:1$JcAfWU8Vd57hEiEb$cf77213586852f7e789e9adcc78f141a90a8cad6aa94a4725d5928c98c9a2e14ce9b6b0eb2877ec850f0c5dbca42927739abee534b592d673b48255a44ba8a23', 1);
UNLOCK TABLES;


-- Структура таблицы `user_cart_solution`
DROP TABLE IF EXISTS `user_cart_solution`;
CREATE TABLE `user_cart_solution` (
  `id` int NOT NULL AUTO_INCREMENT,
  `is_bought` tinyint(1) DEFAULT '0',
  `solution` int NOT NULL,
  `user` int NOT NULL,
  `creator` int NOT NULL,
  `modified_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `solution` (`solution`),
  KEY `user` (`user`),
  KEY `creator` (`creator`),
  CONSTRAINT `user_cart_solution_ibfk_1` FOREIGN KEY (`solution`) REFERENCES `solution` (`id`),
  CONSTRAINT `user_cart_solution_ibfk_2` FOREIGN KEY (`user`) REFERENCES `user` (`id`),
  CONSTRAINT `user_cart_solution_ibfk_3` FOREIGN KEY (`creator`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Данные таблицы `user_cart_solution`
LOCK TABLES `user_cart_solution` WRITE;
INSERT INTO `user_cart_solution` (`id`, `is_bought`, `solution`, `user`, `creator`, `modified_date`, `created_date`) VALUES (1, 0, 3, 1, 1, '2026-01-06 22:27:31', '2026-01-06 22:27:31');
INSERT INTO `user_cart_solution` (`id`, `is_bought`, `solution`, `user`, `creator`, `modified_date`, `created_date`) VALUES (2, 0, 2, 1, 1, '2026-01-06 22:36:09', '2026-01-06 22:36:09');
UNLOCK TABLES;

SET FOREIGN_KEY_CHECKS=1;
