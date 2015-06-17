class trello_webhook_setup(NebriOS):
    listens_to = ['trello_webhook_setup']
    
    # Note: This script is used to set up the trello webhook system.
    # If shared.TRELLO_API_KEY and shared.TRELLO_API_SECRET are not created,
    # you should supply them like so:
    # trello_api_key := <api_key>
    # trello_api_secret := <api_secret>

    def check(self):
        return self.trello_webhook_setup == True

    def action(self):
        self.trello_webhook_setup = "Ran"
        # check for existance of callback urls
        if shared.TRELLO_WEBHOOK_MEMBER_CALLBACK_URL is None:
            shared.TRELLO_WEBHOOK_MEMBER_CALLBACK_URL = 'https://francois.nebrios.com/api/v1/trello_webhook/member_callback'
        if shared.TRELLO_WEBHOOK_BOARD_CALLBACK_URL is None:
            shared.TRELLO_WEBHOOK_BOARD_CALLBACK_URL = 'https://francois.nebrios.com/api/v1/trello_webhook/board_callback'
        # check for existance of trello api key/secret
        if shared.TRELLO_API_KEY is None:
            if self.trello_api_key is not None:
                shared.TRELLO_API_KEY = self.trello_api_key
            else:
                raise Exception('Trello API key does not exist. Please supply one.')
        else:
            self.trello_api_key = shared.TRELLO_API_KEY
        if not shared.TRELLO_API_SECRET:
            if self.trello_api_secret is not None:
                shared.TRELLO_API_SECRET = self.trello_api_secret
            else:
                raise Exception('Trello API secret does not exist. Please supply one.')
        # next let's see if the current user has a token already
        try:
            p = Process.objects.get(user=self.last_actor, kind="oauth_token")
            token = p.token
        except:
            # no token yet, let's load the card.
            load_card('trello-token-save')