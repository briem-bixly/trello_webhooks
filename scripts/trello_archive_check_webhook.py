import copy
from trello import TrelloClient # from https://github.com/sarumont/py-trello
import requests

class trello_archive_check_webhook(NebriOS):
    listens_to = ['shared.trello_webhook_data']

    # Test keys and ids
    #RECIPIENT_BOARD_ID = '5543344ce180c4f4a007b7f2'
    #RECIPIENT_BOARD_LIST_ID = '554368519fbb1a2a23188bc3'

    RECIPIENT_BOARD_ID = '555f18ec2f7124bb20eb43fb'
    RECIPIENT_BOARD_LIST_ID = '555f18fbf000bfa520b9bb3f'

    def check(self):
        # Sample webhook data of an archive action
        """
        {
          "action": {
            "data": {
              "list": {
                "name": "Doing",
                "id": "550f99bb549b7af0addfc6d0"
              },
              "old": {
                "closed": false
              },
              "board": {
                "shortLink": "pMTeOLL5",
                "id": "550f99aa150f282430cae0cb",
                "name": "To Nebrize"
              },
              "card": {
                "idShort": 74,
                "shortLink": "5nCAJUZ3",
                "name": "Test Card (for Erick and to be removed later)",
                "closed": true,
                "id": "555ef54ccd3563e485200b70"
              }
            },
            "idMemberCreator": "551f21e7d06cafd96401fc67",
            "memberCreator": {
              "username": "erickdavid",
              "fullName": "Erick David",
              "id": "551f21e7d06cafd96401fc67",
              "avatarHash": "95b7b8c49d41d5cb65f5587b24ba20b9",
              "initials": "ED"
            },
            "date": "05/22/2015 09:43:20 AM",
            "type": "updateCard",
            "id": "555efa3815d379337643e234"
          },
          ...
        }
        """
        
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
            api_key='11162496ef983e6cc27a13042500464a',
            token='b9c36b3d582223559fa47006603471c260b2f7fc148c30bf545d0f031120bd56'
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
            
            RECIPIENT_BOARD_ID = '556e36092adf5b1fd423bf3d'
            RECIPIENT_BOARD_LIST_ID = '556e3615d5c466f12e525b24'

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
