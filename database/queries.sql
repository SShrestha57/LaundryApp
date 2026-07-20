-- LaundryApp queries


-- =====================================================
-- BOOKING DETAILS
-- Shows each booking with its user, machine, building,
-- and payment split when a payment exists.
-- =====================================================

SELECT
    b.booking_id,
    u.name AS user_name,
    m.machine_type,
    m.machine_number,
    bu.name AS building_name,
    b.price_at_booking,
    bp.transaction_fee,
    bp.building_amount,
    b.booking_status
FROM bookings b
JOIN users u
    ON b.user_id = u.user_id
JOIN machines m
    ON b.machine_id = m.machine_id
JOIN buildings bu
    ON m.building_id = bu.building_id
LEFT JOIN booking_payments bp
    ON b.booking_id = bp.booking_id;


-- =====================================================
-- ACTIVE MACHINES IN A BUILDING
-- Shows operational machines belonging to one building.
-- Change building_id = 1 to the required building.
-- =====================================================

SELECT
    machine_id,
    machine_number,
    machine_type,
    cost_per_cycle,
    duration_minutes,
    status
FROM machines
WHERE building_id = 1
    AND status = 'active'
ORDER BY machine_type, machine_number;


-- =====================================================
-- TENANT BOOKING HISTORY
-- Shows all bookings made by one user.
-- Change user_id = 2 to the required user.
-- =====================================================

SELECT
    b.booking_id,
    m.machine_type,
    m.machine_number,
    b.start_time,
    b.end_time,
    b.price_at_booking,
    b.booking_status
FROM bookings b
JOIN machines m
    ON b.machine_id = m.machine_id
WHERE b.user_id = 2
ORDER BY b.start_time DESC;


-- =====================================================
-- AVAILABLE MACHINES FOR A REQUESTED TIME
-- Shows active machines that do not have a conflicting
-- pending or confirmed booking.
-- =====================================================

SELECT
    m.machine_id,
    m.machine_number,
    m.machine_type,
    m.cost_per_cycle,
    m.duration_minutes
FROM machines m
LEFT JOIN bookings b
    ON m.machine_id = b.machine_id
    AND b.booking_status IN ('pending', 'confirmed')
    AND b.start_time < '2026-07-18 18:40:00'
    AND b.end_time > '2026-07-18 18:00:00'
WHERE m.building_id = 1
  AND m.status = 'active'
  AND b.booking_id IS NULL
ORDER BY m.machine_type, m.machine_number;


-- =====================================================
-- BUILDING LAUNDRY REVENUE
-- Calculates the amount credited to each building from
-- successfully paid laundry bookings.
-- =====================================================

SELECT
    bu.building_id,
    bu.name AS building_name,
    SUM(bp.building_amount) AS total_building_revenue
FROM booking_payments bp
JOIN bookings b
    ON bp.booking_id = b.booking_id
JOIN machines m
    ON b.machine_id = m.machine_id
JOIN buildings bu
    ON m.building_id = bu.building_id
WHERE bp.payment_status = 'paid'
GROUP BY
    bu.building_id,
    bu.name
ORDER BY total_building_revenue DESC;