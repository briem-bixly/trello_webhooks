import copy
from trello import TrelloClient # from https://github.com/sarumont/py-trello
import requests

class trello_archive_check_webhook(NebriOS):
    listens_to = ['shared.trello_webhook_data']

    def check(self):
        
        if (type(shared.trello_webhook_data) != list or 
            shared.trello_webhook_data == []):
            return False
        
        webhook_copy = copy.copy(shared.trello_webhook_data[0])
        is_update = webhook_copy['action']['type'] == 'updateCard'
        is_old_not_closed = ('old' in webhook_copy['action']['data'] and 
                             'closed' in webhook_copy['action']['data']['old'] and
                             webhook_copy['action']['data']['old']['closed'] == False)
        is_card_closed = ('closed' in webhook_copy['action']['data']['card'] and 
                          webhook_copy['action']['data']['card']['closed'] == True)
        
        if is_update and is_old_not_closed and is_card_closed:
            self.webhook_data = webhook_copy
            return True
        
        return False

    def action(self):
        shared.trello_webhook_data_latest = copy.copy(shared.trello_webhook_data)
        shared.trello_webhook_data = []

        self.moved_cards = []
        client = TrelloClient(
            api_key=shared.TRELLO_API_KEY,
            token=self.TRELLO_TOKEN
        )
        card_id = self.webhook_data['action']['data']['card']['id']
        card = client.get_card(card_id)

        card.fetch_actions('createCard')
        # There's only one value in this list: the create action for the card
        creator_id = card.actions[0]['idMemberCreator']
        creator_username = card.actions[0]['memberCreator']['username']
        self.card_creator_id = creator_id
        self.card_creator = creator_username

        card.fetch_actions('updateCard:closed')
        # There may be multiple values for this list each corresponding 
        # to the actions that archived this card. Therefore, only get 
        # the latest archive action
        archiver_id = card.actions[0]['idMemberCreator']
        archiver_username = card.actions[0]['memberCreator']['username']
        self.card_archiver_id = archiver_id
        self.card_archiver = archiver_username

        # Check if card has been archived by someone other than the creator
        if creator_id != archiver_id:
            # self will be replaced with shared after testing

            # card.change_board(self.RECIPIENT_BOARD_ID)
            # card.set_closed(False)
            # card.change_list(self.RECIPIENT_BOARD_LIST_ID)
            # card_data = card.actions[0]['data']['card']
            # card_attr = {
            #     'id': card_data['id'],
            #     'name': card_data['name'],
            #     'creator_id': creator_id,
            #     'creator_username': creator_username,
            #     'archiver_id': archiver_id,
            #     'archiver_username': archiver_username,
            #     'date_archived': card.actions[0]['date']
            # }
            # self.moved_cards.append(card_attr)
            
            RECIPIENT_BOARD_ID = self.RECIPIENT_BOARD_ID
            RECIPIENT_BOARD_LIST_ID = self.RECIPIENT_BOARD_LIST_ID

            card_copy = copy.copy(card)
            board = client.get_board(RECIPIENT_BOARD_ID)
            white_list = board.get_list(RECIPIENT_BOARD_LIST_ID)
            
            # copy orig card to archive board
            json_obj = client.fetch_json(
                '/cards',
                http_method='POST',
                post_args={
                    'idList': RECIPIENT_BOARD_LIST_ID,
                    'urlSource': "null",
                    'idCardSource': card_id
                }
            )

            card_copy_data = card_copy.actions[0]['data']['card']
            card_copy_attr = {
                'id': card_copy_data['id'],
                'name': card_copy_data['name'],
                'creator_id': creator_id,
                'creator_username': creator_username,
                'archiver_id': archiver_id,
                'archiver_username': archiver_username,
                'date_archived': card_copy.actions[0]['date']
            }
            self.moved_cards.append(card_copy_attr)
