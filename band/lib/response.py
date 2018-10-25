RESP_PIXEL = 'pixel'
RESP_REDIRECT = 'redirect'
RESP_ERROR = 'error'
RESP_DATA = 'data'


class BandResponse:

    def __call__(self, data):
        return data

    def data(self, data, statusCode=200):
        return {
            'type__': RESP_DATA,
            '_response___type': RESP_DATA, #TODO: remove it
            'statusCode': statusCode,
            'data': data
        }

    def redirect(self, location, statusCode=302, data={}):
        return {
            'type__': RESP_REDIRECT,
            '_response___type': RESP_REDIRECT, #TODO: remove it
            'location': location,
            'statusCode': statusCode,
            'data': data
        }

    def pixel(self, data={}):
        return {
            'type__': RESP_PIXEL,
            '_response___type': RESP_PIXEL, #TODO: remove it
            'data': data
        }

    def error(self, message="", statusCode=500, data={}):
        return {
            'type__': RESP_ERROR,
            '_response___type': RESP_ERROR, #TODO: remove it
            'errorMessage': message,
            'statusCode': statusCode,
            'data': data,
        }


__all__ = ['BandResponse']
