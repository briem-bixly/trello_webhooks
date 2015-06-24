import datetime
import pytz
from dateutil import parser as dateparser #pip install python-dateutil
from trello import TrelloClient, Card


class trello_completed_notify(NebriOS):
    listens_to = ['fetch_trello_completed_cards']

    def check(self):
        return self.fetch_trello_completed_cards  == True

    def action(self):
        self.fetch_trello_completed_cards = "Ran"
        boards = shared.TRELLO_COMPLETED_CARD_CACHE
        # By default, our timezone is America/Los_Angeles
        # https://scriptrunner.nebrios.com/timezone/edit/
        dt_now = datetime.datetime.now(pytz.utc)
        
        email_body = ""
        for b in boards:
            cards = b['cards']
            my_cards = []
            for card in cards:
                dt_o = card['date']
                if isinstance(dt_o, basestring):
                    dt_o = parse_datetime(dt_o)
                
                # One of your due values is a date instead of a datetime...
                # we do not support substraction between date and datetime
                # This causes a NotImplemented exception
                # dt_o = dt_o.astimezone(pytz.utc)
                dt_o = force_convert_to_utc(dt_o)
                diff = dt_now - dt_o
                if 0 <= diff.total_seconds() and diff.total_seconds() <= 60*60*24:
                    my_cards.append(card)
            if len(my_cards) > 0:
                to_append = "<h2>Board: %s</h2>\n" % b['name']
                to_append = to_append + "<h3>Recently finished tickets</h3>\n"
                to_append = to_append + "<ul>"
                for card in my_cards:
                    to_append = "%s<li><a href='https://trello.com/c/%s'>%s</a></li>" % (to_append, card['shortLink'], card['name'])
                to_append = to_append + "</ul>"
                email_body = email_body + to_append
            else:
                # no cards in this board satisfying the notification requirements
                print "No cards in this board satisfying notification requirements"
        if email_body != "":
            send_email (shared.COMPLETED_NOTIFY_ADDRESS, email_body)

    
def force_convert_to_utc(d):
    return pytz.utc.localize(datetime.datetime(d.year, d.month, d.day, d.hour, d.minute, d.second))

def get_open_cards(board):
    filters = {
        'filter': 'all',
        'fields': 'all'
    }
    json_obj = board.client.fetch_json(
        '/boards/' + board.id + '/cards',
        query_params=filters
    )
    ret = []
    for json in json_obj:
        card = Card.from_json(board, json)
        if json.get('due',''):
            card.due = json['due']
        else:
            card.due = False
        card.actual_list_id = json.get('idList', '')
        ret.append(card)

    return ret

def get_card_list_changes(card):
    filters = {
        'filter': 'updateCard:idList'
    }
    json = card.client.fetch_json('/cards/' + card.id + '/actions/',
                            query_params=filters)
    return json
