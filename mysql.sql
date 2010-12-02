-- MySQL dump 10.13  Distrib 5.1.49, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: deutsch
-- ------------------------------------------------------
-- Server version	5.1.49-2

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
-- Table structure for table `searches`
--

DROP TABLE IF EXISTS `searches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `searches` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `search` varchar(100) COLLATE latin1_german2_ci NOT NULL,
  `source` enum('leo','canoo') COLLATE latin1_german2_ci NOT NULL,
  `success` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `search` (`search`,`source`,`success`)
) ENGINE=MyISAM AUTO_INCREMENT=566401 DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `translations`
--

DROP TABLE IF EXISTS `translations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `translations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `en` varchar(100) COLLATE latin1_german2_ci NOT NULL,
  `enExt` varchar(200) COLLATE latin1_german2_ci NOT NULL,
  `de` varchar(100) COLLATE latin1_german2_ci NOT NULL,
  `deExt` varchar(200) COLLATE latin1_german2_ci NOT NULL,
  `pos` enum('adjadv','noun','prep','verb') COLLATE latin1_german2_ci NOT NULL COMMENT 'Not piece of shit -- part of speech',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniqueifier` (`en`,`de`,`pos`),
  KEY `de` (`de`),
  KEY `en_de` (`en`,`de`),
  KEY `en` (`en`)
) ENGINE=MyISAM AUTO_INCREMENT=387564 DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `verbs`
--

DROP TABLE IF EXISTS `verbs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `verbs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `full` varchar(50) COLLATE latin1_german2_ci NOT NULL,
  `stem` varchar(50) COLLATE latin1_german2_ci NOT NULL,
  `preterite` varchar(50) COLLATE latin1_german2_ci NOT NULL,
  `hilfsverb` enum('haben','sein') COLLATE latin1_german2_ci NOT NULL,
  `perfect` varchar(50) COLLATE latin1_german2_ci NOT NULL,
  `first` varchar(50) COLLATE latin1_german2_ci NOT NULL,
  `firstPlural` varchar(50) COLLATE latin1_german2_ci NOT NULL,
  `second` varchar(50) COLLATE latin1_german2_ci NOT NULL,
  `third` varchar(50) COLLATE latin1_german2_ci NOT NULL,
  `thirdPlural` varchar(50) COLLATE latin1_german2_ci NOT NULL,
  `subj2` varchar(50) COLLATE latin1_german2_ci NOT NULL,
  `participle` varchar(50) COLLATE latin1_german2_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `full` (`full`,`hilfsverb`,`stem`,`first`),
  KEY `stem` (`stem`),
  KEY `preterite` (`preterite`),
  KEY `hilfsverb` (`hilfsverb`),
  KEY `perfect` (`perfect`),
  KEY `third` (`third`),
  KEY `subj2` (`subj2`),
  KEY `first` (`first`),
  KEY `participle` (`participle`),
  KEY `full_2` (`full`),
  KEY `second` (`second`),
  KEY `thirdPlural` (`thirdPlural`),
  KEY `firstPlural` (`firstPlural`)
) ENGINE=MyISAM AUTO_INCREMENT=7844 DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2010-12-02  2:30:21
