import enum


class LogSettingsActions(enum.Enum):
	member_joined = 'member_joined'
	member_left = 'member_left'
	member_banned = 'member_banned'
	member_unbanned = 'member_unbanned'
	member_nickname_changed = 'member_nickname_changed'
	member_received_role = 'member_received_role'
	member_lost_role = 'member_lost_role'
	timeout_given_or_removed = 'timeout_given_or_removed'
	channel_created = 'channel_created'
	channel_deleted = 'channel_deleted'
	role_created = 'role_created'
	role_deleted = 'role_deleted'
	message_deleted = 'message_deleted'
	message_edited = 'message_edited'
	member_joined_voice_channel = 'member_joined_voice_channel'
	member_left_voice_channel = 'member_left_voice_channel'
	member_switched_voice_channel = 'member_switched_voice_channel'

class ClearMessagesTime(enum.Enum):
	previous_hour = 3600
	previous_six_hours = 3600 * 6
	previous_twelwe_hours = 3600 * 12
	previous_day = 3600 * 24
	previous_three_days = 3600 * 24 * 3
	previous_seven_days = 3600 * 24 * 7
