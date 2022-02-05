import requests


class HttpRequests:

	def __init__(self, api_endpoint, api_method=None, request_params=None, headers=None, body=None, secure=None):
		if secure is not False:
			self.protocol = 'https'
		else:
			self.protocol = 'http'
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
			self.url = self.url + '?' + self.request_params
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
