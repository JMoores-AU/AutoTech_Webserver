#Define variables
SET @database_name = '%s';
SET @fr_user = '%s';
SET @fr_password = '%s';
SET @host = '%s';

#Define create user statements
SET @create_query_1 = CONCAT ('CREATE USER "',@fr_user, '"@"', @host, '" IDENTIFIED BY "', @fr_password, '"');

#Define grant statements
SET @grant_query_1 = CONCAT ('GRANT ALL PRIVILEGES ON ', @database_name,'.* TO "', @fr_user, '"@"', @host,'"');
SET @grant_query_2 = CONCAT ('GRANT RELOAD ON *.* TO "', @fr_user, '"@"', @host,'"');


#Execute statements
PREPARE stmt FROM @create_query_1; 
EXECUTE stmt; 
DEALLOCATE PREPARE stmt;

PREPARE stmt FROM @grant_query_1; 
EXECUTE stmt; 
DEALLOCATE PREPARE stmt;

PREPARE stmt FROM @grant_query_2; 
EXECUTE stmt; 
DEALLOCATE PREPARE stmt;
