#Define variables
SET @database_name = '%s';
SET @geoserver_user = '%s';
SET @geoserver_password = '%s';
SET @host = '%s';

#Define create user statements
SET @create_query_1 = CONCAT ('CREATE USER "',@geoserver_user, '"@"', @host, '" IDENTIFIED BY "', @geoserver_password, '"');

#Define grant statements
SET @grant_query_1 = CONCAT ('GRANT SELECT ON ', @database_name,'.* TO "', @geoserver_user, '"@"', @host,'"');


#Execute statements
PREPARE stmt FROM @create_query_1; 
EXECUTE stmt; 
DEALLOCATE PREPARE stmt;

PREPARE stmt FROM @grant_query_1; 
EXECUTE stmt; 
DEALLOCATE PREPARE stmt;
