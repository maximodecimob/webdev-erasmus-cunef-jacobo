import pytest

from app.errors import AlreadyHolds, EventStarted, NotAllowed, SoldOut
from app.repositories.event_repo import EventRepository
from app.services import ticket_service


def tickets_left(event_id):
    return next(e["tickets_left"] for e in EventRepository.get_upcoming_events() if e["id"] == event_id)


def test_AC_3_buying_gives_a_unique_code_and_lowers_tickets_left(world):
    """AC-3: buying gives a unique code and lowers tickets left"""
    event_id = world.add_event(total_tickets=5)
    first = ticket_service.buy_ticket(world.customer, event_id)
    second = ticket_service.buy_ticket(world.other, event_id)
    assert first["code"] and first["code"] != second["code"]
    assert tickets_left(event_id) == 3


def test_AC_2_a_sold_out_event_refuses_the_purchase(world):
    """AC-2: a sold out event refuses the purchase"""
    event_id = world.add_event(total_tickets=1)
    ticket_service.buy_ticket(world.customer, event_id)
    with pytest.raises(SoldOut, match="This event is sold out"):
        ticket_service.buy_ticket(world.other, event_id)
    assert world.count_tickets() == 1


def test_AC_4_a_customer_cannot_hold_two_tickets_for_one_event(world):
    """AC-4: a customer cannot hold two tickets for one event"""
    event_id = world.add_event()
    ticket_service.buy_ticket(world.customer, event_id)
    with pytest.raises(AlreadyHolds):
        ticket_service.buy_ticket(world.customer, event_id)
    assert world.count_tickets() == 1


def test_AC_26_an_organizer_cannot_buy_a_ticket(world):
    """AC-26: an organizer cannot buy a ticket"""
    event_id = world.add_event()
    with pytest.raises(NotAllowed):
        ticket_service.buy_ticket(world.organizer, event_id)
    assert world.count_tickets() == 0


def test_AC_15_my_tickets_lists_only_the_customers_own_tickets(world):
    """AC-15: my tickets lists only the customers own tickets"""
    event_id = world.add_event()
    ticket_service.buy_ticket(world.customer, event_id)
    ticket_service.buy_ticket(world.other, event_id)
    mine = ticket_service.my_tickets(world.customer)
    assert len(mine) == 1
    assert {"code", "title", "venue", "date"} <= set(mine[0])


def test_AC_12_cancelling_my_ticket_removes_it_and_frees_the_place(world):
    """AC-12: cancelling my ticket removes it and frees the place"""
    event_id = world.add_event(total_tickets=3)
    ticket = ticket_service.buy_ticket(world.customer, event_id)
    ticket_service.cancel_ticket(world.customer, ticket["id"])
    assert ticket_service.my_tickets(world.customer) == []
    assert tickets_left(event_id) == 3
    ticket_service.buy_ticket(world.customer, event_id)


def test_AC_16_cancelling_another_customers_ticket_is_refused(world):
    """AC-16: cancelling another customers ticket is refused"""
    event_id = world.add_event()
    ticket = ticket_service.buy_ticket(world.customer, event_id)
    with pytest.raises(NotAllowed):
        ticket_service.cancel_ticket(world.other, ticket["id"])
    assert len(ticket_service.my_tickets(world.customer)) == 1


def test_AC_17_a_ticket_of_an_event_that_started_cannot_be_cancelled(world):
    """AC-17: a ticket of an event that started cannot be cancelled"""
    event_id = world.add_event(days=-1)
    ticket_id = world.add_ticket(event_id, world.customer["id"])
    with pytest.raises(EventStarted):
        ticket_service.cancel_ticket(world.customer, ticket_id)
    assert len(ticket_service.my_tickets(world.customer)) == 1
