DROP PROCEDURE IF EXISTS `remove_broken_isolation_area`;
delimiter //

CREATE PROCEDURE `remove_broken_isolation_area`() DETERMINISTIC
   BEGIN
      DECLARE brokens INT;

      CREATE OR REPLACE VIEW ISOLATE_XYZ AS SELECT _OID_ FROM isolation_area__shape__x_y_z;
      SELECT count(*) INTO brokens FROM isolation_area WHERE _OID_ NOT IN (SELECT * FROM ISOLATE_XYZ);
      
      if brokens > 0 THEN
          SELECT _OWNER as 'Equipment Affected by Broken Isolation' FROM isolation_area WHERE _OID_ NOT IN (SELECT * FROM ISOLATE_XYZ);
          DELETE FROM isolation_area WHERE _OID_ NOT IN (SELECT * FROM ISOLATE_XYZ);
      END IF;
      DROP VIEW ISOLATE_XYZ;
   END;//

DELIMITER ;

CALL remove_broken_isolation_area();
