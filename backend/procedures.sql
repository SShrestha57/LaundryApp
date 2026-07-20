-- =====================================================================
-- WashWise / LaundryApp — Stored Procedures + Triggers
-- =====================================================================

USE washwise;

-- ---------------------------------------------------------------------
-- STORED PROCEDURE 1 — total revenue per building (both streams)
--   booking_revenue      = transaction fees the app keeps on bookings
--   subscription_revenue = SaaS fees the building pays the app
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_revenue_report;
DELIMITER //
CREATE PROCEDURE sp_revenue_report()
BEGIN
    SELECT
        bl.building_id,
        bl.name AS building,
        COALESCE((
            SELECT SUM(bp.transaction_fee)
            FROM booking_payments bp
            JOIN bookings b   ON bp.booking_id = b.booking_id
            JOIN machines m   ON b.machine_id = m.machine_id
            WHERE m.building_id = bl.building_id
              AND bp.payment_status = 'paid'
        ), 0) AS booking_revenue,
        COALESCE((
            SELECT SUM(sp.amount)
            FROM subscription_payments sp
            JOIN building_subscriptions bs ON sp.subscription_id = bs.subscription_id
            WHERE bs.building_id = bl.building_id
              AND sp.payment_status = 'paid'
        ), 0) AS subscription_revenue
    FROM buildings bl
    ORDER BY bl.building_id;
END //
DELIMITER ;

-- ---------------------------------------------------------------------
-- STORED PROCEDURE 2 — create a booking, return the new booking_id
-- (machine status is handled by the AFTER INSERT trigger)
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_book_machine;
DELIMITER //
CREATE PROCEDURE sp_book_machine(
    IN p_user_id     INT,
    IN p_machine_id  INT,
    IN p_start_time  DATETIME,
    IN p_end_time    DATETIME,
    IN p_price       DECIMAL(6,2)
)
BEGIN
    INSERT INTO bookings
        (user_id, machine_id, start_time, end_time, price_at_booking, booking_status)
    VALUES
        (p_user_id, p_machine_id, p_start_time, p_end_time, p_price, 'confirmed');

    SELECT LAST_INSERT_ID() AS booking_id;
END //
DELIMITER ;

-- ---------------------------------------------------------------------
-- TRIGGER 1 — after a booking is created, mark the machine in_use
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_booking_after_insert;
DELIMITER //
CREATE TRIGGER trg_booking_after_insert
AFTER INSERT ON bookings
FOR EACH ROW
BEGIN
    IF NEW.booking_status = 'confirmed' THEN
        UPDATE machines
        SET status = 'in_use'
        WHERE machine_id = NEW.machine_id;
    END IF;
END //
DELIMITER ;

-- ---------------------------------------------------------------------
-- TRIGGER 2 — when a booking is cancelled/completed, free the machine
-- ---------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_booking_after_update;
DELIMITER //
CREATE TRIGGER trg_booking_after_update
AFTER UPDATE ON bookings
FOR EACH ROW
BEGIN
    IF NEW.booking_status IN ('cancelled', 'completed')
       AND OLD.booking_status <> NEW.booking_status THEN
        UPDATE machines
        SET status = 'available'
        WHERE machine_id = NEW.machine_id;
    END IF;
END //
DELIMITER ;
