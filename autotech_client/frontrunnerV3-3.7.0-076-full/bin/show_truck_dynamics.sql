DROP PROCEDURE IF EXISTS show_truck_dynamics_tables;
DROP PROCEDURE IF EXISTS show_linear_graph;

DELIMITER //
CREATE PROCEDURE show_linear_graph( IN aDescr VARCHAR(255), IN aOidLinearGraph VARCHAR(32) )
BEGIN
    SELECT aDescr AS 'TYPE(TABLE-ID) - GRAPH(GRAPH-ID)',`_OID_`,`x`,`y`,`_CID_` FROM feature_point WHERE
        EXISTS (
            SELECT * FROM linear_graph__x_y WHERE
                feature_point.`_OID_` = linear_graph__x_y.`_feature_point`
                AND linear_graph__x_y.`_OID_` = aOidLinearGraph
        );
END //

CREATE PROCEDURE show_truck_dynamics_tables()
BEGIN
    DECLARE eqmtTypeName VARCHAR(32);
    DECLARE oid_truck_dynamics VARCHAR(32);
    DECLARE oid_idlp_graph VARCHAR(32);
    DECLARE oid_idep_graph VARCHAR(32);
    DECLARE oid_idl_graph VARCHAR(32);
    DECLARE oid_ide_graph VARCHAR(32);
    DECLARE oid_islp_graph VARCHAR(32);
    DECLARE oid_isep_graph VARCHAR(32);
    DECLARE oid_isl_graph VARCHAR(32);
    DECLARE oid_ise_graph VARCHAR(32);
    DECLARE oid_sd_graph VARCHAR(32);
    DECLARE oid_isl_custom_graph VARCHAR(32);
    DECLARE oid_ise_custom_graph VARCHAR(32);

    DECLARE done INT DEFAULT FALSE;
    DECLARE cursor_dynamics_tables CURSOR FOR
        SELECT
            eqmt_prf._OID_,
            eqmt_prf._truck_dynamics,
            dynamics_table._idlp_graph,
            dynamics_table._idep_graph,
            dynamics_table._idl_graph,
            dynamics_table._ide_graph,
            dynamics_table._islp_graph,
            dynamics_table._isep_graph,
            dynamics_table._isl_graph,
            dynamics_table._ise_graph,
            dynamics_table._sd_graph,
            dynamics_table._isl_custom_graph,
            dynamics_table._ise_custom_graph
        FROM
            cfg_eqmt_prf AS eqmt_prf,
            cfg_aht_prf_truck_dynamics AS dynamics_table
        WHERE
            NOT eqmt_prf._truck_dynamics IS NULL
            AND eqmt_prf._truck_dynamics = dynamics_table._OID_;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    OPEN cursor_dynamics_tables;
    dynamics_table_loop: LOOP
        FETCH
            cursor_dynamics_tables
        INTO
            eqmtTypeName,
            oid_truck_dynamics,
            oid_idlp_graph,
            oid_idep_graph,
            oid_idl_graph,
            oid_ide_graph,
            oid_islp_graph,
            oid_isep_graph,
            oid_isl_graph,
            oid_ise_graph,
            oid_sd_graph,
            oid_isl_custom_graph,
            oid_ise_custom_graph;

        IF done THEN
            LEAVE dynamics_table_loop;
        END IF;

        CALL show_linear_graph( CONCAT( eqmtTypeName, '(', oid_truck_dynamics, ') - idlp_graph(', oid_idlp_graph, ')' ), oid_idlp_graph );
        SELECT '' AS '\n\n';
        CALL show_linear_graph( CONCAT( eqmtTypeName, '(', oid_truck_dynamics, ') - idep_graph(', oid_idep_graph, ')' ), oid_idep_graph );
        SELECT '' AS '\n\n';
        CALL show_linear_graph( CONCAT( eqmtTypeName, '(', oid_truck_dynamics, ') - idl_graph(',  oid_idl_graph, ')' ),  oid_idl_graph );
        SELECT '' AS '\n\n';
        CALL show_linear_graph( CONCAT( eqmtTypeName, '(', oid_truck_dynamics, ') - ide_graph(',  oid_ide_graph, ')' ),  oid_ide_graph );
        SELECT '' AS '\n\n';
        CALL show_linear_graph( CONCAT( eqmtTypeName, '(', oid_truck_dynamics, ') - islp_graph(', oid_islp_graph, ')' ), oid_islp_graph );
        SELECT '' AS '\n\n';
        CALL show_linear_graph( CONCAT( eqmtTypeName, '(', oid_truck_dynamics, ') - isep_graph(', oid_isep_graph, ')' ), oid_isep_graph );
        SELECT '' AS '\n\n';
        CALL show_linear_graph( CONCAT( eqmtTypeName, '(', oid_truck_dynamics, ') - isl_graph(',  oid_isl_graph, ')' ),  oid_isl_graph );
        SELECT '' AS '\n\n';
        CALL show_linear_graph( CONCAT( eqmtTypeName, '(', oid_truck_dynamics, ') - ise_graph(',  oid_ise_graph, ')' ),  oid_ise_graph );
        SELECT '' AS '\n\n';
        CALL show_linear_graph( CONCAT( eqmtTypeName, '(', oid_truck_dynamics, ') - sd_graph(',   oid_sd_graph, ')' ),   oid_sd_graph );
        SELECT '' AS '\n\n';
        CALL show_linear_graph( CONCAT( eqmtTypeName, '(', oid_truck_dynamics, ') - isl_custom_graph(', oid_isl_custom_graph, ')' ), oid_isl_custom_graph );
        SELECT '' AS '\n\n';
        CALL show_linear_graph( CONCAT( eqmtTypeName, '(', oid_truck_dynamics, ') - ise_custom_graph(', oid_ise_custom_graph, ')' ), oid_ise_custom_graph );
  END LOOP;
  CLOSE cursor_dynamics_tables;
END //
DELIMITER ;

CALL show_truck_dynamics_tables();

DROP PROCEDURE IF EXISTS show_truck_dynamics_tables;
DROP PROCEDURE IF EXISTS show_linear_graph;
