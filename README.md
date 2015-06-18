# trello_webhooks
Trello Webhook App for NebriOS

This app is intended for use in a NebriOS instance. Visit https://nebrios.com to sign up for free!

<h4>Setup</h4>
Please ensure that all files are placed in the correct places over SFTP.
  - trello_archive_check_webhook.py, trello_completed_notify.py, trello_pastdue_notify_webhook.py, trello_watch_boards_for_user.py and trello_webhook_steup.py should be copied to /scripts
  - trello_webhook.py should be copied to /api
  - trello-token-save.html should be copied to /card_html_files

Once all files are properly uploaded, trello_webhook_setup needs to be triggered in debug mode.

If this is the first time setting up these webhooks, a trello api key/secret pair will need to be supplied. This pair can be acquired at https://trello.com/1/appkey/generate. You must be logged in to trello to generate an app key/secret pair.
  ```
  trello_webhook_setup := True
  trello_api_key := <api_key> (optional)
  trello_api_secret := <api_secret> (optional)
  ```
This will trigger a card load with a link to follow that will provide you with a token generated with your app key/secret. The generated token will be stored for future use.

Once that has run, you'll want to trigger trello_watch_boards_for_user to set up webhooks for your particular user.
  ```
  trello_watch_boards_for_user := True
  ```
Setup is now complete. At this point, data will automatically be received from trello based on events that happen on the user's boards and will update appropriate shared KVPs accordingly. This will also trigger creation of shared.TRELLO_BOARD_LIST_TREE, which will contain info detailing boards and lists belonging to all boards.

<h4>Usage</h4>
There are a few different ticket scenarios that are currently covered by this app: notifications when a ticket is completed, notifications when a ticket has become past due, and notifications for when a card has been archived.

Each scenario has it's own rule script to send out notifications. These rule scripts can be triggered manually for testing, or can be set up to run on a drip schedule.

<strong>Manually Triggering Scripts</strong>
  ```
  fetch_trello_completed_cards := True
  ```
  When the above line is sent via debug mode, `trello_completed_notify` will be triggered, causing a script to find all completed cards and send an email listing all recently completed cards. `TARGET_EMAIL` should be edited accordingly.
  
  ```
  trello_pastdue_notify_webhook := True
  ```
  When the above line is sent via debug mode, `trello_pastdue_notify_webhook` will be triggered, causing a script to find all cards that were due in the past 24 hours and send an email listing all found cards. `TARGET_EMAIL` should be edited accordingly.

<strong>Setting Up a Drip</strong>

Under advanced in the nebrios web app, there is a drips tab. This can also be accessed at the `/core/drip/` endpoint.
Drips utilize cron job syntax for when they are run (www.cronmaker.com):
  ```
   * * * * *  command to execute
   │ │ │ │ │
   │ │ │ │ │
   │ │ │ │ └───── day of week (0 - 6) (0 to 6 are Sunday to Saturday, or use names; 7 is Sunday, the same as 0)
   │ │ │ └────────── month (1 - 12)
   │ │ └─────────────── day of month (1 - 31)
   │ └──────────────────── hour (0 - 23)
   └───────────────────────── min (0 - 59)
  ```
  
  `schedule` should reflect the cron schedule in the above syntax
  `key/value pairs` should reflect what key/value pairs should be created
  
  <strong>Example</strong> In order to create a drip to run `trello_pastdue_notify_webhook` every day at 8am, your drip should look like:
      
      schedule: 0 8 * * *
      key/value pairs: trello_pastdue_notify_webhook := True
      
