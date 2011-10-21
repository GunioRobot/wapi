# -*- coding: utf-8 -*-

# Copyright (c) 2008 Alberto García Hierro <fiam@rm-fr.net>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from wapi.auth.base import ApiAuth

class ApiAuthBasic(ApiAuth):
    def login(self, request):
        """Override this and implement the logic for your authentication
        method. You are supposed to return ``None`` if authentication
        succeeded, ``self.authentication_failed`` otherwise.

        If the authentication succeeded you should also set request.user
        to the authenticated User."""
        raise NotImplementedError

    def authentication_failed(self, request):
        """Returns a response indicating the provided credentials were wrong.
        According to http://en.wikipedia.org/wiki/HTTP_401#4xx_Client_Error the
        response should be the same as if the user did not provide credentials"""
        return self.login_required(request)

    def get_credentials(self, request):
        """Utility function for getting the authentication credentials"""
        if 'HTTP_AUTHORIZATION' in request.META:
            print request.META['HTTP_AUTHORIZATION']
            meth, auth = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
            if meth.lower() == 'basic':
                decoded = auth.decode('base64')
                return decoded.split(':', 1)

        return (None, None)

    def login_required(self, request):
        """Returns a response indicating the user needs to log in"""
        response = HttpResponse(_('Authorization Required'), mimetype='text/plain')
        response['WWW-Authenticate'] = 'Basic realm="%s"' % self.__class__.realm
        response.status_code = 401
        return response


class ApiAuthBasicUserPassword(ApiAuthBasic):
    """This class implements authentication against the django.contrib.auth
    user database. You only need to inherit this class and override 'realm'.
    Note, however, this authentication method sends the password as plaintext
    over the network, so it's usually better to avoid it unless you are using
    SSL."""

    def login(self, request):
        username,password = self.get_credentials(request)
        if username is not None and password is not None:
            user = authenticate(username=username, password=password)
            if user is not None and user.is_active:
                request.user = user
                return None
            else:
                return self.authentication_failed(request)
        else:
            return None

class ApiAuthBasicUserPasswordSecure(ApiAuthBasicUserPassword):
    """This authentication method is the same as ApiAuthBasicUserPassword.
    However, it will only suceed if the request has been made over HTTPS."""

    def login(self, request):
        if request.is_secure():
            return super(ApiAuthBasicUserPasswordSecure, self).login(request)

        return None

"""Example usage for ApiAuthBasicUserPassword:
    class ApiAuthMySite(ApiAuthBasicUserPassword):
        realm = "This is my realm. If you don't like it, I have other"
"""
