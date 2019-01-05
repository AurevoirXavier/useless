USERNAME = 'test12345'
PASSWORD = 'test12345'

# [connect] and [read]
TIMEOUT = (1, 1)

BOOKING_PAGE = 'https://kktix.com/events/momoiroclove-fds6c/registrations/new'
EVENT_ID = 'momoiroclove-fds6c'

# [id], [quantity] and [currency]
PAYLOAD = '{"tickets":[{"id":145810,"quantity":1,"invitationCodes":[],"member_code":"","use_qualification_id":null}],"currency":"TWD","recaptcha":{},"agreeTerm":true}'
PAYLOAD_WITH_CAPTCHA = '{{"tickets":[{{"id":145810,"quantity":1,"invitationCodes":[],"member_code":"","use_qualification_id":null}}],"currency":"TWD","recaptcha":{{}},"custom_captcha":"{}","agreeTerm":true}}'
