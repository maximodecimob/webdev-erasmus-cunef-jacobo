-- One active ticket per customer and event (AC-4); a cancelled ticket frees the slot.
CREATE UNIQUE INDEX IF NOT EXISTS idx_tickets_one_active
    ON tickets (event_id, customer_id) WHERE status = 'active';
