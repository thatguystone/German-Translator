-- MySQL dump 10.13  Distrib 5.1.49, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: deutsch
-- ------------------------------------------------------
-- Server version	5.1.49-1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `canooWords`
--

DROP TABLE IF EXISTS `canooWords`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `canooWords` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `full` varchar(50) NOT NULL,
  `stem` varchar(50) NOT NULL COMMENT 'Equal to first person',
  `preterite` varchar(50) NOT NULL,
  `hilfsverb` enum('haben','sein') NOT NULL,
  `perfect` varchar(50) NOT NULL,
  `third` varchar(50) NOT NULL,
  `subj2` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `full` (`full`,`hilfsverb`),
  KEY `stem` (`stem`),
  KEY `preterite` (`preterite`),
  KEY `hilfsverb` (`hilfsverb`),
  KEY `perfect` (`perfect`),
  KEY `third` (`third`),
  KEY `subj2` (`subj2`)
) ENGINE=MyISAM AUTO_INCREMENT=12 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `failedSearches`
--

DROP TABLE IF EXISTS `failedSearches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `failedSearches` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `search` varchar(100) NOT NULL,
  `source` enum('leo','canoo') NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `search` (`search`,`source`)
) ENGINE=MyISAM AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `leoWords`
--

DROP TABLE IF EXISTS `leoWords`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `leoWords` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `en` varchar(100) NOT NULL,
  `enExt` varchar(200) NOT NULL,
  `de` varchar(100) NOT NULL,
  `deExt` varchar(200) NOT NULL,
  `pos` enum('adjadv','noun','prep','verb') NOT NULL COMMENT 'Not piece of shit -- part of speech',
  PRIMARY KEY (`id`),
  UNIQUE KEY `en_2` (`en`,`de`,`pos`),
  KEY `en` (`en`),
  KEY `de` (`de`)
) ENGINE=MyISAM AUTO_INCREMENT=43 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2010-10-25 16:07:51
