class TarkovProfile:

	def __init__(self, discord_user, tarkov_name=None):
		self.discord_id = discord_user.id
		self.discord_name = discord_user.name
		if tarkov_name:
			self.tarkov_name = tarkov_name
		else:
			self.tarkov_name = discord_user.name

	def update_tarkov_name(self, tarkov_name) -> None:
		self.tarkov_name = tarkov_name

	def __str__(self):
		return "{}, {}".format(self.discord_name, self.tarkov_name)