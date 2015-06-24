import pytz
# from dateutil import parser as dateparser #pip install python-dateutil

class trello_pastdue_notify_webhook(NebriOS):
    listens_to = ['trello_pastdue_notify_webhook']
    TARGET_EMAIL = "briem@bixly.com"

    def check(self):
        return self.trello_pastdue_notify_webhook  == True

    def action(self):
        self.trello_pastdue_notify_webhook = "Ran"
        dt_now = datetime.now(pytz.utc)
        
        email_body = ""
        for board in shared.TRELLO_DUE_CARD_CACHE:
            my_cards = []
            cards = board['cards']
            for card in cards:
                dt_o = card['due']
                if isinstance(dt_o, basestring):
                    dt_o = parse_datetime(dt_o)
                dt_o = dt_o.astimezone(pytz.utc)
                diff = dt_now - dt_o
                if 0 <= diff.total_seconds() and diff.total_seconds() <= 60*60*24:
                    my_cards.append(card)
                else:
                    print "not yet deadline"
            if len(my_cards) > 0:
                to_append = "<h2>Board: %s</h2>\n" % board['name']
                to_append = to_append + "<ul>"
                for card in my_cards:
                    to_append = "%s<li><a href='https://trello.com/c/%s'>%s</a></li>" % (to_append, card['shortLink'], card['name'])
                to_append = to_append + "</ul>"
                email_body = email_body + to_append
            else:
                # no cards in this board satisfying the notification requirements
                print "No cards in this board satisfying notification requirements"
                
        if email_body != "":
            send_email (self.PAST_DUE_NOTIFY_ADDRESS, email_body)
