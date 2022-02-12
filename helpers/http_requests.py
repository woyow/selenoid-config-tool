import requests
import requests_cache

from datetime import timedelta

# Cache all http requests
requests_cache.install_cache(
	'selenoid_config_tool_requests_cache',
	use_cache_dir=True,
	cache_control=True,
	expire_after=timedelta(days=1),
	allowable_codes=[200]
)


class HttpRequests:

	def __init__(
			self,
			api_endpoint: str,
			api_method: str = None,
			request_params: dict = None,
			headers: dict = None,
			body: dict = None,
			secure: bool = None
	):
		if secure is False:
			self.protocol = 'http'
		else:
			self.protocol = 'https'
		self.api_endpoint = api_endpoint
		self.api_method = api_method
		self.request_params = request_params
		self.headers = headers
		self.body = body

		if api_method is None:
			self.url = self.protocol + '://' + self.api_endpoint
		else:
			self.url = self.protocol + '://' + self.api_endpoint + self.api_method

		if request_params is not None:
			self.url = self.url + '?'
			param_count = len(self.request_params)
			for key in self.request_params:
				self.url += key + '=' + str(self.request_params[key])
				param_count -= 1
				if param_count > 0:
					self.url += '&'

		self.requests_session = requests.session()

	def get(self):
		try:
			response = self.requests_session.get(self.url, headers=self.headers, timeout=(10, 10))
		except TimeoutError:
			print(f'Something went wrong. Get request {self.url} got timeout error.')
		finally:
			return response

	def post(self):
		pass

	def put(self):
		pass

	def delete(self):
		pass

	def patch(self):
		pass

	def options(self):
		pass

	def head(self):
		pass
