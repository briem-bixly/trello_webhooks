import json
import logging

from trello import TrelloClient


logging.basicConfig(filename='trello_webhook_module.log', level=logging.DEBUG)


TRELLO_API_SECRET = '1752bd46669f299633010d0eece6c7ceb2068abba72162c1f6f4458247554bd6'


def board_callback(request):
    logging.debug('\n\n\n*******************************************************')
    logging.debug('trello_webhook.board_callback received request from Trello')
    logging.debug(request.POST)
    
    post_data = _get_post_data(request)
    logging.debug('post_data: %s' % post_data) 
    if post_data is not None:
        action = post_data['action']
        action_type = action['type']
        
        actions_for_caching = [
            'addAttachmentToCard',
            'addChecklistToCard',
            'addLabelToCard',
            'convertToCardFromCheckItem',
            'createCard',
            'createCheckItem',
            'deleteAttachmentFromCard',
            'deleteCheckItem',
            'removeChecklistFromCard',
            'removeLabelFromCard',
            'updateCard',
            'updateCheckItemStateOnCard',
            'updateChecklist',
        ]
        if action_type in actions_for_caching:
            client = _get_client(request)
            card_id = action['data']['card']['id']
            
            # Save card as shared KVP
            card_json = client.fetch_json('/cards/' + card_id, query_params={
                'actions': 'all',
                'checklists': 'all',
                'attachments': 'true',
                'filter': 'all'
            })
            logging.debug('+++++++++++++ card_json[\'id\'] %s ++++++++++++++' % card_json['id'])
            setattr(shared, 'TRELLO_CARD_%s' % card_json['id'], card_json)
            
            try:
                _update_card_cache_lists(card_json, action_type, post_data)
            except Exception, e:
                logging.debug('----------- _update_card_cache_lists EXCEPTION -----------')
                logging.debug(e)
        elif action_type == 'deleteCard':
            try:
                card_id = action['data']['card']['id']
                delete_action = action
        
                card_cache_key = 'TRELLO_CARD_%s' % card_id
                card_cache = getattr(shared, card_cache_key) or {}
                logging.debug('&&&&&& card_cache &&&&&&')
                logging.debug(card_cache.keys())
                
                if card_cache:
                    client = _get_client(request)
                    me = client.fetch_json('/members/me')
                    cached_member_data = get_cached_member_data(me['id'])                    
                    backup_board_id = cached_member_data['backup_board_id']
                    backup_list_id = cached_member_data['backup_list_id']
                    
                    backup_board = client.get_board(backup_board_id)
                    backup_list = backup_board.get_list(backup_list_id)
                    
                    card_cache_actions = card_cache.get('actions', [])
                    for action in card_cache_actions:
                        if all([
                                action['type'] == 'createCard',
                                delete_action['idMemberCreator'] != action['idMemberCreator']    
                            ]):
    
                            # Also check if the person who deleted the card does not own the card
                            logging.debug('We can transfer card %s to list %s.' % (
                                card_id,
                                backup_list_id,
                            ))
                            
                            # Copy labels from original board to backup board
                            copy_labels = []
                            orig_labels = card_cache['labels']
                            for label in orig_labels:
                                try:
                                    label_copy = backup_board.add_label(
                                        label['name'],
                                        label['color']
                                    )
                                    copy_labels.append(label_copy)
                                except Exception, e:
                                    logging.debug('*** EXCEPTION DURING LABEL CREATE ***')
                                    logging.debug(e)
                            
                            add_card_kwargs = {
                                'desc': card_cache['desc'],
                                'labels': copy_labels,
                            }
                            due_date = card_cache.get('due', None)
                            if due_date:
                                add_card_kwargs['due'] = due_date.isoformat()
                
                            card_backup = backup_list.add_card(card_cache['name'], **add_card_kwargs)
                            
                            # Copy checklist to card backup
                            checklists = card_cache.get('checklists', [])
                            for checklist in checklists:
                                try:
                                    card_backup.add_checklist(
                                        checklist['name'],
                                        [item['name'] for item in checklist['checkItems']],
                                        itemstates=[item['state'] == 'complete' for item in checklist['checkItems']]
                                    )
                                except Exception, e:
                                    logging.debug('$$$$$$ EXCEPTION DURING CHECKLIST CREATE $$$$$$')
                                    logging.debug(e)
                                    logging.debug('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
                                
                            # Copy attachments to card backup
                            attachments = card_cache.get('attachments', [])
                            logging.debug('attachments: %s' % attachments)
                            for attachment in attachments:
                                try:
                                    logging.debug('&&&& attachment[\'url\']')
                                    logging.debug(attachment['url'])
                                    card_backup.attach(
                                        url=attachment['url']
                                    )
                                except Exception, e:
                                    logging.debug('*** EXCEPTION DURING ATTACHMENT ***')
                                    logging.debug(e)
                        else:
                            logging.debug('Not backing up card %s to list %s.' % (card_id, backup_list_id,))
                    try:
                        _update_card_cache_lists(card_cache, action_type, post_data)
                    except Exception, e:
                        logging.debug('----------- _update_card_cache_lists EXCEPTION -----------')
                        logging.debug(e)
            except Exception, e:
                logging.debug('$$$$$$ FOUND EXCEPTION $$$$$$')
                logging.debug(e)
    else:
        logging.debug('post_data is None.')
    logging.debug('*******************************************************\n\n\n\n')


def member_callback(request):
    logging.debug('\n\n\n\n*******************************************************')
    logging.debug('trello_webhook.member_callback received request from Trello')

    post_data = _get_post_data(request)
    logging.debug('post_data: %s' % post_data)
    if post_data is not None:
        logging.debug(post_data)
        logging.debug('post_data.keys %s' % post_data.keys())
        
        action = post_data['action']
        action_type = action['type']
    
        if action_type in ['createBoard', 'addMemberToBoard']:
            client = _get_client(request)
            
            board_id = action['data']['board']['id']
            logging.debug('Creating webhook for Board %s' % board_id)
            client.create_hook(
                _get_hook_url(request, shared.TRELLO_WEBHOOK_BOARD_CALLBACK_URL),
                board_id
            )
    
            # Cache cards as shared KVPs
            try:
                _cache_cards_for_board(client, board_id)
            except Exception, e:
                logging.debug(e)
    else:
        logging.debug('post_data is None.')
    logging.debug('*******************************************************\n\n\n\n')


def get_cached_member_data_key(member_id):
        return 'TRELLO_MEMBER_DATA_%s' % member_id
    
    
def get_cached_member_data(member_id):
    cached_member_data = getattr(shared, get_cached_member_data_key(member_id))
    return cached_member_data


def _cache_cards_for_board(client, board_id):
    # Fetch cards for this board
    cards_json = client.fetch_json('/boards/' + board_id + '/cards', query_params={
        'actions': 'all',
        'checklists': 'all',
        'attachments': 'true',
        'filter': 'all'
    })

    for card_json in cards_json:
        logging.debug('Saving card as shared KVP...')
        setattr(shared, 'TRELLO_CARD_%s' % card_json['id'], card_json)


def _get_client(request):
    trello_api_key, trello_token = _get_app_key_and_token(request)

    return TrelloClient(
        api_key=trello_api_key,
        api_secret=TRELLO_API_SECRET,
        token=trello_token
    )


def _get_app_key_and_token(request):
    return (request.GET['trello_api_key'], request.GET['trello_token'],)


def _get_post_data(request):
    post_data = None
    
    logging.debug('************ request **************')
    logging.debug(request)
    logging.debug(request.POST)
    logging.debug('************ request **************')
    if request.POST:
        post_data = json.loads(request.POST.keys()[0])

    return post_data


def _get_hook_url(request, base_url):
    trello_api_key, trello_token = _get_app_key_and_token(request)

    return '%s?trello_api_key=%s&trello_token=%s' % (
        base_url,
        trello_api_key,
        trello_token
    )
    
    
def _update_card_cache_lists(card_json, action_type, post_data):
    if action_type in ["createCard", "updateCard", "deleteCard"]:
        card_deleted = False
        if action_type == "deleteCard":
            card_deleted = True
        _update_due_card_cache_list(action_type, post_data, card_deleted)
    if action_type in ["createCard", "updateCard", "deleteCard"]:
        LIST_NAME = "Done"
        card_deleted = False
        is_moved_to_done = ('listAfter' in post_data['action']['data'] and 
                        LIST_NAME == post_data['action']['data']['listAfter']['name'] and
                        'listBefore' in post_data['action']['data'] and 
                        LIST_NAME != post_data['action']['data']['listBefore']['name'])
        is_card_closed = ('closed' in post_data['action']['data']['card'] and 
                      post_data['action']['data']['card']['closed'] == True)
        if action_type == "deleteCard" or is_card_closed or (not is_moved_to_done):
            card_deleted = True
        _update_completed_card_cache_list(action_type, post_data, card_deleted)


def _update_completed_card_cache_list(action_type, webhook_data, card_deleted):
    data = webhook_data['action']['data']
    card_data = data['card']
    board_data = data['board']
    card_id = card_data['id']
    board_id = board_data['id']
    
    if not shared.TRELLO_COMPLETED_CARD_CACHE:
        shared.TRELLO_COMPLETED_CARD_CACHE = []
        
    #look for board_id in shared.TRELLO_DUE_CARD_CACHE
    found = False
    board_to_update = {}
    for b in shared.TRELLO_COMPLETED_CARD_CACHE:
        if b['id'] == board_id:
            found = True
            board_to_update = b
            break
    if not found:
        board_to_update = board_data
        board_to_update['cards'] = []
        shared.TRELLO_COMPLETED_CARD_CACHE.append(board_to_update)
        
    #look for card_id in board_to_update['cards']
    board_cards = board_to_update['cards']
    found = False
    card_to_update = {}
    for c in board_cards:
        if c['id'] == card_id:
            found = True
            card_to_update = c
            break
        
    card_to_update['name'] = card_data['name']
        
    if not found:
        card_to_update['id'] = card_id
        card_to_update['shortLink'] = card_data['shortLink']
        board_cards.append(card_to_update)
    else:
        if card_deleted:
            board_cards.remove(card_to_update)
            return
        
    card_to_update['date'] = webhook_data['action']['date']
    

def _update_due_card_cache_list(action_type, webhook_data, card_deleted):
    if not webhook_data:
        return
    data = webhook_data['action']['data']
    card_data = data['card']
    board_data = data['board']
    if 'list' not in data.keys():
        return
    list_data = data['list']
    card_id = card_data['id']
    board_id = board_data['id']
    
    if not shared.TRELLO_DUE_CARD_CACHE:
        shared.TRELLO_DUE_CARD_CACHE = []
    
    #look for board_id in shared.TRELLO_DUE_CARD_CACHE
    found = False
    board_to_update = {}
    for b in shared.TRELLO_DUE_CARD_CACHE:
        if b['id'] == board_id:
            found = True
            board_to_update = b
            break
    if not found:
        board_to_update = board_data
        board_to_update['cards'] = []
        shared.TRELLO_DUE_CARD_CACHE.append(board_to_update)
    
    #look for card_id in board_to_update['cards']
    board_cards = board_to_update['cards']
    found = False
    card_to_update = {}
    for c in board_cards:
        if c['id'] == card_id:
            found = True
            card_to_update = c
            break
    
    card_to_update['name'] = card_data['name']
        
    if not found:
        card_to_update['id'] = card_id
        card_to_update['shortLink'] = card_data['shortLink']
        board_cards.append(card_to_update)
    else:
        if card_deleted:
            board_cards.remove(card_to_update)
            return
        
    if 'due' in card_data:
        card_to_update['due'] = card_data['due']
    else:
        card_to_update['due'] = ""
        
    if list_data['name'] == "Done":
        card_to_update['due'] = ""
    
    #all cards in shared.TRELLO_DUE_CARD_CACHE that has 'due' == "", remove immediately
    if not card_to_update['due']:
        board_cards.remove(card_to_update)
        
        
def oauth_token(request):
    if request.FORM:
        user = request.user
        try:
            p = Process.objects.get(user=request.user, kind="oauth_token")
            p.token = request.FORM.trello_token
            p.save()
        except:
            p = Process.objects.create()
            p.user=request.user
            p.kind="oauth_token"
            p.token=request.FORM.trello_token
            p.save()
